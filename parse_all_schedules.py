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
    """Настройка Selenium Chrome."""
    options = Options()
    options.add_argument("--headless")  # Без интерфейса
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
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
    """Загружает расписание для одной группы."""
    print(f"\n🌐 Загружаем расписание для '{group_name}'...")
    driver.get(URL)

    wait = WebDriverWait(driver, 30)

    # === 1️⃣ Форма обучения ===
    dept_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--department")))
    if not wait_for_option_text(dept_select, "Очная", timeout=20):
        print("❌ Не найдена форма обучения 'Очная'. Пропуск.")
        return None

    Select(dept_select).select_by_visible_text("Очная")
    time.sleep(3)

    # === 2️⃣ Группа ===
    group_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--groups")))
    if not wait_for_option_text(group_select, group_name, timeout=20):
        print(f"❌ Группа '{group_name}' не найдена.")
        return None

    Select(group_select).select_by_visible_text(group_name)
    time.sleep(3)

    # === 3️⃣ Тип расписания ===
    type_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--types")))
    Select(type_select).select_by_visible_text("Основное")
    time.sleep(2)

    # === 4️⃣ Таблица ===
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#printable table.raspTable")))
    except Exception:
        print(f"⚠️ Таблица не найдена для {group_name}")
        return None

    time.sleep(1)
    tables = driver.find_elements(By.CSS_SELECTOR, "#printable table.raspTable")

    schedule = {"group": group_name, "type": "Основное", "days": []}

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

    print(f"✅ Собрано расписание для '{group_name}' — {len(schedule['days'])} дней.")
    return schedule


def main():
    driver = setup_driver()
    all_schedules = []

    try:
        print("🌍 Загружаем список всех групп...")
        driver.get(URL)
        wait = WebDriverWait(driver, 25)

        # Выбираем "Очная", чтобы список групп загрузился
        dept_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--department")))
        Select(dept_select).select_by_visible_text("Очная")
        time.sleep(3)

        group_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--groups")))
        group_options = [opt.text.strip() for opt in group_select.find_elements(By.TAG_NAME, "option") if opt.get_attribute("value") != "null"]

        print(f"📋 Найдено групп: {len(group_options)}")

        for i, group_name in enumerate(group_options, 1):
            try:
                print(f"\n🔹 [{i}/{len(group_options)}] {group_name}")
                schedule = load_schedule(driver, group_name)
                if schedule:
                    all_schedules.append(schedule)
            except Exception as e:
                print(f"⚠️ Ошибка при {group_name}: {e}")
            time.sleep(2)

        # Сохраняем все данные
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_schedules, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Сохранено расписаний: {len(all_schedules)} в {OUTPUT_FILE}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
