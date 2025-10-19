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
    # options.add_argument("--headless")  # Убери для дебага
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")  # Fake UA
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


def select_option_robust(driver, select_element, partial_text):
    """Надёжный выбор опции: Select + fallback на manual click."""
    wait = WebDriverWait(driver, 10)
    
    try:
        # Сначала пробуем Select (стандартно)
        Select(select_element).select_by_visible_text(partial_text)
        print(f"✅ Выбрано через Select: '{partial_text}'")
        return True
    except NoSuchElementException:
        print(f"⚠️ Select фейлил для '{partial_text}', пробуем manual...")
        
        # Fallback: клик на select (открыть дропдаун)
        select_element.click()
        time.sleep(1)  # Ждём анимацию
        
        # Ждём и кликаем опцию
        option_locator = (By.XPATH, f".//option[contains(text(), '{partial_text}')]")
        option = wait.until(EC.element_to_be_clickable(option_locator))
        ActionChains(driver).move_to_element(option).click(option).perform()
        print(f"✅ Выбрано manual: '{partial_text}'")
        return True
    except Exception as e:
        print(f"❌ Fallback фейлил: {e}")
        # Debug опций при ошибке
        print(f"🔍 Опции в селекте '{select_element.get_attribute('id')}':")
        for opt in select_element.find_elements(By.TAG_NAME, "option"):
            print(f"  - '{opt.text.strip()}' (value: {opt.get_attribute('value')})")
        return False


def load_schedule(driver, group_name):
    print("🌐 Загружаем страницу расписания...")
    driver.get(URL)

    wait = WebDriverWait(driver, 25)

    # === 1️⃣ Форма обучения ===
    print("🎓 Ждём список форм обучения...")
    dept_select = wait.until(EC.element_to_be_clickable((By.ID, "studentAdvert__controls--department")))

    if not wait_for_option_text(dept_select, "Очная", timeout=20):
        raise RuntimeError("❌ Не найдена опция 'Очная'")

    if not select_option_robust(driver, dept_select, "Очная"):
        raise RuntimeError("❌ Не удалось выбрать 'Очная'")
    
    time.sleep(random.uniform(2, 4))

    # === 2️⃣ Группа ===
    print(f"👥 Ждём список групп и выбираем '{group_name}'...")
    group_select = wait.until(EC.element_to_be_clickable((By.ID, "studentAdvert__controls--groups")))

    if not wait_for_option_text(group_select, group_name, timeout=20):
        raise RuntimeError(f"❌ Группа '{group_name}' не найдена")

    if not select_option_robust(driver, group_select, group_name):
        raise RuntimeError(f"❌ Не удалось выбрать '{group_name}'")
    
    time.sleep(random.uniform(2, 4))

    # === 3️⃣ Тип расписания ===
    print("📅 Выбираем 'Основное'...")
    type_select = wait.until(EC.element_to_be_clickable((By.ID, "studentAdvert__controls--types")))
    if not select_option_robust(driver, type_select, "Основное"):
        raise RuntimeError("❌ Не удалось выбрать 'Основное'")
    
    time.sleep(random.uniform(1, 3))

    # === 4️⃣ Ждём таблицу ===
    print("⏳ Ждём таблицу...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#printable table.raspTable")))
    time.sleep(random.uniform(1, 2))

    # === 5️⃣ Парсинг ===
    print("📖 Извлекаем данные...")
    tables = driver.find_elements(By.CSS_SELECTOR, "#printable table.raspTable")

    schedule = {
        "group": group_name,
        "type": "Основное",
        "days": []
    }

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

        schedule["days"].append({
            "day": day_name,
            "lessons": lessons
        })

    print(f"✅ Собрано {len(schedule['days'])} дней.")
    return schedule


def save_schedule(schedule, path):
    """Сохраняет в JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)
    print(f"💾 Сохранено в {path}")


def main():
    driver = setup_driver()
    try:
        schedule = load_schedule(driver, GROUP_NAME)
        save_schedule(schedule, OUTPUT_FILE)
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
