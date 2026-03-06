#!/usr/bin/env python3
"""
Thordata 注册测试 - 优化版
- 参数化配置
- 使用代理防风控
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
    
    # 注册账号（每次测试建议用不同的邮箱）
    "account": {
        "email": f"test{random.randint(10000,99999)}@thordata.com",
        "password": "Zxs6412915@+"
    },
    
    # 注册URL
    "register_url": "https://dashboard.thordata.com/zh/register",
    
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
        self.screenshots = []


def random_delay(min_sec=0.3, max_sec=1.0):
    """模拟人类延迟"""
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


def run_register_test(config=None):
    """运行注册测试"""
    if config:
        CONFIG.update(config)
    
    result = RegisterTestResult()
    result.email = CONFIG["account"]["email"]
    
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
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )
        
        # 反检测脚本
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = context.new_page()
        
        try:
            print("=" * 60)
            print("Thordata 注册测试 (优化版)")
            print("=" * 60)
            print(f"测试邮箱: {CONFIG['account']['email']}")
            print(f"代理: {CONFIG['proxy']['server']}")
            print("=" * 60)
            
            # ===== 步骤1: 访问注册页 =====
            print("\n[步骤1] 访问注册页面...")
            page.goto(CONFIG["register_url"], wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000)
            
            print(f"  ✅ 页面标题: {page.title()}")
            print(f"  ✅ URL: {page.url}")
            
            take_screenshot(page, "register_page", "注册页")
            
            # ===== 步骤2: 填写邮箱 =====
            print("\n[步骤2] 填写邮箱...")
            try:
                page.fill('input[type="email"], input[name="email"], input[placeholder*="邮箱"], input[placeholder*="email"]', 
                         CONFIG["account"]["email"])
            except:
                page.fill('input[type="text"]', CONFIG["account"]["email"])
            
            random_delay(0.3, 0.8)
            print(f"  ✅ 邮箱: {CONFIG['account']['email']}")
            
            # ===== 步骤3: 填写密码 =====
            print("\n[步骤3] 填写密码...")
            try:
                page.fill('input[type="password"], input[name="password"]', 
                         CONFIG["account"]["password"])
            except Exception as e:
                print(f"  ⚠️ 密码输入尝试: {e}")
            
            random_delay(0.3, 0.8)
            print("  ✅ 密码已填写")
            
            take_screenshot(page, "register_filled", "填写完成")
            
            # ===== 步骤4: 勾选协议 =====
            print("\n[步骤4] 勾选用户协议...")
            try:
                # 尝试勾选复选框
                page.check('input[type="checkbox"]')
                print("  ✅ 已勾选协议")
            except:
                # 可能协议已经是默认勾选
                print("  ⚠️ 协议复选框处理")
            
            random_delay(0.2, 0.5)
            
            # ===== 步骤5: 点击注册 =====
            print("\n[步骤5] 点击注册按钮...")
            try:
                page.click('button[type="submit"]', timeout=5000)
            except:
                try:
                    page.click('button:has-text("注册")', timeout=5000)
                except:
                    page.keyboard.press('Enter')
            
            page.wait_for_timeout(10000)
            
            # 检查是否有验证码
            page_text_check = page.inner_text('body')
            page_content_check = page.content()
            
            if '验证' in page_text_check or 'captcha' in page_content_check.lower() or 'turnstile' in page_content_check.lower() or '人机' in page_text_check:
                print("  ⚠️ 检测到验证码!")
                take_screenshot(page, "register_captcha", "验证码页面")
                
                # 尝试点击验证按钮
                try:
                    page.click('text=人机验证', timeout=5000)
                    print("  👆 点击了人机验证按钮")
                    page.wait_for_timeout(5000)
                except:
                    pass
                
                print("  💡 请在浏览器中手动完成验证...")
                print("  ⏳ 等待 90 秒...")
                page.wait_for_timeout(90000)
                page.wait_for_timeout(5000)
            
            take_screenshot(page, "register_submit", "提交注册")
            
            # ===== 步骤6: 检查结果 =====
            print("\n[步骤6] 检查注册结果...")
            final_url = page.url
            print(f"  📍 URL: {final_url}")
            
            # 获取页面内容
            page_text = page.inner_text('body')
            page_content = page.content()
            
            # 检查是否需要邮箱验证
            activation_keywords = ['验证', '激活', '确认', '确认链接', '24小时']
            result.activation_hint = any(kw in page_text for kw in activation_keywords)
            
            # 检查是否有错误
            error_keywords = ['错误', '失败', '已存在', 'invalid', 'error']
            has_error = any(kw in page_text.lower() for kw in error_keywords)
            
            if result.activation_hint:
                result.status = "PASSED"
                print("  ✅ 注册成功 - 需要邮箱验证")
                # 提取激活提示
                if '已向' in page_text:
                    idx = page_text.find('已向')
                    result.activation_message = page_text[idx:idx+100]
                    print(f"  📧 {result.activation_message}")
                
                take_screenshot(page, "register_success", "注册成功")
                
            elif has_error:
                result.status = "FAILED"
                result.error_message = "注册返回错误"
                print("  ❌ 注册失败")
                take_screenshot(page, "register_failed", "注册失败")
                
            else:
                result.status = "BLOCKED"
                result.error_message = "无法确定结果"
                print("  ⚠️ 无法确定注册结果")
                take_screenshot(page, "register_unknown", "结果未知")
            
        except Exception as e:
            print(f"\n❌ 注册异常: {e}")
            result.status = "ERROR"
            result.error_message = str(e)
            take_screenshot(page, "register_error", "注册异常")
        
        finally:
            browser.close()
    
    result.end_time = datetime.now()
    return result


def generate_report(result: RegisterTestResult):
    """生成HTML报告"""
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
    # 每次生成不同的测试邮箱
    CONFIG["account"]["email"] = f"test{random.randint(10000,99999)}@thordata.com"
    
    print("\n" + "=" * 60)
    print("Thordata 注册测试 (优化版)")
    print("=" * 60 + "\n")
    
    result = run_register_test()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print(f"状态: {result.status}")
    print(f"邮箱: {result.email}")
    if result.activation_message:
        print(f"提示: {result.activation_message[:50]}...")
    if result.error_message:
        print(f"错误: {result.error_message}")
    
    # 生成报告
    report_path = generate_report(result)
    print(f"\n📊 报告: {report_path}")
    
    return result


if __name__ == "__main__":
    main()
