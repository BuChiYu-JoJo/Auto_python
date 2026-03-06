"""
Thordata 登录 - 反检测版本
"""

import os
import sys
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.login_page import LoginPage


# 随机 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# 随机视口尺寸
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
]


def random_delay(min_sec=0.5, max_sec=2.0):
    """随机延迟，模拟人类思考时间"""
    time.sleep(random.uniform(min_sec, max_sec))


def simulate_human_movement(page):
    """模拟人类鼠标移动"""
    for _ in range(3):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.1, 0.3))


def wait_for_geetest_or_login(page, timeout=30000):
    """等待验证码或登录结果"""
    print("  ⏳ 等待页面加载...")
    
    # 等待可能的验证码
    try:
        # 等待最多 30 秒让验证码加载
        page.wait_for_timeout(5000)
        
        # 检查是否有验证码
        page_html = page.content().lower()
        
        if 'geetest' in page_html or 'captcha' in page_html or '验证' in page_html:
            print("  ⚠️ 检测到验证码，请手动处理...")
            print("  💡 请在浏览器中手动完成验证")
            # 等待用户手动完成验证
            page.wait_for_timeout(timeout)
        
        # 检查是否登录成功
        if "login" not in page.url.lower():
            return True
            
    except Exception as e:
        print(f"  ⚠️ 等待异常: {e}")
    
    return "login" not in page.url


def login_with_bypass():
    """带反检测的登录"""
    print("=" * 60)
    print("Thordata 反检测登录测试")
    print("=" * 60)
    
    with sync_playwright() as p:
        # 随机选择配置
        user_agent = random.choice(USER_AGENTS)
        viewport = random.choice(VIEWPORTS)
        
        print(f"\n[配置] User-Agent: {user_agent[:50]}...")
        print(f"[配置] Viewport: {viewport['width']}x{viewport['height']}")
        
        # 启动浏览器（带反检测参数）
        browser = p.chromium.launch(
            headless=False,  # 非headless更容易通过检测
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--allow-running-insecure-content',
                '--disable-web-security',
                '--disable-extensions',
                '--disable-plugins',
                '--window-size=1920,1080',
            ]
        )
        
        # 创建上下文
        context = browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            permissions=['geolocation', 'notifications'],
            ignore_https_errors=True,
        )
        
        # 添加 JavaScript 来隐藏 webdriver
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            window.chrome = {
                runtime: {}
            };
        """)
        
        page = context.new_page()
        
        # 访问登录页
        print("\n[步骤1] 访问登录页...")
        page.goto("https://dashboard.thordata.com/zh/login", wait_until="domcontentloaded")
        random_delay(2, 4)
        
        # 模拟人类浏览行为
        print("\n[步骤2] 模拟人类浏览...")
        page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        random_delay(1, 2)
        
        # 输入用户名
        print("\n[步骤3] 输入用户名...")
        page.fill('#email', 'lightsong@thordata.com')
        random_delay(0.5, 1.5)
        
        # 输入密码
        print("\n[步骤4] 输入密码...")
        page.fill('#psw', 'Zxs6412915@+')
        random_delay(0.5, 1.5)
        
        # 模拟鼠标移动
        simulate_human_movement(page)
        
        # 点击登录
        print("\n[步骤5] 点击登录...")
        
        # 尝试多种点击方式
        try:
            page.click('button[type="submit"]', timeout=5000)
        except:
            try:
                page.click('div:has-text("登录")', timeout=5000)
            except:
                page.keyboard.press('Enter')
        
        # 等待登录结果
        print("\n[步骤6] 等待登录结果...")
        random_delay(3, 6)
        
        # 检查结果
        print(f"\n[结果] URL: {page.url}")
        print(f"[结果] 标题: {page.title()}")
        
        # 截图
        page.screenshot(path="/home/test/ai-test/reports/screenshots/login_attempt.png", full_page=True)
        
        if "login" not in page.url.lower():
            print("\n✅ 登录成功!")
            # 导出登录后的 cookies
            cookies = context.cookies()
            print(f"获取到 {len(cookies)} 个 Cookie")
            return True
        else:
            print("\n❌ 登录失败")
            # 检查是否有验证码
            content = page.content()
            if 'geetest' in content.lower() or '验证' in content:
                print("  → 被验证码拦截")
            return False


if __name__ == "__main__":
    success = login_with_bypass()
    print(f"\n最终结果: {'成功' if success else '失败'}")
