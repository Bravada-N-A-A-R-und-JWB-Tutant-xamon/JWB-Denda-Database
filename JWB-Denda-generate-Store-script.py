#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("=== СКРИПТ ЗАПУСТИЛСЯ, ПОГНАЛИ ===")

import os
import json

def is_ubuntu_touch_project(repo_path):
    """
    Проверяет, является ли папка проектом для Ubuntu Touch / Lomiri.
    Возвращает True, если найден хотя бы один маркер.
    """
    try:
        root_files = os.listdir(repo_path)
    except Exception as e:
        print(f"Ошибка чтения папки {repo_path}: {e}")
        return False

    # 1. Проверяем точные совпадения по именам (конфиги кликабла и манифест)
    ut_exact_files = ["manifest.json", "clickable.yaml", "clickable.json"]
    for file in ut_exact_files:
        if file in root_files:
            return True

    # 2. Проверяем файлы по расширениям (.desktop и .apparmor)
    for file in root_files:
        if file.endswith(".desktop") or file.endswith(".apparmor"):
            return True

    # Если ни один маркер не нашелся — это левый репозиторий
    return False


def deep_parse_app(repo_path, repo_name):
    """
    Выполняет глубокий парсинг манифестов и метаданных приложения.
    Сюда можно добавлять чтение иконок, версий, описаний и т.д.
    """
    app_data = {
        "name": repo_name,
        "repository_url": f"https://github.com/Bravada-n-A-a-R-und-jwb-tutant-xamon/{repo_name}",
        "type": "Ubuntu Touch App",
        "status": "Active"
    }

    # Пытаемся вытянуть реальные данные из манифеста, если он есть
    manifest_path = os.path.join(repo_path, "manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                app_data["display_name"] = manifest.get("title", repo_name)
                app_data["version"] = manifest.get("version", "1.0.0")
                app_data["description"] = manifest.get("description", "Нет описания.")
        except Exception as e:
            print(f"[{repo_name}] Предупреждение: Не удалось распарсить manifest.json: {e}")
    else:
        app_data["display_name"] = repo_name
        app_data["version"] = "1.0.0"
        app_data["description"] = "Репозиторий под кодом JWB, манифест не найден."

    return app_data


def generate_store_database(apps_root_dir):
    """
    Основной цикл обхода репозиториев организации и генерации JSON-базы.
    """
    store_database = []
    
    print(f"Сканируем директорию: {os.path.abspath(apps_root_dir)}")

    # Перебираем папки скачанных репозиториев организации
    try:
        items = os.listdir(apps_root_dir)
    except Exception as e:
        print(f"Критическая ошибка: Не удалось прочитать apps_root_dir: {e}")
        return

    for repo_name in items:
        # Пропускаем саму системную папку гита, скрытые папки и файлы
        if repo_name.startswith("."):
            continue
            
        repo_path = os.path.join(apps_root_dir, repo_name)
        
        if os.path.isdir(repo_path):
            # ВРУБАЕМ ТВОЙ ТРИГГЕР-ФИЛЬТР 🚨
            if not is_ubuntu_touch_project(repo_path):
                print(f"[{repo_name}] СКИП: не имеет отношения к Ubuntu Touch. НИ-НИ! ❌")
                continue # Сразу переходим к следующему репозиторию

            # Если проверка прошлась — значит это наш чел, парсим по полной!
            print(f"[{repo_name}] ОБНАРУЖЕН UT-ПРОЕКТ! Запускаем глубокий парсинг... 🟩")
            
            app_data = deep_parse_app(repo_path, repo_name)
            store_database.append(app_data)

    # Определяем путь для сохранения готовой базы
    output_path = os.path.join(apps_root_dir, "store_data.json")
    
    # Сохраняем чистую базу данных
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(store_database, f, indent=4, ensure_ascii=False)
        print(f"\nБаза данных успешно отрендерена! Всего приложений в JWB-Denda: {len(store_database)}")
    except Exception as e:
        print(f"Ошибка при записи файла базы данных store_data.json: {e}")


# --- ТОЧКА ВХОДА ДЛЯ GITHUB ACTIONS ---
if __name__ == "__main__":
    # Передаем "." — текущую папку корня репозитория в Actions
    generate_store_database(".")
