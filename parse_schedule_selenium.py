import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

URL = "https://api.nntu.ru/raspisanie"
GROUP_NAME = "АСИ 25-1"
OUTPUT_FILE = "schedule.json"


def setup_driver():
    options = Options()
    options.add_argument("--headless")  # режим без интерфейса
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    return driver


def load_schedule(driver, group_name):
    print("🌐 Загружаем страницу расписания...")
    driver.get(URL)

    wait = WebDriverWait(driver, 20)

    # --- 1️⃣ Форма обучения ---
    print("🎓 Выбираем форму обучения 'Очная'...")
    dept_select = wait.until(EC.presence_of_element_located(
        (By.ID, "studentAdvert__controls--department")))
    Select(dept_select).select_by_value("1")  # Очная

    time.sleep(2)

    # --- 2️⃣ Группа ---
    print(f"👥 Ищем группу '{group_name}'...")
    group_select = wait.until(EC.presence_of_element_located(
        (By.ID, "studentAdvert__controls--groups")))

    options = [opt.text.strip() for opt in group_select.find_elements(By.TAG_NAME, "option")]
    if group_name not in options:
        raise ValueError(f"Группа '{group_name}' не найдена!")

    Select(group_select).select_by_visible_text(group_name)
    time.sleep(2)

    # --- 3️⃣ Тип расписания ---
    print("📅 Выбираем 'Основное' расписание...")
    type_select = wait.until(EC.presence_of_element_located(
        (By.ID, "studentAdvert__controls--types")))
    Select(type_select).select_by_value("1")

    # --- 4️⃣ Ждём таблицу ---
    print("⏳ Ждём загрузку таблицы...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#printable table.raspTable")))
    time.sleep(2)

    # --- 5️⃣ Парсинг ---
    print("📖 Извлекаем данные...")
    tables = driver.find_elements(By.CSS_SELECTOR, "#printable table.raspTable")

    schedule = {
        "group": group_name,
        "type": "Основное",
        "days": []
    }

    for table in tables:
        day_name = table.find_element(By.TAG_NAME, "h3").text.strip()
        rows = table.find_elements(By.TAG_NAME, "tr")[2:]  # пропустить заголовки

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

        schedule["days"].append({
            "day": day_name,
            "lessons": lessons
        })

    print(f"✅ Собрано расписание на {len(schedule['days'])} дней.")
    return schedule


def save_schedule(schedule, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)
    print(f"💾 Сохранено в {path}")


def main():
    driver = setup_driver()
    try:
        schedule = load_schedule(driver, GROUP_NAME)
        save_schedule(schedule, OUTPUT_FILE)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
