#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("=== СБОРКА БАЗЫ JWB-DENDA ЧЕРЕЗ .DESKTOP + .IN ШАБЛОНЫ ===")

import os
import json
import re
import urllib.request

def get_organization_repos(org_name, token=None):
    """Получает список всех репозиториев организации через GitHub API."""
    url = f"https://api.github.com/orgs/{org_name}/repos?per_page=100"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Ошибка при получении списка репозиториев: {e}")
        return []

def get_repo_files_tree(org_name, repo_name, token=None):
    """Получает список файлов в корне репозитория через API GitHub."""
    url = f"https://api.github.com/repos/{org_name}/{repo_name}/contents/"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            contents = json.loads(response.read().decode('utf-8'))
            return [f["name"] for f in contents if f["type"] == "file"]
    except Exception:
        return []

def get_file_content(org_name, repo_name, file_path, token=None):
    """Скачивает сырой контент файла из веток main или master."""
    for branch in ["main", "master"]:
        url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/{branch}/{file_path}"
        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                return response.read().decode('utf-8')
        except Exception:
            continue
    return None

def extract_clean_author(maintainer_str):
    """
    Парсит строку maintainer и вытягивает только имя до email или ссылки.
    Пример: "JWB-Tutant'xamon <jwb.tutantxamon@gmail.com>" -> "JWB-Tutant'xamon"
    """
    if not maintainer_str:
        return None
    clean_name = re.sub(r'<[^>]+>|\([^)]+\)', '', maintainer_str)
    return clean_name.strip()

def clean_template_vars(text):
    """Вырезает CMake/Qbs переменные конфигурации вида @VARIABLE@ или %VARIABLE%."""
    if not text:
        return ""
    # Заменяем @VAR@ на пустую строку или дефолтное безопасное значение
    cleaned = re.sub(r'@[A-Za-z0-9_]+@', '', text)
    # На всякий случай чистим возможные %VAR%
    cleaned = re.sub(r'%[A-Za-z0-9_]+%', '', cleaned)
    return cleaned

def parse_desktop_content(content):
    """Парсит .desktop файл (включает поддержку .desktop.in) и вытаскивает метаданные."""
    data = {}
    if not content:
        return data
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        
        if key == "Name":
            for arg in [" %U", " %u", " %F", " %f"]:
                value = value.replace(arg, "")
            # Очищаем имя от возможных неразрешённых @переменных@ сборщика
            value = clean_template_vars(value)
            data["display_name"] = value.strip()
        elif key == "Icon":
            # Убираем расширения или шаблоны из имени иконки, если они там есть
            value = clean_template_vars(value)
            data["icon_name"] = value
        elif key in [
            "X-Ubuntu-Touch-Maintainer", "X-Lomiri-Maintainer",
            "Maintainer", "Developer", "X-Ubuntu-Developer", "X-Lomiri-Developer"
        ]:
            data["desktop_author"] = extract_clean_author(value)
        elif key == "X-Lomiri-Splash-Color":
            data["splash_color"] = value
        elif key == "X-Ubuntu-Splash-Color" and "splash_color" not in data:
            data["splash_color"] = value
    return data

def generate_store_database():
    org_name = "Bravada-n-A-a-R-und-jwb-tutant-xamon"
    token = os.getenv("GITHUB_TOKEN")
    
    repos = get_organization_repos(org_name, token)
    store_database = []
    
    print(f"Найдено репозиториев в организации: {len(repos)}")

    for repo in repos:
        repo_name = repo["name"]
        if repo_name == "JWB-Denda-Database":
            continue

        root_files = get_repo_files_tree(org_name, repo_name, token)
        
        desktop_file = None
        manifest_file = None
        has_ut_marker = False
        
        # Улучшенный маркер: чекаем обычные файлы И файлы с расширением .in
        for file in root_files:
            if file.endswith(".desktop") or file.endswith(".desktop.in"):
                desktop_file = file
                has_ut_marker = True
            if file in ["manifest.json", "manifest.json.in", "clickable.yaml", "clickable.json"]:
                has_ut_marker = True
            if file in ["manifest.json", "manifest.json.in"]:
                manifest_file = file

        if not has_ut_marker:
            continue

        print(f"[{repo_name}] ОБНАРУЖЕН ПРОЕКТ! Собираем данные... 🟩")
        
        # Динамические дефолты
        display_name = repo_name.replace("-", " ").replace("_", " ")
        author_name = repo.get("owner", {}).get("login", "Xarmbrassadora-Bravada")
        icon_url = "https://bravada-n-a-a-r-und-jwb-tutant-xamon.github.io/JWB-Denda-Database/assets/default-icon.png"
        splash_color = "#FFFFFF" 
        app_version = "1.0.0"

        # Читаем манифест (обычный или шаблонный)
        if manifest_file:
            manifest_raw = get_file_content(org_name, repo_name, manifest_file, token)
            if manifest_raw:
                try:
                    # Если работаем с шаблоном .in, очищаем его регуляркой до валидного JSON
                    if manifest_file.endswith(".in"):
                        manifest_raw = clean_template_vars(manifest_raw)
                    
                    manifest_json = json.loads(manifest_raw)
                    app_version = manifest_json.get("version", "1.0.0")
                    
                    # Если версия осталась макросом @PROJECT_VERSION@, ставим дефолт
                    if "@" in app_version or not app_version:
                        app_version = "1.0.0"
                        
                    manifest_maintainer = manifest_json.get("maintainer")
                    parsed_author = extract_clean_author(manifest_maintainer)
                    if parsed_author:
                        author_name = parsed_author
                        print(f"[{repo_name}] Автор успешно взят из {manifest_file}: {author_name}")
                except Exception as e:
                    print(f"[{repo_name}] Предупреждение парсинга манифеста: {e}")

        if desktop_file:
            desktop_raw = get_file_content(org_name, repo_name, desktop_file, token)
            desktop_data = parse_desktop_content(desktop_raw)
            
            if "display_name" in desktop_data and desktop_data["display_name"]:
                display_name = desktop_data["display_name"]
            if "splash_color" in desktop_data and desktop_data["splash_color"]:
                splash_color = desktop_data["splash_color"]
            
            if "desktop_author" in desktop_data and desktop_data["desktop_author"]:
                author_name = desktop_data["desktop_author"]
                print(f"[{repo_name}] Автор переопределен из .desktop: {author_name}")
                
            # Поиск ссылки на иконку
            if "icon_name" in desktop_data:
                icon_name = desktop_data["icon_name"]
                icon_file = None
                
                # Если имя иконки очистилось в ноль из-за макросов, пробуем дефолтные имена файлов
                if not icon_name:
                    icon_name = repo_name.lower()

                for file in root_files:
                    if file.lower().startswith(icon_name.lower()) or icon_name.lower() in file.lower():
                        if file.endswith((".png", ".svg", ".jpg")):
                            icon_file = file
                            break
                            
                # Запасной вариант: если по имени из десктопа ничего не нашли, ищем любую иконку в корне
                if not icon_file:
                    for file in root_files:
                        if file.endswith((".png", ".svg")) and ("icon" in file.lower() or "logo" in file.lower()):
                            icon_file = file
                            break

                if icon_file:
                    icon_url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/main/{icon_file}"
                elif "." in icon_name and not icon_name.startswith("@"):
                    icon_url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/main/{icon_name}"

        app_data = {
            "name": repo_name,
            "display_name": display_name,
            "author": author_name,
            "version": app_version,
            "icon": icon_url,
            "splash": {
                "color": splash_color
            },
            "description": repo["description"] if repo["description"] else "Компонент независимой экосистемы JWB.",
            "repository_url": repo["html_url"],
            "type": "Ubuntu Touch App",
            "status": "Active"
        }

        store_database.append(app_data)

    output_path = "store_data.json"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(store_database, f, indent=4, ensure_ascii=False)
        print(f"\nУСПЕХ! Сборка базы с поддержкой .in шаблонов завершена. Найдено приложений: {len(store_database)}")
    except Exception as e:
        print(f"Ошибка записи JSON: {e}")

if __name__ == "__main__":
    generate_store_database()
