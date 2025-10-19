from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time, json

# === Настройки ===
GROUP_NAME = "АСИ 25-1"
DEPARTMENT_NAME = "Очная"
URL = "https://api.nntu.ru/raspisanie"

# Настраиваем браузер
options = Options()
options.add_argument("--headless")  # без GUI
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(URL)
time.sleep(3)

# Выбираем форму обучения
department_select = Select(driver.find_element(By.NAME, "department_id"))
department_select.select_by_visible_text(DEPARTMENT_NAME)
time.sleep(2)

# Выбираем группу
group_select = Select(driver.find_element(By.NAME, "group_id"))
group_select.select_by_visible_text(GROUP_NAME)
time.sleep(2)

# Нажимаем кнопку "Показать"
driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()
time.sleep(5)

# Парсим страницу
soup = BeautifulSoup(driver.page_source, "html.parser")
schedule = {}

for day_header in soup.find_all("h3"):
    day_name = day_header.get_text(strip=True)
    table = day_header.find_next("table")
    if not table:
        continue
    lessons = []
    for tr in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if cols:
            lessons.append(cols)
    schedule[day_name] = lessons

driver.quit()

# Сохраняем JSON
with open("schedule.json", "w", encoding="utf-8") as f:
    json.dump(schedule, f, ensure_ascii=False, indent=2)

print("✅ Расписание сохранено в schedule.json")
