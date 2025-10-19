import time
import json
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

URL = "https://api.nntu.ru/raspisanie"
GROUP_NAME = "АСИ 25-1"
OUTPUT_FILE = "schedule.json"


def setup_driver():
    """Настройка Selenium Chrome."""
    options = Options()
    options.add_argument("--headless")  # Убери для дебага: options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
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


def select_option_by_partial_text(driver, select_element, partial_text):
    """Выбираем опцию по частичному совпадению текста (игнорирует пробелы)."""
    try:
        # Debug: выводим все опции с repr для скрытых символов
        print(f"🔍 Доступные опции в селекте '{select_element.get_attribute('id')}':")
        for opt in select_element.find_elements(By.TAG_NAME, "option"):
            print(f"  - repr: {repr(opt.text)} | stripped: '{opt.text.strip()}'")
        
        # Ищем опцию по XPath (contains игнорирует лишнее)
        option = select_element.find_element(By.XPATH, f".//option[contains(text(), '{partial_text}')]")
        ActionChains(driver).move_to_element(option).click(option).perform()
        print(f"✅ Выбрана опция, содержащая '{partial_text}'")
        return True
    except NoSuchElementException:
        print(f"❌ Не удалось выбрать опцию с текстом '{partial_text}'")
        return False


def load_schedule(driver, group_name):
    print("🌐 Загружаем страницу расписания...")
    driver.get(URL)

    wait = WebDriverWait(driver, 25)

    # === 1️⃣ Форма обучения ===
    print("🎓 Ждём появление списка форм обучения...")
    dept_select = wait.until(EC.element_to_be_clickable(  # Изменили на clickable
        (By.ID, "studentAdvert__controls--department")
    ))

    if not wait_for_option_text(dept_select, "Очная", timeout=20):
        raise RuntimeError("❌ Не найдена опция 'Очная' — возможно, сайт не загрузился полностью.")

    # Manual select с debug
    if not select_option_by_partial_text(driver, dept_select, "Очная"):
        raise RuntimeError("❌ Не удалось кликнуть на 'Очная' — проверь debug-вывод!")
    
    print("✅ Выбрана форма обучения 'Очная'")
    time.sleep(random.uniform(2, 4))  # Random delay

    # === 2️⃣ Группа ===
    print(f"👥 Ждём загрузку списка групп и выбираем '{group_name}'...")
    group_select = wait.until(EC.element_to_be_clickable(  # Clickable
        (By.ID, "studentAdvert__controls--groups")
    ))

    if not wait_for_option_text(group_select, group_name, timeout=20):
        raise RuntimeError(f"❌ Группа '{group_name}' не найдена в списке!")

    # Manual select для групп тоже (на всякий)
    if not select_option_by_partial_text(driver, group_select, group_name):
        raise RuntimeError(f"❌ Не удалось кликнуть на группу '{group_name}'")
    
    print(f"✅ Выбрана группа '{group_name}'")
    time.sleep(random.uniform(2, 4))

    # === 3️⃣ Тип расписания ===
    print("📅 Выбираем 'Основное' расписание...")
    type_select = wait.until(EC.element_to_be_clickable(
        (By.ID, "studentAdvert__controls--types")
    ))
    # Для типов используем Select, но с fallback
    try:
        Select(type_select).select_by_visible_text("Основное")
    except NoSuchElementException:
        if not select_option_by_partial_text(driver, type_select, "Основное"):
            raise RuntimeError("❌ Не удалось выбрать 'Основное'")
    time.sleep(random.uniform(1, 3))

    # === 4️⃣ Ждём таблицу ===
    print("⏳ Ждём загрузку таблицы...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#printable table.raspTable")))
    time.sleep(random.uniform(1, 2))

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
    except (TimeoutException, NoSuchElementException) as e:
        print(f"⚠️ Selenium-ошибка: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
