#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("=== СБОРКА БАЗЫ JWB-DENDA ЧЕРЕЗ GITHUB API ===")

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

def get_file_from_repo(org_name, repo_name, file_path, token=None):
    """Пытается скачать конкретный файл из корня ветки по умолчанию."""
    url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/main/{file_path}"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
        
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception:
        # Если в main нет, попробуем master на всякий случай
        url_master = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/master/{file_path}"
        req_master = urllib.request.Request(url_master, headers=headers)
        try:
            with urllib.request.urlopen(req_master) as response:
                return response.read().decode('utf-8')
        except Exception:
            return None

def generate_store_database():
    org_name = "Bravada-n-A-a-R-und-jwb-tutant-xamon"
    # GitHub автоматически подсовывает этот токен в переменные окружения воркфлоу
    token = os.getenv("GITHUB_TOKEN")
    
    print(f"Запрос репозиториев для организации: {org_name}")
    repos = get_organization_repos(org_name, token)
    
    store_database = []
    print(f"Найдено репозиториев в организации: {len(repos)}")

    for repo in repos:
        repo_name = repo["name"]
        
        # Пропускаем саму репу базы данных, чтобы не зацикливаться
        if repo_name == "JWB-Denda-Database":
            continue

        print(f"[{repo_name}] Проверяем маркеры Ubuntu Touch...")
        
        # Проверяем наличие маркеров удалённо через Raw GitHub
        has_ut_marker = False
        manifest_content = None
        
        # Список файлов-маркеров
        for marker in ["manifest.json", "clickable.yaml", "clickable.json"]:
            content = get_file_from_repo(org_name, repo_name, marker, token)
            if content:
                has_ut_marker = True
                if marker == "manifest.json":
                    manifest_content = content
                break

        if not has_ut_marker:
            print(f"[{repo_name}] СКИП: Маркеры UT не найдены. ❌")
            continue

        print(f"[{repo_name}] ОБНАРУЖЕН UT-ПРОЕКТ! Парсим метаданные... 🟩")
        
        # Базовый каркас данных из API гитхаба
        app_data = {
            "name": repo_name,
            "repository_url": repo["html_url"],
            "display_name": repo_name,
            "version": "1.0.0",
            "description": repo["description"] if repo["description"] else "Репозиторий экосистемы JWB.",
            "type": "Ubuntu Touch App",
            "status": "Active"
        }

        # Если нашли реальный manifest.json, забираем данные оттуда
        if manifest_content:
            try:
                manifest = json.loads(manifest_content)
                app_data["display_name"] = manifest.get("title", repo_name)
                app_data["version"] = manifest.get("version", "1.0.0")
                if manifest.get("description"):
                    app_data["description"] = manifest.get("description")
            except Exception as e:
                print(f"[{repo_name}] Ошибка разбора манифеста: {e}")

        store_database.append(app_data)

    # Сохраняем результат прямо в корень для деплоя
    output_path = "store_data.json"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(store_database, f, indent=4, ensure_ascii=False)
        print(f"\nУСПЕХ! База обновлена. Приложений в JWB-Denda: {len(store_database)}")
    except Exception as e:
        print(f"Ошибка записи JSON: {e}")

if __name__ == "__main__":
    generate_store_database()
