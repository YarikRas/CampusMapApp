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


def normalize_text(s: str) -> str:
    """Убираем неразрывные пробелы и лишние пробелы, переводим в нижний регистр."""
    if s is None:
        return ""
    return " ".join(s.replace("\xa0", " ").split()).strip().lower()


def setup_driver():
    """Создаёт новый экземпляр Chrome с уникальным профилем (temp dir)."""
    user_data_dir = tempfile.mkdtemp()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    # дополнительные опции для устойчивости
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    return driver


def wait_for_option_text(select_element, text, timeout=20):
    """Ждём, пока в <select> появится опция с видимым текстом `text` (нормализуем текст)."""
    target = normalize_text(text)
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            opts = [opt.text for opt in select_element.find_elements(By.TAG_NAME, "option")]
        except Exception:
            opts = []
        normalized = [normalize_text(o) for o in opts]
        if target in normalized:
            return True
        time.sleep(0.5)
    return False


def load_schedule_for_group(driver, group_name):
    """Загружает расписание для одной группы; возвращает dict или None."""
    print(f"\n🌐 Загружаем страницу для {group_name}...")
    driver.get(URL)
    wait = WebDriverWait(driver, 30)

    # 1) дождаться селекта формы обучения и опции "Очная"
    try:
        dept_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--department")))
    except Exception as e:
        print("❌ Не смогли найти селект формы обучения:", e)
        return None

    if not wait_for_option_text(dept_select, "Очная", timeout=25):
        print("❌ Опция 'Очная' не появилась. Пропуск группы.")
        return None

    try:
        Select(dept_select).select_by_visible_text("Очная")
    except Exception:
        # last-resort: выбрать по value, если есть option с value != null и text содержит "Очная"
        for opt in dept_select.find_elements(By.TAG_NAME, "option"):
            if "очная" in normalize_text(opt.text) and opt.get_attribute("value") and opt.get_attribute("value") != "null":
                try:
                    Select(dept_select).select_by_value(opt.get_attribute("value"))
                    break
                except Exception:
                    pass
        else:
            print("❌ Не удалось выбрать 'Очная' ни по тексту, ни по значению.")
            return None

    time.sleep(1.5)

    # 2) дождаться селекта групп и появления нужной группы
    try:
        group_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--groups")))
    except Exception as e:
        print("❌ Не смогли найти селект групп:", e)
        return None

    if not wait_for_option_text(group_select, group_name, timeout=25):
        print(f"❌ Группа '{group_name}' не появилась в списке. Пропуск.")
        return None

    try:
        Select(group_select).select_by_visible_text(group_name)
    except Exception:
        # fallback: попытка выбрать по нормализованному тексту (итерируем опции)
        chosen = False
        for opt in group_select.find_elements(By.TAG_NAME, "option"):
            if normalize_text(opt.text) == normalize_text(group_name):
                try:
                    Select(group_select).select_by_value(opt.get_attribute("value"))
                    chosen = True
                    break
                except Exception:
                    pass
        if not chosen:
            print(f"❌ Не удалось выбрать группу '{group_name}' (ни по тексту, ни по value).")
            return None

    time.sleep(1.5)

    # 3) выбрать "Основное"
    try:
        type_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--types")))
    except Exception:
        print("❌ Не найден селект типа расписания.")
        return None

    if not wait_for_option_text(type_select, "Основное", timeout=10):
        print("❌ Тип 'Основное' не найден. Пропуск.")
        return None
    try:
        Select(type_select).select_by_visible_text("Основное")
    except Exception:
        # fallback: выбрать по нормализованному тексту
        for opt in type_select.find_elements(By.TAG_NAME, "option"):
            if normalize_text(opt.text) == "основное":
                try:
                    Select(type_select).select_by_value(opt.get_attribute("value"))
                    break
                except Exception:
                    pass

    time.sleep(2)

    # 4) ждать таблицы
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#printable table.raspTable")))
    except Exception:
        print(f"⚠️ Таблица не появилась для {group_name}")
        return None

    time.sleep(1)
    tables = driver.find_elements(By.CSS_SELECTOR, "#printable table.raspTable")
    schedule = {"group": group_name, "type": "Основное", "days": []}

    for table in tables:
        try:
            day_name = table.find_element(By.TAG_NAME, "h3").text.strip()
        except Exception:
            day_name = "Неизвестный день"

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
    """Возвращает список всех доступных групп с сайта (после выбора 'Очная')."""
    driver = None
    try:
        driver = setup_driver()
        driver.get(URL)
        wait = WebDriverWait(driver, 25)

        dept_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--department")))
        if not wait_for_option_text(dept_select, "Очная", timeout=25):
            raise RuntimeError("Опция 'Очная' не появилась — проверь сайт/задержку.")
        try:
            Select(dept_select).select_by_visible_text("Очная")
        except Exception:
            # fallback: выбрать по value, если есть опция с текстом содержащая 'очная'
            selected = False
            for opt in dept_select.find_elements(By.TAG_NAME, "option"):
                if "очная" in normalize_text(opt.text) and opt.get_attribute("value") and opt.get_attribute("value") != "null":
                    Select(dept_select).select_by_value(opt.get_attribute("value"))
                    selected = True
                    break
            if not selected:
                raise RuntimeError("Не удалось выбрать 'Очная' ни по тексту, ни по value.")

        time.sleep(2)
        group_select = wait.until(EC.presence_of_element_located((By.ID, "studentAdvert__controls--groups")))
        # Подготовка списка групп: исключаем заглушку "Выберите группу"
        opts = group_select.find_elements(By.TAG_NAME, "option")
        groups = []
        for opt in opts:
            val = opt.get_attribute("value")
            txt = opt.text.strip()
            if not val or val == "null" or txt == "":
                continue
            groups.append(txt)
        return groups

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def save_schedule(all_schedules):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_schedules, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Сохранено в {OUTPUT_FILE}")


def main():
    all_schedules = {}
    try:
        groups = get_all_groups()
    except Exception as e:
        print("❌ Не удалось получить список групп:", e)
        return

    print(f"📋 Групп для обработки: {len(groups)}")

    for i, group_name in enumerate(groups, start=1):
        print(f"\n[{i}/{len(groups)}] Обрабатываем: {group_name}")
        driver = None
        try:
            driver = setup_driver()
            schedule = load_schedule_for_group(driver, group_name)
            if schedule:
                all_schedules[group_name] = schedule
        except Exception as e:
            print(f"⚠️ Ошибка при {group_name}: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        time.sleep(2)

    save_schedule(all_schedules)


if __name__ == "__main__":
    main()
