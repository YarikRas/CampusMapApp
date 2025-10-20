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
    # если используешь webdriver-manager, можно его сюда подключить; в Actions chromedriver уже должен быть в PATH
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    return driver


def wait_for_option_text(select_element, text, timeout=20):
    """Ждём, пока в <select> появится опция с видимым текстом `text`."""
    end_time = time.time() + timeout
    while time.time() < end_time:
        opts = [opt.text.strip() for opt in select_element.find_elements(By.TAG_NAME, "option")]
        if text in opts:
            return True
        time.sleep(0.5)
    return False


def load_schedule_for_group(driver, group_name):
    """Загружает расписание для одной группы (возвращает dict или None)."""
    print(f"\n🌐 Загружаем расписание для '{group_name}'...")
    driver.get(URL)
    wait = WebDriverWait(driver, 30)

    # 1) дождаться селекта формы обучения и опции "Очная"
    dept_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--department")))
    if not wait_for_option_text(dept_select, "Очная", timeout=25):
        print("❌ Опция 'Очная' не появилась. Пропуск группы.")
        return None
    Select(dept_select).select_by_visible_text("Очная")
    time.sleep(1.5)

    # 2) дождаться селекта групп и появления нужной группы
    group_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--groups")))
    if not wait_for_option_text(group_select, group_name, timeout=25):
        print(f"❌ Группа '{group_name}' не появилась в списке. Пропуск.")
        return None
    Select(group_select).select_by_visible_text(group_name)
    time.sleep(1.5)

    # 3) выбрать "Основное"
    type_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--types")))
    if not wait_for_option_text(type_select, "Основное", timeout=10):
        print("❌ Тип 'Основное' не найден. Пропуск.")
        return None
    Select(type_select).select_by_visible_text("Основное")
    time.sleep(1.5)

    # 4) ждать, пока появятся таблицы
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#printable table.raspTable")))
    except Exception:
        print(f"⚠️ Таблица не появилась для {group_name}")
        return None

    time.sleep(0.8)
    tables = driver.find_elements(By.CSS_SELECTOR, "#printable table.raspTable")
    schedule = {"group": group_name, "type": "Основное", "days": []}

    for table in tables:
        # заголовок дня лежит внутри <th colspan..><h3>Day</h3>
        try:
            day_name = table.find_element(By.TAG_NAME, "h3").text.strip()
        except Exception:
            # на некоторых таблицах может быть другая структура — попробуем найти ближайший <thead> -> h3
            day_name = "Неизвестный день"

        # строки с парами — пропускаем 2 строки заголовка (как в твоём примере)
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


def main():
    driver = setup_driver()
    all_schedules = {}

    try:
        print("🌍 Открываем страницу, получаем список групп...")
        driver.get(URL)
        wait = WebDriverWait(driver, 30)

        # дождаться селекта формы обучения и выбрать "Очная"
        dept_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--department")))
        if not wait_for_option_text(dept_select, "Очная", timeout=25):
            raise RuntimeError("Опция 'Очная' не появилась вообще — проверь страницу.")
        Select(dept_select).select_by_visible_text("Очная")
        time.sleep(2)

        # дождаться селекта групп
        group_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--groups")))
        # собрать все опции кроме заглушки "Выберите группу"
        group_options = [opt.text.strip() for opt in group_select.find_elements(By.TAG_NAME, "option") if opt.get_attribute("value") and opt.get_attribute("value") != "null" and opt.text.strip()]
        print(f"📋 Всего групп найдено: {len(group_options)}")

        # можно фильтровать, например только группы начинающиеся с "АСИ"
        # group_options = [g for g in group_options if g.startswith("АСИ")]

        for idx, group_name in enumerate(group_options, start=1):
            print(f"\n🔸 [{idx}/{len(group_options)}] Обработка группы: {group_name}")
            try:
                # ВАЖНО: для стабильности заново грузим страницу внутри функции load_schedule_for_group
                schedule = load_schedule_for_group(driver, group_name)
                if schedule:
                    all_schedules[group_name] = schedule
            except Exception as e:
                print(f"⚠️ Ошибка при обработке {group_name}: {e}")
            # небольшая пауза чтобы не перегружать сайт
            time.sleep(2)

        # сохранить JSON
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_schedules, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Сохранено расписаний: {len(all_schedules)} --> {OUTPUT_FILE}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
