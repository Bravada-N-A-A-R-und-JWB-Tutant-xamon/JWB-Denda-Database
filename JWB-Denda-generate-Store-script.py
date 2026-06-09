import os
import requests
import json

# НАСТРОЙКИ: Имя твоей организации и токен (токен гитхаб подставит сам в Actions)
ORG_NAME = "Bravada-N-A-A-R-und-JWB-Tutant-xamon"
TOKEN = os.getenv("GITHUB_TOKEN")

headers = {"Accept": "application/vnd.github.v3+json"}
if TOKEN:
    headers["Authorization"] = f"token {TOKEN}"

def get_repositories():
    url = f"https://api.github.com/orgs/{ORG_NAME}/repos?per_page=100"
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

def get_repo_files(repo_name, branch):
    # Получаем дерево файлов, чтобы найти .desktop с любым именем
    url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/git/trees/{branch}?recursive=1"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("tree", [])
    return []

def main():
    print("=== СТАРТ СБОРКИ БАЗЫ ДАННЫХ JWB-DENDA ===")
    repos = get_repositories()
    store_data = []

    for repo in repos:
        repo_name = repo["name"]
        # Игнорируем служебный репо с самой базой данных
        if repo_name == "denda-database" or repo.get("fork", False):
            continue

        default_branch = repo.get("default_branch", "main")
        print(f"\nСканируем репозиторий: {repo_name} (Ветка: {default_branch})")

        files = get_repo_files(repo_name, default_branch)
        
        desktop_path = None
        manifest_path = None

        # Ищем файлы по расширению и формату, крот теперь работает на сервере!
        for f in files:
            path = f["path"]
            if path.lower().endswith(".desktop"):
                desktop_path = path
            elif path.lower().endswith("manifest.json"):
                manifest_path = path

        # Дефолтные значения
        app_name = repo_name.replace("-", " ")
        app_version = "1.0.0"
        app_icon = ""
        app_splash = "#141414"
        app_category = "Apps"

        raw_base_url = f"https://raw.githubusercontent.com/{ORG_NAME}/{repo_name}/{default_branch}"

        # 1. Парсим manifest.json если нашли
        if manifest_path:
            m_res = requests.get(f"{raw_base_url}/{manifest_path}")
            if m_res.status_code == 200:
                try:
                    manifest = m_res.json()
                    app_name = manifest.get("title", manifest.get("name", app_name))
                    app_version = manifest.get("version", app_version)
                    if "icon" in manifest:
                        app_icon = f"{raw_base_url}/{manifest['icon']}"
                except:
                    print(f"Ошибка парсинга JSON в {repo_name}")

        # 2. Парсим .desktop если нашли
        if desktop_path:
            d_res = requests.get(f"{raw_base_url}/{desktop_path}")
            if d_res.status_code == 200:
                for line in d_res.text.splitlines():
                    if line.startswith("Name=") and not manifest_path:
                        app_name = line.split("=")[1].strip()
                    elif line.startswith("X-Ubuntu-Splash-Color="):
                        app_splash = line.split("=")[1].strip()

        # 3. Фоллбэк для иконок (То, что ты придумал!)
        if not app_icon:
            # Проверяем, есть ли вообще logo.svg или icon.svg в дереве файлов
            file_paths = [f["path"].lower() for f in files]
            if "logo.svg" in file_paths:
                app_icon = f"{raw_base_url}/logo.svg"
            elif "assets/logo.svg" in file_paths:
                app_icon = f"{raw_base_url}/assets/logo.svg"
            elif "icon.svg" in file_paths:
                app_icon = f"{raw_base_url}/icon.svg"
            else:
                app_icon = "qrc:/Assets/JWB-Denda Logo (none).svg"

        # Закидываем прилу в общую базу
        store_data.append({
            "repoName": repo_name,
            "appName": app_name,
            "appVersion": app_version,
            "appIcon": app_icon,
            "appSplashColor": app_splash,
            "appCategory": app_category,
            "appDescription": repo.get("description", "No description provided.")
        })
        print(f"Успешно добавлен: {app_name} v{app_version}")

    # Сохраняем итоговый файл
    with open("store_data.json", "w", encoding="utf-8") as f:
        json.dump(store_data, f, ensure_ascii=False, indent=2)
    print("\n=== СБОРКА ЗАВЕРШЕНА! Файл store_data.json готов. ===")

if __name__ == "__main__":
    main()
