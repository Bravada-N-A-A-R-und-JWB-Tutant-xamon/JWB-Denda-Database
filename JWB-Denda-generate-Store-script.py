#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("=== ОКОНЧАТЕЛЬНЫЙ СУПЕР-УМНЫЙ ПАРСЕР ВЕТОК JWB-DENDA ===")

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

def get_repo_files_recursive(org_name, repo_name, branch="main", token=None):
    """Получает файлы из корня и из папки assets/Assets репозитория."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    file_list = []
    
    # Сканируем корень репозитория
    url_root = f"https://api.github.com/repos/{org_name}/{repo_name}/contents/?ref={branch}"
    try:
        req = urllib.request.Request(url_root, headers=headers)
        with urllib.request.urlopen(req) as response:
            contents = json.loads(response.read().decode('utf-8'))
            for f in contents:
                if f["type"] == "file":
                    file_list.append({"name": f["name"], "path": f["path"]})
    except Exception:
        return [] # Если ветки нет или ошибка — возвращаем пустой список

    # Сканируем папку assets / Assets (с учётом регистра для GitHub API)
    for assets_folder in ["assets", "Assets"]:
        url_assets = f"https://api.github.com/repos/{org_name}/{repo_name}/contents/{assets_folder}?ref={branch}"
        try:
            req = urllib.request.Request(url_assets, headers=headers)
            with urllib.request.urlopen(req) as response:
                contents = json.loads(response.read().decode('utf-8'))
                for f in contents:
                    if f["type"] == "file":
                        file_list.append({"name": f["name"], "path": f["path"]})
        except Exception:
            pass
            
    return file_list

def get_file_content(org_name, repo_name, branch, file_path, token=None):
    """Скачивает сырой контент файла по его точному пути и правильной ветке."""
    url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/{branch}/{file_path}"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception:
        return None

def extract_clean_author(maintainer_str):
    """Вытягивает только имя до email или ссылки."""
    if not maintainer_str:
        return None
    clean_name = re.sub(r'<[^>]+>|\([^)]+\)', '', maintainer_str)
    return clean_name.strip()

def clean_template_vars(text):
    """Вырезает CMake/Qbs переменные конфигурации вида @VARIABLE@ или %VARIABLE%."""
    if not text:
        return ""
    cleaned = re.sub(r'@[A-Za-z0-9_]+@', '', text)
    cleaned = re.sub(r'%[A-Za-z0-9_]+%', '', cleaned)
    return cleaned

def parse_desktop_content(content):
    """Парсит .desktop или .desktop.in файл и вытаскивает метаданные."""
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
            value = clean_template_vars(value)
            data["display_name"] = value.strip()
        elif key == "Icon":
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
    org_name = "Bravada-N-A-A-R-und-JWB-Tutant-xamon"
    token = os.getenv("GITHUB_TOKEN")
    
    repos = get_organization_repos(org_name, token)
    store_database = []
    
    print(f"Найдено репозиториев в организации через API: {len(repos)}")

    for repo in repos:
        repo_name = repo["name"]
        if repo_name == "JWB-Denda-Database":
            continue

        # Собираем приоритетный список веток для проверки
        branches_to_try = []
        default_branch = repo.get("default_branch", "main")
        
        if default_branch and default_branch != "EMPTY":
            branches_to_try.append(default_branch)
            
        # Добавляем стандартные рабочие ветки в пул проверки на случай капризов с дефолтами
        for b in ["main", "master", "Source-Code"]:
            if b not in branches_to_try:
                branches_to_try.append(b)

        all_files = []
        working_branch = "main"
        has_ut_marker = False
        desktop_file_path = None
        manifest_file_path = None

        # Перебираем ветки, пока не найдём ту, в которой РЕАЛЬНО лежат маркеры приложения
        for branch in branches_to_try:
            files = get_repo_files_recursive(org_name, repo_name, branch, token)
            if not files:
                continue
                
            # Проверяем маркеры в этой ветке
            branch_has_marker = False
            for file in files:
                filename_lower = file["name"].lower()
                if filename_lower.endswith(".desktop") or filename_lower.endswith(".desktop.in"):
                    desktop_file_path = file["path"]
                    branch_has_marker = True
                if filename_lower in ["manifest.json", "manifest.json.in", "clickable.yaml", "clickable.json"]:
                    branch_has_marker = True
                if filename_lower in ["manifest.json", "manifest.json.in"]:
                    manifest_file_path = file["path"]

            if branch_has_marker:
                all_files = files
                working_branch = branch
                has_ut_marker = True
                break # Нашли живую рабочую ветку, стоп колёса!

        if not has_ut_marker:
            continue

        print(f"[{repo_name}] ОБНАРУЖЕН ПРОЕКТ! Использована ветка: {working_branch} 🟩")
        
        display_name = repo_name.replace("-", " ").replace("_", " ")
        author_name = repo.get("owner", {}).get("login", "Xarmbrassadora-Bravada")
        icon_url = "https://bravada-n-a-a-r-und-jwb-tutant-xamon.github.io/JWB-Denda-Database/assets/default-icon.png"
        splash_color = "#FFFFFF" 
        app_version = "1.0.0"

        # Парсим манифест
        if manifest_file_path:
            manifest_raw = get_file_content(org_name, repo_name, working_branch, manifest_file_path, token)
            if manifest_raw:
                try:
                    if manifest_file_path.lower().endswith(".in"):
                        manifest_raw = re.sub(r'@[A-Za-z0-9_*]*VERSION[A-Za-z0-9_*]*@', '1.0.0', manifest_raw)
                        manifest_raw = re.sub(r'\${[A-Za-z0-9_*]*VERSION[A-Za-z0-9_*]*}', '1.0.0', manifest_raw)
                        manifest_raw = re.sub(r'@[A-Za-z0-9_]+@', 'templated_value', manifest_raw)
                        manifest_raw = re.sub(r'\${[A-Za-z0-9_]+}', 'templated_value', manifest_raw)
                    
                    manifest_json = json.loads(manifest_raw)
                    extracted_version = manifest_json.get("version", "1.0.0")
                    if extracted_version and "templated_value" not in extracted_version and "@" not in extracted_version:
                        app_version = extracted_version
                        
                    manifest_maintainer = manifest_json.get("maintainer")
                    parsed_author = extract_clean_author(manifest_maintainer)
                    if parsed_author and "templated_value" not in parsed_author:
                        author_name = parsed_author
                except Exception:
                    pass

        icon_target_path = None

        if desktop_file_path:
            desktop_raw = get_file_content(org_name, repo_name, working_branch, desktop_file_path, token)
            desktop_data = parse_desktop_content(desktop_raw)
            
            if "display_name" in desktop_data and desktop_data["display_name"]:
                display_name = desktop_data["display_name"]
            if "splash_color" in desktop_data and desktop_data["splash_color"]:
                splash_color = desktop_data["splash_color"]
            if "desktop_author" in desktop_data and desktop_data["desktop_author"]:
                author_name = desktop_data["desktop_author"]
                
            if "icon_name" in desktop_data and desktop_data["icon_name"]:
                icon_name = desktop_data["icon_name"]
                for file in all_files:
                    fname = file["name"].lower()
                    if fname.startswith(icon_name.lower()) or icon_name.lower() in fname:
                        if fname.endswith((".png", ".svg", ".jpg", ".jpeg")):
                            icon_target_path = file["path"]
                            break

        # Запасной поиск графики, если десктоп пуст
        if not icon_target_path:
            for file in all_files:
                fname_lower = file["name"].lower()
                if fname_lower.endswith((".png", ".svg", ".jpg", ".jpeg")):
                    if any(word in fname_lower for word in ["logo", "icon", "favicon", "avatar", repo_name.lower()]):
                        icon_target_path = file["path"]
                        break
            
            if not icon_target_path:
                for file in all_files:
                    if file["path"].lower().startswith("assets/") and file["name"].lower().endswith((".svg", ".png")):
                        icon_target_path = file["path"]
                        break

        if icon_target_path:
            icon_url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/{working_branch}/{icon_target_path}"

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
        print(f"\nУСПЕХ! Полная сборка базы завершена. Найдено приложений: {len(store_database)}")
    except Exception as e:
        print(f"Ошибка записи JSON: {e}")

if __name__ == "__main__":
    generate_store_database()
