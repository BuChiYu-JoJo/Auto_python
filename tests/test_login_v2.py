#!/usr/bin/env python3
"""
Thordata 登录测试 - 优化版
- 参数化配置
- 使用代理防风控
- 失败自动截图
- 登录成功自动保存Cookie
"""

import os
import sys
import time
import random
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==================== 配置区 ====================
CONFIG = {
    # 代理配置（解决风控问题）
    "proxy": {
        "server": "http://rmmsg2sa.pr.thordata.net:9999",
        "username": "td-customer-MzsNH4f",
        "password": "EtXApbeko8bDT"
    },
    
    # 测试账号
    "account": {
        "email": "lightsong@thordata.com",
        "password": "Zxs6412915@+"
    },
    
    # 登录URL
    "login_url": "https://dashboard.thordata.com/zh/login",
    
    # 反检测配置
    "stealth": {
        "use_random_ua": True,
        "random_delay": True,
    },
    
    # 截图目录
    "screenshot_dir": "/home/test/ai-test/screenshots",
    
    # Cookie保存路径
    "cookie_path": "/home/test/ai-test/config/cookies_login.json"
}


# 随机 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


class LoginTestResult:
    def __init__(self):
        self.name = "Thordata 登录测试"
        self.start_time = datetime.now()
        self.end_time = None
        self.status = "FAILED"
        self.error_message = ""
        self.screenshots = []
        self.cookies = None


def random_delay(min_sec=0.3, max_sec=1.5):
    """模拟人类延迟"""
    if CONFIG["stealth"]["random_delay"]:
        time.sleep(random.uniform(min_sec, max_sec))


def take_screenshot(page, name, step_desc):
    """截图并记录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{CONFIG['screenshot_dir']}/{name}_{timestamp}.png"
    try:
        page.screenshot(path=filename, full_page=True)
        print(f"  📸 截图: {filename}")
        return filename
    except Exception as e:
        print(f"  ⚠️ 截图失败: {e}")
        return None


def run_login_test(config=None):
    """运行登录测试"""
    if config:
        CONFIG.update(config)
    
    result = LoginTestResult()
    
    # 随机选择 User-Agent
    user_agent = random.choice(USER_AGENTS) if CONFIG["stealth"]["use_random_ua"] else USER_AGENTS[0]
    
    with sync_playwright() as p:
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
            user_agent=user_agent,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )
        
        # 反检测脚本
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)
        
        page = context.new_page()
        
        try:
            print("=" * 60)
            print("Thordata 登录测试 (优化版)")
            print("=" * 60)
            print(f"账号: {CONFIG['account']['email']}")
            print(f"代理: {CONFIG['proxy']['server']}")
            print("=" * 60)
            
            # ===== 步骤1: 导航到登录页 =====
            print("\n[步骤1] 导航到登录页...")
            page.goto(CONFIG["login_url"], wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000)
            
            print(f"  ✅ 页面标题: {page.title()}")
            print(f"  ✅ URL: {page.url}")
            
            take_screenshot(page, "login_page", "登录页")
            
            # ===== 步骤2: 输入用户名 =====
            print("\n[步骤2] 输入用户名...")
            
            # 尝试多种输入方式
            try:
                page.fill('#email', CONFIG["account"]["email"])
            except:
                page.fill('input[placeholder="电子邮件地址"]', CONFIG["account"]["email"])
            
            random_delay(0.5, 1.5)
            print(f"  ✅ 已输入: {CONFIG['account']['email']}")
            
            # ===== 步骤3: 输入密码 =====
            print("\n[步骤3] 输入密码...")
            try:
                page.fill('#psw', CONFIG["account"]["password"])
            except:
                page.fill('input[placeholder="密码"]', CONFIG["account"]["password"])
            
            random_delay(0.5, 1.5)
            print("  ✅ 已输入密码")
            
            # ===== 步骤4: 点击登录 =====
            print("\n[步骤4] 点击登录...")
            try:
                page.click('button[type="submit"]', timeout=3000)
            except:
                try:
                    page.click('button:has-text("登录")', timeout=3000)
                except:
                    page.keyboard.press('Enter')
            
            page.wait_for_timeout(10000)
            
            # ===== 步骤5: 检查验证码/登录结果 =====
            print("\n[步骤5] 检查登录结果...")
            
            page_content = page.content()
            
            # 检查是否有验证码
            if 'geetest' in page_content.lower() or 'captcha' in page_content.lower() or 'turnstile' in page_content.lower():
                print("  ⚠️ 检测到验证码!")
                take_screenshot(page, "captcha", "验证码页面")
                
                # 等待用户手动完成
                print("  💡 请在浏览器中手动完成验证...")
                print("  ⏳ 等待 60 秒...")
                page.wait_for_timeout(60000)
                
                # 验证码后再次等待
                page.wait_for_timeout(5000)
            
            # ===== 步骤6: 验证登录结果 =====
            print("\n[步骤6] 验证登录结果...")
            final_url = page.url
            print(f"  📍 最终URL: {final_url}")
            
            if "login" not in final_url.lower():
                result.status = "PASSED"
                print("  ✅ 登录成功!")
                
                # 保存 Cookie
                result.cookies = context.cookies()
                with open(CONFIG["cookie_path"], 'w') as f:
                    json.dump([{
                        "name": c["name"],
                        "value": c["value"],
                        "domain": c["domain"],
                        "path": c["path"]
                    } for c in result.cookies], f, indent=2)
                
                print(f"  💾 Cookie已保存: {CONFIG['cookie_path']}")
                
                take_screenshot(page, "login_success", "登录成功")
                result.screenshots.append(CONFIG["screenshot_dir"] + f"/login_success_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                
            else:
                result.status = "FAILED"
                result.error_message = "登录失败"
                print("  ❌ 登录失败")
                take_screenshot(page, "login_failed", "登录失败")
            
        except Exception as e:
            print(f"\n❌ 登录异常: {e}")
            result.status = "ERROR"
            result.error_message = str(e)
            take_screenshot(page, "login_error", "登录异常")
        
        finally:
            browser.close()
    
    result.end_time = datetime.now()
    return result


def generate_report(result: LoginTestResult):
    """生成HTML报告"""
    duration = (result.end_time - result.start_time).total_seconds()
    timestamp = result.start_time.strftime("%Y%m%d_%H%M%S")
    
    status_class = "pass" if result.status == "PASSED" else "fail"
    status_text = "✅ 成功" if result.status == "PASSED" else "❌ 失败"
    
    report_path = f"/home/test/ai-test/reports/login_test_report_{timestamp}.html"
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录测试报告</title>
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
        .error {{ background: #fff3cd; padding: 15px; border-radius: 8px; color: #856404; margin-top: 20px; }}
        .footer {{ background: #f8f9fa; padding: 15px 40px; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 登录测试报告</h1>
            <div class="meta">测试时间: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')} | 耗时: {duration:.1f}秒</div>
        </div>
        <div class="content">
            <div class="status-box {status_class}">
                <div class="status">{status_text}</div>
            </div>
            <div class="info">
                <p><strong>测试账号:</strong> {CONFIG['account']['email']}</p>
                <p><strong>登录URL:</strong> {CONFIG['login_url']}</p>
                <p><strong>代理:</strong> {CONFIG['proxy']['server']}</p>
            </div>
            {"<div class='error'><strong>错误信息:</strong> " + result.error_message + "</div>" if result.error_message else ""}
        </div>
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
    print("Thordata 登录测试 (优化版)")
    print("=" * 60 + "\n")
    
    result = run_login_test()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print(f"状态: {result.status}")
    if result.error_message:
        print(f"错误: {result.error_message}")
    
    # 生成报告
    report_path = generate_report(result)
    print(f"\n📊 报告: {report_path}")
    
    return result


if __name__ == "__main__":
    main()
