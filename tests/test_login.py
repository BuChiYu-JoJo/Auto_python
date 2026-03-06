"""
登录功能测试用例 - 反检测版本
支持自动处理验证码（需要手动时暂停等待）
"""

import os
import sys
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.login_page import LoginPage


class TestResult:
    """测试结果类"""
    
    def __init__(self):
        self.name = "Thordata 登录测试"
        self.status = "PASSED"
        self.start_time = ""
        self.end_time = ""
        self.duration = 0
        self.error_message = ""
        self.screenshot_path = ""


# 随机 User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def random_delay(min_sec=0.3, max_sec=1.5):
    """模拟人类延迟"""
    time.sleep(random.uniform(min_sec, max_sec))


def run_test() -> TestResult:
    """运行登录测试"""
    result = TestResult()
    result.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 随机选择配置
    user_agent = random.choice(USER_AGENTS)
    
    with sync_playwright() as p:
        # 启动浏览器（反检测模式 - headless）
        browser = p.chromium.launch(
            headless=True,  # 服务器无GUI，使用headless
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--start-maximized',
            ]
        )
        
        # 创建上下文
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=user_agent,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )
        
        # 注入脚本来隐藏自动化特征
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)
        
        page = context.new_page()
        
        # 测试配置
        base_url = "https://dashboard.thordata.com/zh/login"
        username = "lightsong@thordata.com"
        password = "Zxs6412915@+"
        
        try:
            print("=" * 60)
            print("开始执行登录测试（反检测模式）...")
            print("=" * 60)
            
            # 步骤1: 导航到登录页
            print("\n[步骤1] 导航到登录页...")
            page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
            print(f"  ✅ 页面标题: {page.title()}")
            print(f"  ✅ URL: {page.url}")
            
            # 截图
            page.screenshot(path="/home/test/ai-test/reports/screenshots/login_page.png", full_page=True)
            print("  ✅ 截图: screenshots/login_page.png")
            
            # 步骤2: 输入用户名
            print("\n[步骤2] 输入用户名...")
            page.fill('#email', username)
            random_delay(0.5, 1.5)
            print(f"  ✅ 已输入: {username}")
            
            # 步骤3: 输入密码
            print("\n[步骤3] 输入密码...")
            page.fill('#psw', password)
            random_delay(0.5, 1.5)
            print("  ✅ 已输入密码")
            
            # 步骤4: 点击登录按钮
            print("\n[步骤4] 点击登录...")
            try:
                # 尝试多种选择器
                page.click('button[type="submit"]', timeout=3000)
            except:
                try:
                    page.click('div:has-text("登录")', timeout=3000)
                except:
                    page.keyboard.press('Enter')
            
            random_delay(1, 2)
            
            # 步骤5: 等待登录结果（包含验证码检测）
            print("\n[步骤5] 等待登录结果...")
            
            # 等待一段时间让验证码出现
            page.wait_for_timeout(8000)
            
            # 检查页面内容
            page_content = page.content()
            
            # 检查是否有验证码
            if 'geetest' in page_content.lower() or 'captcha' in page_content.lower():
                print("  ⚠️ 检测到验证码!")
                print("  💡 请在弹出的浏览器窗口中手动完成验证")
                print("  ⏳ 等待 60 秒...")
                
                # 等待用户手动完成验证
                page.wait_for_timeout(60000)
            
            # 再次检查登录结果
            page.wait_for_timeout(3000)
            
            # 截图
            page.screenshot(path="/home/test/ai-test/reports/screenshots/login_result.png", full_page=True)
            print("  ✅ 截图: screenshots/login_result.png")
            
            # 步骤6: 检查登录结果
            print("\n[步骤6] 检查登录结果...")
            final_url = page.url
            print(f"  📍 最终URL: {final_url}")
            
            # 判断登录是否成功
            if "login" not in final_url.lower():
                result.status = "PASSED"
                print("  ✅ 登录成功!")
                
                # 导出登录后的cookies供后续使用
                cookies = context.cookies()
                print(f"  📦 获取到 {len(cookies)} 个 Cookie")
                
                # 保存 cookies
                import json
                with open('/home/test/ai-test/config/cookies_logged_in.json', 'w') as f:
                    json.dump(cookies, f, indent=2)
                print("  💾 Cookie 已保存到 config/cookies_logged_in.json")
                
            else:
                result.status = "FAILED"
                result.error_message = "登录失败，可能需要手动验证"
                print(f"  ❌ 登录失败")
                
                # 保存截图用于调试
                page.screenshot(path="/home/test/ai-test/reports/screenshots/login_failed.png", full_page=True)
            
            result.screenshot_path = "/home/test/ai-test/reports/screenshots/login_result.png"
            
        except Exception as e:
            print(f"\n❌ 测试执行出错: {str(e)}")
            result.status = "ERROR"
            result.error_message = str(e)
            page.screenshot(path="/home/test/ai-test/reports/screenshots/login_error.png", full_page=True)
        
        finally:
            # 保持浏览器打开，让用户可以看到结果
            print("\n[浏览器保持打开中，按回车继续...]")
            # page.wait_for_timeout(10000)  # 可选：等待一段时间
            
            context.close()
            browser.close()
    
    result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start = datetime.strptime(result.start_time, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(result.end_time, "%Y-%m-%d %H:%M:%S")
    result.duration = (end - start).total_seconds()
    
    return result


def generate_html_report(result: TestResult):
    """生成 HTML 测试报告"""
    import os
    
    report_dir = "/home/test/ai-test/reports"
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"{report_dir}/test_report_{timestamp}.html"
    
    status_color = {
        "PASSED": "#22c55e",
        "FAILED": "#ef4444",
        "ERROR": "#f97316"
    }
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>测试报告 - {result.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            .status {{ 
                display: inline-block; 
                padding: 8px 16px; 
                border-radius: 4px; 
                color: white;
                font-weight: bold;
            }}
            .info {{ margin: 20px 0; }}
            .info p {{ margin: 8px 0; }}
            img {{ max-width: 100%; border: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <h1>{result.name}</h1>
        <div class="status" style="background: {status_color.get(result.status, '#666')}">
            {result.status}
        </div>
        
        <div class="info">
            <p><strong>开始时间:</strong> {result.start_time}</p>
            <p><strong>结束时间:</strong> {result.end_time}</p>
            <p><strong>耗时:</strong> {result.duration:.2f} 秒</p>
            {f'<p><strong>错误信息:</strong> {result.error_message}</p>' if result.error_message else ''}
        </div>
        
        {f'<h2>截图</h2><img src="screenshots/login_result.png" />' if result.screenshot_path else ''}
    </body>
    </html>
    """
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return report_path


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Thordata 登录测试")
    print("=" * 60 + "\n")
    
    result = run_test()
    
    print("\n" + "=" * 60)
    print("测试执行完成!")
    print("=" * 60)
    print(f"测试名称: {result.name}")
    print(f"测试状态: {result.status}")
    print(f"测试耗时: {result.duration:.2f}秒")
    
    # 生成报告
    report_path = generate_html_report(result)
    print(f"报告路径: {report_path}")
    
    return result


if __name__ == "__main__":
    main()
