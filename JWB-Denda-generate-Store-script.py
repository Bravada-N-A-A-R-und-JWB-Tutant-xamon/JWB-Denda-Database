#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("=== СБОРКА БАЗЫ JWB-DENDA ЧЕРЕЗ .DESKTOP (UBUNTU + LOMIRI ПОДДЕРЖКА) ===")

import os
import json
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

def parse_desktop_content(content):
    """Парсит .desktop файл и вытаскивает все метаданные, поддерживая и Ubuntu, и Lomiri префиксы."""
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
            data["display_name"] = value
        elif key == "Icon":
            data["icon_name"] = value
        elif key in [
            "X-Ubuntu-Touch-Maintainer", "X-Lomiri-Maintainer",
            "Maintainer", "Developer", "X-Ubuntu-Developer", "X-Lomiri-Developer"
        ]:
            data["author"] = value
        elif key == "X-Lomiri-Splash-Color":
            data["splash_color"] = value
        elif key == "X-Ubuntu-Splash-Color" and "splash_color" not in data:
            data["splash_color"] = value
        elif key == "X-Lomiri-Splash-Image":
            data["splash_image_name"] = value
        elif key == "X-Ubuntu-Splash-Image" and "splash_image_name" not in data:
            data["splash_image_name"] = value
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
        has_ut_marker = False
        
        for file in root_files:
            if file.endswith(".desktop"):
                desktop_file = file
                has_ut_marker = True
            if file in ["manifest.json", "clickable.yaml", "clickable.json"]:
                has_ut_marker = True

        if not has_ut_marker:
            continue

        print(f"[{repo_name}] ОБНАРУЖЕН ПРОЕКТ СРЕДЫ! Парсим... 🟩")
        
        display_name = repo_name.replace("-", " ").replace("_", " ")
        author_name = "Khmelyauskas Alexander (Knyaz)"
        icon_url = "https://bravada-n-a-a-r-und-jwb-tutant-xamon.github.io/JWB-Denda-Database/assets/default-icon.png"
        splash_color = "#FFFFFF" 
        splash_image_url = ""    
        app_version = "1.0.0"

        if "manifest.json" in root_files:
            manifest_raw = get_file_content(org_name, repo_name, "manifest.json", token)
            if manifest_raw:
                try:
                    manifest_json = json.loads(manifest_raw)
                    app_version = manifest_json.get("version", "1.0.0")
                except Exception:
                    pass

        if desktop_file:
            desktop_raw = get_file_content(org_name, repo_name, desktop_file, token)
            desktop_data = parse_desktop_content(desktop_raw)
            
            if "display_name" in desktop_data:
                display_name = desktop_data["display_name"]
            if "author" in desktop_data:
                author_name = desktop_data["author"]
            if "splash_color" in desktop_data:
                splash_color = desktop_data["splash_color"]
                
            # Поиск ссылки на иконку
            if "icon_name" in desktop_data:
                icon_name = desktop_data["icon_name"]
                icon_file = None
                for file in root_files:
                    if file.startswith(icon_name) or icon_name in file:
                        if file.endswith((".png", ".svg", ".jpg")):
                            icon_file = file
                            break
                if icon_file:
                    icon_url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/main/{icon_file}"
                elif "." in icon_name:
                    icon_url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/main/{icon_name}"

            # Поиск ссылки на картинку сплэша
            if "splash_image_name" in desktop_data:
                splash_name = desktop_data["splash_image_name"]
                splash_file = None
                for file in root_files:
                    if file.startswith(splash_name) or splash_name in file:
                        if file.endswith((".png", ".svg", ".jpg")):
                            splash_file = file
                            break
                if splash_file:
                    splash_image_url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/main/{splash_file}"
                elif "." in splash_name:
                    splash_image_url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/main/{splash_name}"

        app_data = {
            "name": repo_name,
            "display_name": display_name,
            "author": author_name,
            "version": app_version,
            "icon": icon_url,
            "splash": {
                "color": splash_color,
                "image": splash_image_url
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
        print(f"\nУСПЕХ! Полная универсальная база готова. Найдено приложений: {len(store_database)}")
    except Exception as e:
        print(f"Ошибка записи JSON: {e}")

if __name__ == "__main__":
    generate_store_database()
