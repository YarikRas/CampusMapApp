import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://api.nntu.ru/raspisanie"
GROUPS_URL = "https://api.nntu.ru/getgroups"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

def get_groups(department_id=1):
    resp = requests.post(GROUPS_URL, data={"department_id": department_id}, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def get_schedule_html(group_id, department_id=1):
    data = {
        "department_id": department_id,
        "group_id": group_id,
        "type": 1,
        "date_from": "",
        "date_to": ""
    }
    resp = requests.post(BASE_URL, data=data, headers=HEADERS)
    resp.raise_for_status()
    return resp.text

def parse_schedule(html):
    soup = BeautifulSoup(html, "html.parser")
    schedule = {}

    for day_header in soup.find_all(["h3", "h2"]):
        day_name = day_header.get_text(strip=True)
        table = day_header.find_next("table")
        if not table:
            continue
        lessons = []
        for tr in table.find_all("tr")[1:]:
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
        schedule[day_name] = lessons

    return schedule

def main():
    print("📡 Получаем список групп...")
    groups = get_groups()
    all_schedules = {}

    for group in groups:
        group_name = group["name"]
        group_id = group.get("id") or group.get("group_id")
        print(f"📘 Загружаем {group_name} (id={group_id})")

        try:
            html = get_schedule_html(group_id)
            schedule = parse_schedule(html)
            all_schedules[group_name] = schedule
            time.sleep(1.5)  # пауза, чтобы не заблокировали
        except Exception as e:
            print(f"⚠️ Ошибка при {group_name}: {e}")

    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(all_schedules, f, ensure_ascii=False, indent=2)
    print("✅ Все расписания сохранены в schedule.json")

if __name__ == "__main__":
    main()
