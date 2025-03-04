from flask import Flask, request, render_template_string, jsonify, Response
import time
import json
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

html_template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Singles成績Jsonパーサー</title>
</head>
<body>
<h1>Singles成績Jsonパーサー</h1>
<form method="post" action="/scrape">
  ユーザーID: <input type="text" name="user" required><br>
  パスワード: <input type="password" name="pass" required><br>
  <input type="submit" value="スクレイピング実行">
</form>
</body>
</html>
"""

def scrape_grades(user, pwd):
    options = Options()
    options.add_argument('--headless')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-data-dir=/tmp/chrome-user-data")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    service = ChromeDriverManager().install()
    driver = webdriver.Chrome(service=ChromeService(service), options=options)
    driver.set_window_size(1280, 800)
    try:
        driver.get("https://twins.tsukuba.ac.jp/campusweb/campusportal.do")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "wf_PTW0000011_20120827233559-form")))
        time.sleep(1)
        driver.find_element(By.NAME, "userName").clear()
        driver.find_element(By.NAME, "userName").send_keys(user)
        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "password").send_keys(pwd)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        WebDriverWait(driver, 15).until(EC.title_contains("CampusSquare for WEB"))
        time.sleep(2)
        driver.get("https://twins.tsukuba.ac.jp/campusweb/campussquare.do?_flowId=SIW0001200-flow")
        WebDriverWait(driver, 15).until(lambda d: "_flowExecutionKey=" in d.current_url)
        redirected_url = driver.current_url
        parsed = urllib.parse.urlparse(redirected_url)
        qs = urllib.parse.parse_qs(parsed.query)
        flow_key = qs.get('_flowExecutionKey', [None])[0]
        if not flow_key:
            driver.quit()
            return None
        new_url = f"https://twins.tsukuba.ac.jp/campusweb/campussquare.do?_flowExecutionKey={flow_key}"
        driver.get(new_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        all_rows = []
        while True:
            time.sleep(2)
            page_html = driver.page_source
            soup = BeautifulSoup(page_html, "html.parser")
            tables = soup.find_all("table", class_="normal")
            target_table = None
            for table in tables:
                header = table.find("tr")
                if header and "No." in header.get_text():
                    target_table = table
                    break
            if target_table:
                headers = [th.get_text(strip=True) for th in target_table.find_all("th")]
                rows = target_table.find_all("tr")[1:]
                for row in rows:
                    cols = [col.get_text(strip=True) for col in row.find_all("td")]
                    if cols:
                        row_dict = dict(zip(headers, cols))
                        all_rows.append(row_dict)
            try:
                next_link = driver.find_element(By.XPATH, '//a[contains(text(), "次へ")]')
                next_href = next_link.get_attribute("href")
                if next_href:
                    driver.get(next_href)
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    time.sleep(2)
                else:
                    break
            except Exception:
                break
        driver.quit()
        return all_rows
    except Exception:
        driver.quit()
        return None

@app.route("/", methods=["GET"])
def index():
    return render_template_string(html_template)

@app.route("/scrape", methods=["POST"])
def scrape_endpoint():
    user = request.form.get("user") or (request.json and request.json.get("user"))
    pwd = request.form.get("pass") or (request.json and request.json.get("pass"))
    if not user or not pwd:
        return jsonify({"error": "認証情報が不足しています"}), 400
    data = scrape_grades(user, pwd)
    if data is None:
        return jsonify({"error": "スクレイピングに失敗しました"}), 500
    if request.form:
        resp = Response(json.dumps(data, ensure_ascii=False, indent=2), mimetype="application/json")
        resp.headers["Content-Disposition"] = "attachment; filename=grades_data.json"
        return resp
    else:
        return jsonify(data)

@app.route("/grades", methods=["POST"])
def grades_api():
    content = request.get_json()
    if not content:
        return jsonify({"error": "JSON body is required"}), 400
    user = content.get("user")
    pwd = content.get("pass")
    if not user or not pwd:
        return jsonify({"error": "認証情報が不足しています"}), 400
    data = scrape_grades(user, pwd)
    if data is None:
        return jsonify({"error": "スクレイピングに失敗しました"}), 500
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)