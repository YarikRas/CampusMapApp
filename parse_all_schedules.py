import time
import json
import tempfile
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

URL = "https://api.nntu.ru/raspisanie"
OUTPUT_FILE = "schedule.json"


def setup_driver():
    """Создаёт новый экземпляр Chrome с уникальным профилем."""
    user_data_dir = tempfile.mkdtemp()
    options = Options()
    options.add_argument("--headless")  # Без интерфейса
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    return driver


def wait_for_option_text(select_element, text, timeout=15):
    """Ждём, пока появится нужная <option> по тексту."""
    end_time = time.time() + timeout
    while time.time() < end_time:
        options = [opt.text.strip() for opt in select_element.find_elements(By.TAG_NAME, "option")]
        if text in options:
            return True
        time.sleep(0.5)
    return False


def load_schedule(driver, group_name):
    """Парсит расписание одной группы."""
    print(f"\n🌐 Загружаем страницу для {group_name}...")
    driver.get(URL)

    wait = WebDriverWait(driver, 25)

    # === 1️⃣ Форма обучения ===
    dept_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--department")))
    if not wait_for_option_text(dept_select, "Очная", timeout=20):
        raise RuntimeError("❌ Не найдена опция 'Очная' — возможно, сайт не загрузился полностью.")
    Select(dept_select).select_by_visible_text("Очная")
    time.sleep(3)

    # === 2️⃣ Группа ===
    group_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--groups")))
    if not wait_for_option_text(group_select, group_name, timeout=20):
        print(f"⚠️ Пропускаем: группа '{group_name}' не найдена.")
        return None
    Select(group_select).select_by_visible_text(group_name)
    time.sleep(3)

    # === 3️⃣ Тип расписания ===
    type_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--types")))
    Select(type_select).select_by_visible_text("Основное")
    time.sleep(2)

    # === 4️⃣ Ждём таблицу ===
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#printable table.raspTable")))
    except:
        print(f"⚠️ Таблица для '{group_name}' не найдена.")
        return None
    time.sleep(2)

    # === 5️⃣ Парсинг ===
    tables = driver.find_elements(By.CSS_SELECTOR, "#printable table.raspTable")
    schedule = {"group": group_name, "type": "Основное", "days": []}

    for table in tables:
        try:
            day_name = table.find_element(By.TAG_NAME, "h3").text.strip()
        except:
            continue
        rows = table.find_elements(By.TAG_NAME, "tr")[2:]
        lessons = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 6:
                continue
            pair, subject, teacher, room, note, week = [c.text.strip() for c in cols]
            lessons.append({
                "pair": pair,
                "subject": subject,
                "teacher": teacher,
                "room": room,
                "note": note,
                "week": week
            })
        schedule["days"].append({"day": day_name, "lessons": lessons})

    print(f"✅ Собрано {len(schedule['days'])} дней для {group_name}")
    return schedule


def get_all_groups():
    """Возвращает список всех доступных групп с сайта."""
    print("🌍 Загружаем список всех групп...")
    driver = setup_driver()
    driver.get(URL)
    wait = WebDriverWait(driver, 25)
    dept_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--department")))
    Select(dept_select).select_by_visible_text("Очная")
    time.sleep(3)

    group_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--groups")))
    groups = [opt.text.strip() for opt in group_select.find_elements(By.TAG_NAME, "option") if opt.get_attribute("value") != "null"]
    driver.quit()
    print(f"📋 Найдено {len(groups)} групп.")
    return groups


def save_schedule(all_schedules):
    """Сохраняет все расписания в один JSON."""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_schedules, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Все расписания сохранены в {OUTPUT_FILE}")


def main():
    all_schedules = {}
    groups = get_all_groups()

    for i, group_name in enumerate(groups, start=1):
        print(f"\n[{i}/{len(groups)}] Обработка {group_name}...")
        driver = setup_driver()
        try:
            schedule = load_schedule(driver, group_name)
            if schedule:
                all_schedules[group_name] = schedule
        except Exception as e:
            print(f"⚠️ Ошибка при обработке {group_name}: {e}")
        finally:
            driver.quit()
        time.sleep(2)  # небольшая пауза между запросами

    save_schedule(all_schedules)


if __name__ == "__main__":
    main()
