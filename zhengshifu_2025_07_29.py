import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ENABLE_LOGIN_TEST = True
ENABLE_REGISTER_TEST = True
ENABLE_BUY_TEST = True

WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=e05a6891a68b9b3b1cfacf8dcf5852bf647457439261362fac0a1e096951bfa9"


@dataclass
class TestJob:
    name: str
    enabled: bool
    pytest_target: str
    report_key: str


def parse_pytest_html_report(report_path: Path) -> dict:
    content = report_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "html.parser")

    run_count_element = soup.find("p", class_="run-count")
    failed_tests_element = soup.find("span", class_="failed")
    passed_tests_element = soup.find("span", class_="passed")

    if not run_count_element or not failed_tests_element or not passed_tests_element:
        raise ValueError("Summary section not found in the report.")

    total_tests = int(run_count_element.text.split()[0])
    failed_tests = int(failed_tests_element.text.split()[0])
    passed_tests = int(passed_tests_element.text.split()[0])

    failure_details = []
    for row in soup.select("tr.failed"):
        test_name = row.select_one("td.col-name").text.strip()
        err_node = row.select_one("td.col-error")
        error_msg = err_node.text.strip() if err_node else "No error message found"
        failure_details.append(f"**{test_name}**: {error_msg}")

    return {
        "total": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "failures": failure_details,
    }


def send_to_dingtalk(webhook_url: str, message: dict, test_name: str) -> None:
    headers = {"Content-Type": "application/json"}

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
            "text": markdown_text,
        },
    }

    requests.post(webhook_url, json=data, headers=headers, timeout=20).raise_for_status()
    print(f"✅ DingTalk 推送成功：{test_name}")


def save_html_as_image(html_path: Path, output_image_path: Path) -> None:
    html_uri = html_path.resolve().as_uri()
    output_image_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_uri, wait_until="domcontentloaded")
        page.wait_for_selector(".summary", timeout=10000)
        page.screenshot(path=str(output_image_path), full_page=True)
        browser.close()

    print(f"📷 报告截图已保存：{output_image_path}")


def run_pytest() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = Path("./reports/zhengshifu")
    images_dir = Path("./report_images") / datetime.now().strftime("%Y%m%d")
    reports_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    jobs = [
        TestJob("Login Test", ENABLE_LOGIN_TEST, "pytest_login1.py::test_login_zs", "login"),
        TestJob("Register Test", ENABLE_REGISTER_TEST, "pytest_register_new.py::test_register", "register"),
        TestJob("Buy Test", ENABLE_BUY_TEST, "py_buy_zs.py::test_login_and_buy", "buy"),
    ]

    for job in jobs:
        if not job.enabled:
            continue

        report_file = reports_dir / f"{job.report_key}_test_report_{timestamp}.html"
        image_file = images_dir / f"{job.report_key}_test_report_{timestamp}.png"

        cmd = ["pytest", job.pytest_target, f"--html={report_file}", "--self-contained-html", "-v"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        print(f"\n{'=' * 80}")
        print(f"{job.name} OUTPUT")
        print(f"{'=' * 80}")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if result.returncode != 0:
            print(f"⚠️ {job.name} exited with code {result.returncode}")

        try:
            summary = parse_pytest_html_report(report_file)
            send_to_dingtalk(WEBHOOK_URL, summary, job.name)
            save_html_as_image(report_file, image_file)
        except Exception as e:
            print(f"❌ 报告解析/推送失败 ({job.name}): {e}")


if __name__ == "__main__":
    run_pytest()
