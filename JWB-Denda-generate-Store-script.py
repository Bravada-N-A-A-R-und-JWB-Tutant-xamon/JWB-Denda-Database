print("=== СКРИПТ ЗАПУСТИЛСЯ, ПОГНАЛИ ===")
import os
import json

def is_ubuntu_touch_project(repo_path):
    """
    Проверяет, является ли папка проектом для Ubuntu Touch / Lomiri.
    Возвращает True, если найден хотя бы один маркер.
    """
    # Получаем список всех файлов в корне репозитория
    try:
        root_files = os.listdir(repo_path)
    except Exception:
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


# --- Твой основной цикл обхода репозиториев будет выглядеть так ---
def generate_store_database(apps_root_dir):
    store_database = []

    # Допустим, перебираем папки скачанных репозиториев организации
    for repo_name in os.listdir(apps_root_dir):
        repo_path = os.path.join(apps_root_dir, repo_name)
        
        if os.path.isdir(repo_path):
            # ВРУБАЕМ ТВОЙ ТРИГГЕР-ФИЛЬТР 🚨
            if not is_ubuntu_touch_project(repo_path):
                print(f"[{repo_name}] СКИП: не имеет отношения к Ubuntu Touch. НИ-НИ! ❌")
                continue # Сразу переходим к следующему репозиторию

            # Если проверка прошлась — значит это наш чел, парсим по полной!
            print(f"[{repo_name}] ОБНАРУЖЕН UT-ПРОЕКТ! Запускаем глубокий парсинг... 🟩")
            
            # Тут вызываешь нашу функцию глубокого парсинга deep_parse_app, которую написали выше
            app_data = deep_parse_app(repo_path, repo_name)
            store_database.append(app_data)

    # Сохраняем чистую базу данных
    output_path = os.path.join(apps_root_dir, "store_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(store_database, f, indent=4, ensure_ascii=False)
        
    print(f"\nБаза данных успешно отрендерена! Всего приложений в JWB-Denda: {len(store_database)}")
