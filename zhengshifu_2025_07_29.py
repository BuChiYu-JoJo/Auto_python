import schedule
import subprocess
import time
import os
import base64
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ======= 配置项：控制哪些测试执行 =======
ENABLE_LOGIN_TEST = True
ENABLE_REGISTER_TEST = True
ENABLE_BUY_TEST = True
ENABLE_AMAZON_TEST = False

ENABLE_GOOGLE_TEST = False
ENABLE_WEBHOOK_TEST = False
ENABLE_SNOWFLAKE_TEST = False

def init_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless=new")     # 加上这个防止 GUI 崩溃
    options.add_argument("--disable-gpu")
    options.binary_location = "C:\\chrome\\chrome-win64\\chrome.exe"
    service = Service("C:\\chrome\\chromedriver-win64\\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
    return driver


import base64
from datetime import datetime
import os

def save_html_as_image(html_path, output_image_path, expand_passed=False):
    driver = init_driver()
    try:
        file_url = f"file://{os.path.abspath(html_path)}"
        driver.get(file_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "summary"))
        )
        time.sleep(1)

        # 自动判断集成测试类型（不展开）
        filename_lower = os.path.basename(html_path).lower()
        if any(key in filename_lower for key in ["amazon", "google", "httphook", "snowflake"]):
            expand_passed = False

        if expand_passed:
            try:
                show_all_btn = driver.find_element(By.ID, "show_all_details")
                driver.execute_script("arguments[0].click();", show_all_btn)
                print("✅ 点击 'Show all details' 展开成功")
                time.sleep(1.5)
            except Exception as e:
                print(f"⚠️ 展开失败: {e}")

        time.sleep(1)

        # 获取页面尺寸
        width = driver.execute_script("return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)")
        height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
        driver.set_window_size(width, height)
        time.sleep(1)

        # 构造按日期归类的目录结构
        date_folder = datetime.now().strftime("%Y%m%d")
        base_dir = "./report_images"
        full_dir = os.path.join(base_dir, date_folder)
        os.makedirs(full_dir, exist_ok=True)

        # 构造最终文件路径
        filename = os.path.basename(output_image_path)
        final_path = os.path.join(full_dir, filename)

        # 截图
        screenshot = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "format": "png",
            "fromSurface": True
        })

        with open(final_path, "wb") as f:
            f.write(base64.b64decode(screenshot["data"]))

        print(f"📷 已保存完整截图至：{final_path}（尺寸：{width}x{height}）")

    except Exception as e:
        print(f"❌ 截图失败: {e}")
    finally:
        driver.quit()




def screenshot_reports_only():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = "./reports/zhengshifu"
    image_dir = "./report_images"
    os.makedirs(image_dir, exist_ok=True)

    # 你要手动指定报告文件名（或自动寻找最新）
    login_report = max([f for f in os.listdir(reports_dir) if "login_test_report" in f], default=None)
    register_report = max([f for f in os.listdir(reports_dir) if "register_test_report" in f], default=None)
    buy_report = max([f for f in os.listdir(reports_dir) if "buy_test_report" in f], default=None)

#    if login_report:
#        save_html_as_image(f"{reports_dir}/{login_report}", f"{image_dir}/login_{timestamp}.png")
#    if register_report:
#        save_html_as_image(f"{reports_dir}/{register_report}", f"{image_dir}/register_{timestamp}.png", expand_passed=True)
    if buy_report:
        save_html_as_image(f"{reports_dir}/{buy_report}", f"{image_dir}/buy_{timestamp}.png", expand_passed=True)


def parse_pytest_html_report(report_path):
    with open(report_path, 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')

    # 摘要信息
    run_count_element = soup.find('p', class_='run-count')
    failed_tests_element = soup.find('span', class_='failed')
    passed_tests_element = soup.find('span', class_='passed')

    if not run_count_element or not failed_tests_element or not passed_tests_element:
        raise ValueError("Summary section not found in the report.")

    total_tests = int(run_count_element.text.split()[0])
    failed_tests = int(failed_tests_element.text.split()[0])
    passed_tests = int(passed_tests_element.text.split()[0])

    # 提取失败详情
    failure_details = []
    failed_rows = soup.select('tr.failed')

    for row in failed_rows:
        test_name = row.select_one('td.col-name').text.strip()
        error_msg = row.select_one('td.col-error').text.strip() if row.select_one('td.col-error') else 'No error message found'
        failure_details.append(f"**{test_name}**: {error_msg}")

    return {
        "total": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "failures": failure_details
    }


def send_to_dingtalk(webhook_url, message, test_name):
    headers = {'Content-Type': 'application/json'}

    failure_text = ""
    if message.get("failures"):
        failure_text = "\n\n**Failed Details:**\n" + "\n".join(f"- {line}" for line in message["failures"])

    markdown_text = (
        f"### Pytest Report Summary - {test_name}\n"
        f"- **Total Tests:** {message['total']}\n"
        f"- **Passed Tests:** {message['passed']}\n"
        f"- **Failed Tests:** {message['failed']}\n"
        f"{failure_text}"
    )

    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"Pytest Report Summary - {test_name}",
            "text": markdown_text
        }
    }

    proxies = {
        "http": None,
        "https": None,
    }

    try:
        response = requests.post(webhook_url, json=data, headers=headers, proxies=proxies)
        response.raise_for_status()
        print(f"Message sent to DingTalk successfully for {test_name}!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message for {test_name}: {e}")


# 定义运行pytest的函数
def run_pytest():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = "./reports/zhengshifu"
        image_dir = "./report_images"
        os.makedirs(reports_dir, exist_ok=True)
        os.makedirs(image_dir, exist_ok=True)

        # === 1. Login 测试 ===
        if ENABLE_LOGIN_TEST:
            login_report_file = f"{reports_dir}/login_test_report_{timestamp}.html"
            login_image_file = f"{image_dir}/login_test_report_{timestamp}.png"
            pytest_command_login = [
                "pytest", "pytest_login1.py::test_login_zs",
                f"--html={login_report_file}", "-v"
            ]
            result_login = subprocess.run(pytest_command_login, capture_output=True, text=True)
            print("Login Test Output:\n", result_login.stdout, result_login.stderr)
            if result_login.returncode != 0:
                print(f"⚠️ Login test failed with code {result_login.returncode}")
            try:
                summary_login = parse_pytest_html_report(login_report_file)
                send_to_dingtalk(webhook_url, summary_login, "Login Test")
                save_html_as_image(login_report_file, login_image_file)
            except Exception as e:
                print(f"❌ Failed to parse/send login report: {e}")

        # === 2. Register 测试 ===
        if ENABLE_REGISTER_TEST:
            register_report_file = f"{reports_dir}/register_test_report_{timestamp}.html"
            register_image_file = f"{image_dir}/register_test_report_{timestamp}.png"
            pytest_command_register = [
                "pytest", "pytest_register_new.py::test_register",
                f"--html={register_report_file}", "-v"
            ]
            result_register = subprocess.run(pytest_command_register, capture_output=True, text=True)
            print("Register Test Output:\n", result_register.stdout, result_register.stderr)
            if result_register.returncode != 0:
                print(f"⚠️ Register test failed with code {result_register.returncode}")
            try:
                summary_register = parse_pytest_html_report(register_report_file)
                send_to_dingtalk(webhook_url, summary_register, "Register Test")
                save_html_as_image(register_report_file, register_image_file, expand_passed=True)
            except Exception as e:
                print(f"❌ Failed to parse/send register report: {e}")

        # === 3. Buy 测试 ===
        if ENABLE_BUY_TEST:
            buy_report_file = f"{reports_dir}/buy_test_report_{timestamp}.html"
            buy_image_file = f"{image_dir}/buy_test_report_{timestamp}.png"
            pytest_command_buy = [
                "pytest", "py_buy_zs.py",
                f"--html={buy_report_file}", "-v"
            ]
            result_buy = subprocess.run(pytest_command_buy, capture_output=True, text=True)
            print("Buy Test Output:\n", result_buy.stdout, result_buy.stderr)
            if result_buy.returncode != 0:
                print(f"⚠️ Buy test failed with code {result_buy.returncode}")
            try:
                summary_buy = parse_pytest_html_report(buy_report_file)
                send_to_dingtalk(webhook_url, summary_buy, "Buy Test")
                save_html_as_image(buy_report_file, buy_image_file, expand_passed=True)
            except Exception as e:
                print(f"❌ Failed to parse/send buy report: {e}")


        # === 4. Amazon S3 集成测试 ===
        if ENABLE_AMAZON_TEST:
            amazon_report_file = f"{reports_dir}/amazon_test_report_{timestamp}.html"
            amazon_image_file = f"{image_dir}/amazon_test_report_{timestamp}.png"
            pytest_command_amazon = [
                "pytest", "scraper_amazons3.py",
                f"--html={amazon_report_file}", "-v"
            ]
            result_amazon = subprocess.run(pytest_command_amazon, capture_output=True, text=True)
            print("Amazon S3 Test Output:\n", result_amazon.stdout, result_amazon.stderr)
            if result_amazon.returncode != 0:
                print(f"⚠️ Amazon S3 test failed with code {result_amazon.returncode}")
            try:
                summary_amazon = parse_pytest_html_report(amazon_report_file)
                send_to_dingtalk(webhook_url, summary_amazon, "Amazon S3 Test")
                save_html_as_image(amazon_report_file, amazon_image_file, expand_passed=True)
            except Exception as e:
                print(f"❌ Failed to parse/send Amazon S3 report: {e}")


        # === 5. Google Gmail 集成测试 ===
        if ENABLE_GOOGLE_TEST:
            google_report_file = f"{reports_dir}/google_test_report_{timestamp}.html"
            google_image_file = f"{image_dir}/google_test_report_{timestamp}.png"
            pytest_command_google = [
                "pytest", "scraper_GoogleGmail.py",
                f"--html={google_report_file}", "-v"
            ]
            result_google = subprocess.run(pytest_command_google, capture_output=True, text=True)
            print("Google Gmail Test Output:\n", result_google.stdout, result_google.stderr)
            if result_google.returncode != 0:
                print(f"⚠️ Google Gmail test failed with code {result_google.returncode}")
            try:
                summary_google = parse_pytest_html_report(google_report_file)
                send_to_dingtalk(webhook_url, summary_google, "Google Gmail Test")
                save_html_as_image(google_report_file, google_image_file, expand_passed=True)
            except Exception as e:
                print(f"❌ Failed to parse/send Google Gmail report: {e}")


        # === 6. HTTP Webhook 集成测试 ===
        if ENABLE_WEBHOOK_TEST:
            webhook_report_file = f"{reports_dir}/httphook_test_report_{timestamp}.html"
            webhook_image_file = f"{image_dir}/httphook_test_report_{timestamp}.png"
            pytest_command_webhook = [
                "pytest", "scraper_httphook.py",
                f"--html={webhook_report_file}", "-v"
            ]
            result_webhook = subprocess.run(pytest_command_webhook, capture_output=True, text=True)
            print("HTTP Webhook Test Output:\n", result_webhook.stdout, result_webhook.stderr)
            if result_webhook.returncode != 0:
                print(f"⚠️ HTTP Webhook test failed with code {result_webhook.returncode}")
            try:
                summary_webhook = parse_pytest_html_report(webhook_report_file)
                send_to_dingtalk(webhook_url, summary_webhook, "HTTP Webhook Test")
                save_html_as_image(webhook_report_file, webhook_image_file, expand_passed=True)
            except Exception as e:
                print(f"❌ Failed to parse/send HTTP Webhook report: {e}")


        # === 7. Snowflake 集成测试 ===
        if ENABLE_SNOWFLAKE_TEST:
            snowflake_report_file = f"{reports_dir}/snowflake_test_report_{timestamp}.html"
            snowflake_image_file = f"{image_dir}/snowflake_test_report_{timestamp}.png"
            pytest_command_snow = [
                "pytest", "Scraper_Snowflake.py",
                f"--html={snowflake_report_file}", "-v"
            ]
            result_snow = subprocess.run(pytest_command_snow, capture_output=True, text=True)
            print("Snowflake Test Output:\n", result_snow.stdout, result_snow.stderr)
            if result_snow.returncode != 0:
                print(f"⚠️ Snowflake test failed with code {result_snow.returncode}")
            try:
                summary_snow = parse_pytest_html_report(snowflake_report_file)
                send_to_dingtalk(webhook_url, summary_snow, "Snowflake Test")
                save_html_as_image(snowflake_report_file, snowflake_image_file, expand_passed=True)
            except Exception as e:
                print(f"❌ Failed to parse/send Snowflake report: {e}")

    except Exception as e:
        print(f"💥 Unexpected error: {e}")


if __name__ == "__main__":
    webhook_url = 'https://oapi.dingtalk.com/robot/send?access_token=e05a6891a68b9b3b1cfacf8dcf5852bf647457439261362fac0a1e096951bfa9'  # Your DingTalk Webhook URL

    # 手动运行一次pytest以查看详细输出
    print("Manually running pytest for debugging...")
    run_pytest()
#    screenshot_reports_only()
    # 设置定时任务，每10分钟运行一次
#    schedule.every(10).minutes.do(run_pytest)

# 保持脚本运行，以检查定时任务并执行它
#    try:
#        while True:
#            schedule.run_pending()
#            time.sleep(1)  # 休眠1秒以减少CPU占用
#    except (KeyboardInterrupt, SystemExit):
#        print("Script interrupted or exited by user.")


