import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

URL = "https://api.nntu.ru/raspisanie"
GROUP_NAME = "МА 25ПМ"
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
    print("🌐 Загружаем страницу расписания...")
    driver.get(URL)

    wait = WebDriverWait(driver, 25)

    # === 1️⃣ Форма обучения ===
    print("🎓 Ждём появление списка форм обучения...")
    dept_select = wait.until(EC.presence_of_element_located(
        (By.ID, "studentAdvert__controls--department")
    ))

    if not wait_for_option_text(dept_select, "Очная", timeout=20):
        raise RuntimeError("❌ Не найдена опция 'Очная' — возможно, сайт не загрузился полностью.")

    Select(dept_select).select_by_visible_text("Очная")
    print("✅ Выбрана форма обучения 'Очная'")
    time.sleep(3)

    # === 2️⃣ Группа ===
    print(f"👥 Ждём загрузку списка групп и выбираем '{group_name}'...")
    group_select = wait.until(EC.presence_of_element_located(
        (By.ID, "studentAdvert__controls--groups")
    ))

    if not wait_for_option_text(group_select, group_name, timeout=20):
        raise RuntimeError(f"❌ Группа '{group_name}' не найдена в списке!")

    Select(group_select).select_by_visible_text(group_name)
    print(f"✅ Выбрана группа '{group_name}'")
    time.sleep(3)

    # === 3️⃣ Тип расписания ===
    print("📅 Выбираем 'Основное' расписание...")
    type_select = wait.until(EC.presence_of_element_located(
        (By.ID, "studentAdvert__controls--types")
    ))
    Select(type_select).select_by_visible_text("Основное")
    time.sleep(2)

    # === 4️⃣ Ждём таблицу ===
    print("⏳ Ждём загрузку таблицы...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#printable table.raspTable")))
    time.sleep(2)

    # === 5️⃣ Парсинг таблиц ===
    print("📖 Извлекаем данные...")
    tables = driver.find_elements(By.CSS_SELECTOR, "#printable table.raspTable")

    schedule = {
        "group": group_name,
        "type": "Основное",
        "days": []
    }

    for table in tables:
        day_name = table.find_element(By.TAG_NAME, "h3").text.strip()
        rows = table.find_elements(By.TAG_NAME, "tr")[2:]  # Пропускаем заголовки

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
    """Сохраняет результат в JSON."""
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
