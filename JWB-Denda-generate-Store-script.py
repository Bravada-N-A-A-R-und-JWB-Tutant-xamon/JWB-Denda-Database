import os
import json
import re

def deep_parse_app(repo_path, repo_name):
    # Дефолты на случай, если файлы битые
    app_data = {
        "repoName": repo_name,
        "appName": repo_name,
        "appVersion": "1.0.0",
        "appAuthor": "Unknown",
        "appCategory": "apps",
        "appDescription": "",
        "appIcon": "qrc:/Assets/JWB-Denda Logo (none).svg",
        "appSplashColor": "#141414",
        "readme": ""
    }

    manifest_path = os.path.join(repo_path, "manifest.json")
    desktop_filename = None

    # 1. ПАРСИМ MANIFEST.JSON
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                man = json.load(f)
                
                # Читаем базовые инфо-поля
                app_data["appName"] = man.get("title", man.get("name", repo_name))
                app_data["appVersion"] = man.get("version", "1.0.0")
                app_data["appDescription"] = man.get("description", "")
                
                # Чистим майнтейнера до символа '<'
                maintainer = man.get("maintainer", "")
                if "<" in maintainer:
                    maintainer = maintainer.split("<")[0].strip()
                app_data["appAuthor"] = maintainer if maintainer else "Unknown"

                # Вытаскиваем имя десктоп-файла из хуков
                hooks = man.get("hooks", {})
                for hook_key, hook_value in hooks.items():
                    if isinstance(hook_value, dict) and "desktop" in hook_value:
                        desktop_filename = hook_value["desktop"]
                        break

        except Exception as e:
            print(f"[{repo_name}] Ошибка чтения manifest.json: {e}")

    # Если в хуках десктоп не нашли, ищем по старинке любой .desktop в корне
    if not desktop_filename:
        for file in os.listdir(repo_path):
            if file.endswith(".desktop"):
                desktop_filename = file
                break

    # 2. ПАРСИМ .DESKTOP ФАЙЛ (Иконка и Сплэш в HEX)
    if desktop_filename:
        desktop_path = os.path.join(repo_path, desktop_filename)
        if os.path.exists(desktop_path):
            try:
                with open(desktop_path, 'r', encoding='utf-8') as f:
                    desktop_content = f.read()

                    # Читаем Icon= (путь и файл после знака равно)
                    icon_match = re.search(r'^Icon\s*=\s*(.*)', desktop_content, re.MULTILINE)
                    if icon_match:
                        app_data["appIcon"] = icon_match.group(1).strip()

                    # Читаем цвета сплэша (Lomiri или Ubuntu)
                    splash_match = re.search(r'^(?:X-Lomiri-Splash-Color|X-Ubuntu-Splash-Color)\s*=\s*(.*)', desktop_content, re.MULTILINE | re.IGNORECASE)
                    if splash_match:
                        app_data["appSplashColor"] = splash_match.group(1).strip()

                    # Заодно вытащим категорию, если она есть
                    cat_match = re.search(r'^X-Lomiri-Default-Department-ID\s*=\s*(.*)', desktop_content, re.MULTILINE | re.IGNORECASE)
                    if cat_match:
                        app_data["appCategory"] = cat_match.group(1).strip().lower()

            except Exception as e:
                print(f"[{repo_name}] Ошибка чтения десктопа {desktop_filename}: {e}")

    # 3. ВЫТЯГИВАЕМ README.MD
    readme_path = os.path.join(repo_path, "README.md")
    if os.path.exists(readme_path):
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                app_data["readme"] = f.read()
        except Exception as e:
            print(f"[{repo_name}] Не удалось прочесть README.md: {e}")

    return app_data
