#!/usr/bin/env python3
"""
Thordata 注册测试 - 优化版
- 代理自动重试（每次重试换IP）
- 参数化配置
- 失败自动截图
- 自动生成报告
"""

import os
import sys
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==================== 配置区 ====================
CONFIG = {
    # 代理配置
    "proxy": {
        "server": "http://rmmsg2sa.pr.thordata.net:9999",
        "username": "td-customer-MzsNH4f",
        "password": "EtXApbeko8bDT"
    },

    # 注册账号
    "account": {
        "email": "test{random}@thordata.com",
        "password": "Zxs6412915@+"
    },

    # 注册URL
    "register_url": "https://dashboard.thordata.com/zh/register",

    # 重试配置
    "retry": {
        "max_attempts": 3,  # 最大重试次数
        "wait_between": 10   # 重试间隔秒数
    },

    # 截图目录
    "screenshot_dir": "/home/test/ai-test/screenshots",

    # 报告目录
    "report_dir": "/home/test/ai-test/reports"
}


class RegisterTestResult:
    def __init__(self):
        self.name = "Thordata 注册测试"
        self.start_time = datetime.now()
        self.end_time = None
        self.status = "FAILED"
        self.email = ""
        self.activation_hint = False
        self.activation_message = ""
        self.error_message = ""
        self.attempts = 0
        self.screenshots = []


def random_delay(min_sec=0.3, max_sec=1.0):
    time.sleep(random.uniform(min_sec, max_sec))


def take_screenshot(page, name, step_desc):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{CONFIG['screenshot_dir']}/{name}_{timestamp}.png"
    try:
        page.screenshot(path=filename, full_page=True)
        print(f"  📸 截图: {filename}")
        return filename
    except Exception as e:
        print(f"  ⚠️ 截图失败: {e}")
        return None


def run_registerAttempt(attempt_num):
    """执行一次注册尝试"""
    print(f"\n{'='*50}")
    print(f"第 {attempt_num} 次尝试")
    print(f"{'='*50}")

    result = RegisterTestResult()
    result.attempts = attempt_num
    result.email = CONFIG["account"]["email"].format(random=random.randint(10000, 99999))

    with sync_playwright() as p:
        # 每次都重新启动浏览器获取新IP
        browser = p.chromium.launch(
            headless=False,
            proxy=CONFIG["proxy"],
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--window-size=1920,1080',
            ]
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()

        try:
            print(f"测试邮箱: {result.email}")

            # ===== 步骤1: 访问注册页 =====
            print("\n[步骤1] 访问注册页面...")
            page.goto(CONFIG["register_url"], wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000)
            print(f"  ✅ 页面标题: {page.title()}")
            take_screenshot(page, f"attempt{attempt_num}_page", "注册页")

            # ===== 步骤2: 填写信息 =====
            print("\n[步骤2] 填写注册信息...")
            try:
                page.fill('input[type="email"], input[name="email"], input[placeholder*="邮箱"]', result.email)
            except:
                page.fill('input[type="text"]', result.email)
            random_delay(0.3, 0.8)

            try:
                page.fill('input[type="password"]', CONFIG["account"]["password"])
            except:
                pass
            random_delay(0.3, 0.8)

            take_screenshot(page, f"attempt{attempt_num}_filled", "填写完成")

            # ===== 步骤3: 勾选协议 =====
            print("\n[步骤3] 勾选协议...")
            try:
                page.check('input[type="checkbox"]')
            except:
                pass
            
            # 等待注册按钮出现
            page.wait_for_selector('.login-container-body-E-btn', timeout=10000)
            
            # ===== 步骤4: 点击注册 =====
            print("\n[步骤4] 点击注册...")
            # 使用 JavaScript 点击 DIV 按钮
            page.evaluate("() => { document.querySelector('.login-container-body-E-btn').click(); }")
            page.wait_for_timeout(3000)

            page.wait_for_timeout(10000)

            # ===== 检查验证码 =====
            page_text = page.inner_text('body')
            page_content = page.content()

            if '验证' in page_text or '人机' in page_text or 'turnstile' in page_content:
                print("  ⚠️ 遇到验证码!")
                take_screenshot(page, f"attempt{attempt_num}_captcha", "验证码")

                # 尝试点击验证
                try:
                    page.click('text=人机验证', timeout=3000)
                    print("  👆 点击验证按钮")
                    page.wait_for_timeout(5000)
                except:
                    pass

                # 等待验证
                print("  ⏳ 等待验证完成...")
                page.wait_for_timeout(15000)

            take_screenshot(page, f"attempt{attempt_num}_submit", "提交后")

            # ===== 检查结果 =====
            print("\n[步骤4] 检查结果...")
            page_text = page.inner_text('body')

            activation_keywords = ['验证', '激活', '确认', '24小时', '已向']
            result.activation_hint = any(kw in page_text for kw in activation_keywords)

            error_keywords = ['错误', '失败', '已存在', 'invalid', 'error', '请完成']
            has_error = any(kw in page_text.lower() for kw in error_keywords)

            if result.activation_hint:
                result.status = "PASSED"
                print("  ✅ 注册成功 - 需要邮箱验证!")
                if '已向' in page_text:
                    idx = page_text.find('已向')
                    result.activation_message = page_text[idx:idx+80]
                    print(f"  📧 {result.activation_message}")
                take_screenshot(page, f"attempt{attempt_num}_success", "成功")
            elif has_error:
                result.status = "FAILED"
                result.error_message = "注册返回错误"
                print("  ❌ 注册失败")
                take_screenshot(page, f"attempt{attempt_num}_failed", "失败")
            else:
                result.status = "BLOCKED"
                result.error_message = "无法确定结果"
                print("  ⚠️ 结果未知")
                take_screenshot(page, f"attempt{attempt_num}_unknown", "未知")

        except Exception as e:
            print(f"\n❌ 异常: {e}")
            result.status = "ERROR"
            result.error_message = str(e)
            take_screenshot(page, f"attempt{attempt_num}_error", "异常")

        finally:
            browser.close()

    return result


def run_register_test():
    """运行注册测试（带重试）"""
    max_attempts = CONFIG["retry"]["max_attempts"]
    wait_time = CONFIG["retry"]["wait_between"]

    for attempt in range(1, max_attempts + 1):
        result = run_registerAttempt(attempt)

        if result.status == "PASSED":
            return result

        if attempt < max_attempts:
            print(f"\n⚠️ 第 {attempt} 次尝试未通过，等待 {wait_time} 秒后重试...")
            print("   (代理会分配新IP)")
            time.sleep(wait_time)

    return result


def generate_report(result: RegisterTestResult):
    duration = (result.end_time - result.start_time).total_seconds()
    timestamp = result.start_time.strftime("%Y%m%d_%H%M%S")

    status_class = "pass" if result.status == "PASSED" else "fail"
    status_text = "✅ 成功" if result.status == "PASSED" else "❌ 失败"

    report_path = f"{CONFIG['report_dir']}/register_test_report_{timestamp}.html"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>注册测试报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; padding: 40px 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px 40px; color: white; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .content {{ padding: 30px 40px; }}
        .status-box {{ padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px; }}
        .status-box.pass {{ background: #d4edda; }}
        .status-box.fail {{ background: #f8d7da; }}
        .status-box .status {{ font-size: 24px; font-weight: bold; }}
        .status-box.pass .status {{ color: #155724; }}
        .status-box.fail .status {{ color: #721c24; }}
        .info {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .info p {{ margin: 8px 0; color: #666; }}
        .attempts {{ background: #e7f3ff; padding: 15px; border-radius: 8px; color: #0066cc; margin-bottom: 20px; }}
        .activation {{ background: #d1ecf1; padding: 15px; border-radius: 8px; color: #0c5460; margin-top: 20px; }}
        .error {{ background: #fff3cd; padding: 15px; border-radius: 8px; color: #856404; margin-top: 20px; }}
        .footer {{ background: #f8f9fa; padding: 15px 40px; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 注册测试报告</h1>
            <div class="meta">测试时间: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')} | 耗时: {duration:.1f}秒</div>
        </div>
        <div class="content">
            <div class="status-box {status_class}">
                <div class="status">{status_text}</div>
            </div>
            <div class="attempts">
                <strong>尝试次数:</strong> {result.attempts} / {CONFIG['retry']['max_attempts']}<br>
                <small>每次尝试会使用新的代理IP</small>
            </div>
            <div class="info">
                <p><strong>测试邮箱:</strong> {result.email}</p>
                <p><strong>注册URL:</strong> {CONFIG['register_url']}</p>
                <p><strong>代理:</strong> {CONFIG['proxy']['server']}</p>
            </div>
"""

    if result.activation_hint and result.activation_message:
        html += f'            <div class="activation"><strong>📧 邮箱验证提示:</strong><br>{result.activation_message}</div>\n'

    if result.error_message:
        html += f'            <div class="error"><strong>错误信息:</strong> {result.error_message}</div>\n'

    html += f"""        </div>
        <div class="footer">
            Agent: OpenClaw Automation | {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return report_path


def main():
    print("\n" + "=" * 60)
    print("Thordata 注册测试 (代理重试版)")
    print("=" * 60)
    print(f"最大尝试次数: {CONFIG['retry']['max_attempts']}")
    print(f"重试间隔: {CONFIG['retry']['wait_between']}秒")
    print("=" * 60 + "\n")

    result = run_register_test()
    result.end_time = datetime.now()

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print(f"状态: {result.status}")
    print(f"尝试次数: {result.attempts}")
    print(f"邮箱: {result.email}")
    if result.activation_message:
        print(f"提示: {result.activation_message[:50]}...")

    report_path = generate_report(result)
    print(f"\n📊 报告: {report_path}")

    return result


if __name__ == "__main__":
    main()
