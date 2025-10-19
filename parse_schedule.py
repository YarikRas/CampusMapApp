import requests
from bs4 import BeautifulSoup
import json

# === Настройки ===
API_BASE = "https://api.nntu.ru"
DEPARTMENT_ID = 1  # Очная форма
#GROUP_NAME = "МА 25ПМ"  # можно поменять под любую группу
GROUP_NAME = "АСИ 25-1"  # можно поменять под любую группу
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

# === 1. Получаем список групп ===
def get_groups():
    url = f"{API_BASE}/getgroups"
    data = {"department_id": DEPARTMENT_ID}
    resp = requests.post(url, data=data, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

# === 2. Находим ID нужной группы ===
def find_group_id(groups, group_name):
    for g in groups:
        # На всякий случай приводим к одному регистру
        if g.get("name", "").strip().lower() == group_name.strip().lower():
            return g.get("id") or g.get("group_id")
    raise ValueError(f"Группа '{group_name}' не найдена")

# === 3. Получаем HTML расписания ===
def get_schedule(group_id):
    url = f"{API_BASE}/getschedule"
    data = {
        "department_id": DEPARTMENT_ID,
        "group_id": group_id,
        "type": 1,
        "date_from": None,
        "date_to": None
    }
    resp = requests.post(url, data=data, headers=HEADERS)
    resp.raise_for_status()
    return resp.text

# === 4. Парсим HTML в JSON ===
def parse_schedule(html):
    soup = BeautifulSoup(html, "html.parser")
    schedule = {}

    # Обычно дни — это <h3> с названием дня
    for day_header in soup.find_all(["h3", "h2"]):
        day_name = day_header.get_text(strip=True)
        table = day_header.find_next("table")
        if not table:
            continue

        lessons = []
        for tr in table.find_all("tr")[1:]:  # пропускаем шапку таблицы
            cols = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cols) >= 3:
                lessons.append({
                    "time": cols[0],
                    "subject": cols[1],
                    "teacher": cols[2],
                    "room": cols[3] if len(cols) > 3 else "",
                    "note": cols[4] if len(cols) > 4 else "",
                    "week": cols[5] if len(cols) > 5 else ""
                })

        if lessons:
            schedule[day_name] = lessons

    return schedule

# === 5. Сохраняем в JSON ===
def save_schedule(data, filename="schedule.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Сохранено: {filename}")

# === Основной запуск ===
def main():
    print("📡 Получаем список групп...")
    groups = get_groups()

    print(f"🔍 Ищем группу '{GROUP_NAME}'...")
    group_id = find_group_id(groups, GROUP_NAME)
    print(f"📘 Найдена группа {GROUP_NAME} (id={group_id})")

    print("📅 Загружаем расписание...")
    html = get_schedule(group_id)

    print("🧩 Парсим HTML...")
    schedule = parse_schedule(html)

    save_schedule(schedule)
    print("🎉 Готово!")

if __name__ == "__main__":
    main()
