"""
Thordata 登录模块 - 通过 API 获取 Token
"""

import requests
from playwright.sync_api import sync_playwright

# 登录 API
LOGIN_API = "https://dashboard.thordata.com/api/v1/user/login"

def login_and_get_cookies(email: str, password: str):
    """通过 API 登录并获取 cookies"""
    
    session = requests.Session()
    
    # 先获取页面（可能需要一些初始 cookie）
    resp = session.get("https://dashboard.thordata.com/zh/login")
    print(f"初始页面状态: {resp.status_code}")
    
    # 调用登录 API
    login_data = {
        "email": email,
        "password": password
    }
    
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://dashboard.thordata.com/zh/login",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    resp = session.post(LOGIN_API, json=login_data, headers=headers)
    print(f"登录API响应: {resp.status_code}")
    print(f"响应内容: {resp.text[:500]}")
    
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0:
            token = data.get("data", {}).get("s")
            print(f"✅ 登录成功! Token: {token[:50]}..." if token else "Token为空")
            return session, token
    
    return session, None


def get_playwright_context_with_auth():
    """获取已认证的 Playwright context"""
    
    email = "lightsong@thordata.com"
    password = "Zxs6412915@+"
    
    # 登录获取 token
    session, token = login_and_get_cookies(email, password)
    
    if not token:
        print("❌ 登录失败")
        return None, None
    
    # 使用 Playwright 打开浏览器
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # 方法1: 设置额外的 HTTP 头来模拟已登录状态
        page.set_extra_http_headers({
            "Authorization": f"Bearer {token}"
        })
        
        # 尝试访问需要登录的页面
        page.goto("https://dashboard.thordata.com/zh/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        
        print(f"访问后的URL: {page.url}")
        
        return context, page


if __name__ == "__main__":
    login_and_get_cookies("lightsong@thordata.com", "Zxs6412915@+")
