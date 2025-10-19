import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

URL = "https://api.nntu.ru/raspisanie"
OUTPUT_FILE = "schedule.json"


def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    return driver


def wait_for_option_text(select_element, text, timeout=15):
    end_time = time.time() + timeout
    while time.time() < end_time:
        options = [opt.text.strip() for opt in select_element.find_elements(By.TAG_NAME, "option")]
        if text in options:
            return True
        time.sleep(0.5)
    return False


def load_schedule(driver, group_name):
    print(f"\n🌐 Загружаем расписание для {group_name}...")
    driver.get(URL)
    wait = WebDriverWait(driver, 25)

    # === Форма обучения ===
    dept_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--department")))
    if not wait_for_option_text(dept_select, "Очная", timeout=20):
        raise RuntimeError("❌ Не найдена опция 'Очная' — возможно, сайт не загрузился полностью.")
    Select(dept_select).select_by_visible_text("Очная")
    time.sleep(3)

    # === Группа ===
    group_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--groups")))
    if not wait_for_option_text(group_select, group_name, timeout=20):
        raise RuntimeError(f"❌ Группа '{group_name}' не найдена в списке!")
    Select(group_select).select_by_visible_text(group_name)
    time.sleep(3)

    # === Тип расписания ===
    type_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--types")))
    Select(type_select).select_by_visible_text("Основное")
    time.sleep(2)

    # === Ждём таблицу ===
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#printable table.raspTable")))
    time.sleep(2)

    # === Парсинг ===
    tables = driver.find_elements(By.CSS_SELECTOR, "#printable table.raspTable")

    schedule = {"group": group_name, "days": []}
    for table in tables:
        day_name = table.find_element(By.TAG_NAME, "h3").text.strip()
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

    print(f"✅ {group_name}: собрано {len(schedule['days'])} дней.")
    return schedule


def main():
    driver = setup_driver()
    all_schedules = {}

    try:
        print("🌐 Загружаем страницу и список групп...")
        driver.get(URL)
        wait = WebDriverWait(driver, 25)

        # Выбираем форму обучения
        dept_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--department")))
        Select(dept_select).select_by_visible_text("Очная")
        time.sleep(3)

        # Получаем список всех групп
        group_select = driver.find_element(By.ID, "studentAdvert__controls--groups")
        group_names = [
            opt.text.strip()
            for opt in group_select.find_elements(By.TAG_NAME, "option")
            if opt.text.strip().startswith("АСИ")
        ]

        print(f"📘 Найдено {len(group_names)} групп АСИ: {group_names}")

        for group_name in group_names:
            try:
                schedule = load_schedule(driver, group_name)
                all_schedules[group_name] = schedule
            except Exception as e:
                print(f"⚠️ Ошибка при {group_name}: {e}")
            time.sleep(5)  # Пауза между группами

        # Сохраняем в файл
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_schedules, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Все расписания сохранены в {OUTPUT_FILE}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
