from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time, json

# Настройки
GROUP_NAME = "АСИ 25-1"
DEPARTMENT_NAME = "Очная"

driver = webdriver.Chrome()  # можно заменить на Firefox/Edge
driver.get("https://api.nntu.ru/raspisanie")

# 1️⃣ Ждём загрузки выпадающего списка формы обучения
time.sleep(3)

# Находим select с формой обучения
department_select = Select(driver.find_element(By.NAME, "department_id"))
department_select.select_by_visible_text(DEPARTMENT_NAME)

time.sleep(2)

# 2️⃣ Ждём загрузки списка групп
group_select = Select(driver.find_element(By.NAME, "group_id"))
group_select.select_by_visible_text(GROUP_NAME)

time.sleep(2)

# 3️⃣ Нажимаем кнопку "Показать"
driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()

# 4️⃣ Ждём подгрузку расписания
time.sleep(5)

# 5️⃣ Забираем HTML
html = driver.page_source

# 6️⃣ Можно тут же пропарсить через BeautifulSoup
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, "html.parser")

schedule = {}
for day_header in soup.find_all("h3"):
    day_name = day_header.get_text(strip=True)
    table = day_header.find_next("table")
    if not table:
        continue
    lessons = []
    for tr in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        lessons.append(cols)
    schedule[day_name] = lessons

# 7️⃣ Сохраняем в JSON
with open("schedule.json", "w", encoding="utf-8") as f:
    json.dump(schedule, f, ensure_ascii=False, indent=2)

print("✅ Расписание сохранено в schedule.json")
driver.quit()
