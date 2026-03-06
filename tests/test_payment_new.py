#!/usr/bin/env python3
"""
支付功能测试用例 - 完整流程版
包括登录、选择套餐、进入支付页面
"""

import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.login_page import LoginPage


class PaymentTestResult:
    """支付测试结果类"""
    
    def __init__(self):
        self.name = "Thordata 支付测试"
        self.results = {}


# 代理配置
PROXY = {
    "server": "http://rmmsg2sa.pr.thordata.net:9999",
    "username": "td-customer-MzsNH4f",
    "password": "EtXApbeko8bDT"
}

# 测试账号
TEST_EMAIL = "lightsong@thordata.com"
TEST_PASSWORD = "Zxs6412915@+"


def run_payment_test() -> PaymentTestResult:
    """运行支付测试"""
    result = PaymentTestResult()
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            proxy=PROXY,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            print("=" * 60)
            print("开始执行支付测试...")
            print("=" * 60)
            
            # ===== 步骤1: 登录 =====
            print("\n[步骤1] 登录...")
            page.goto("https://dashboard.thordata.com/zh/login", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            
            # 输入账号密码
            page.fill('input[placeholder="电子邮件地址"]', TEST_EMAIL)
            page.wait_for_timeout(500)
            page.fill('input[placeholder="密码"]', TEST_PASSWORD)
            page.wait_for_timeout(500)
            
            # 点击登录
            page.keyboard.press('Enter')
            page.wait_for_timeout(15000)
            
            if "login" in page.url.lower():
                print("  ❌ 登录失败")
                result.results["登录"] = "FAILED"
                return result
            else:
                print("  ✅ 登录成功")
                result.results["登录"] = "PASSED"
            
            # ===== 步骤2: 访问住宅代理页面 =====
            print("\n[步骤2] 访问住宅代理页面...")
            page.goto("https://dashboard.thordata.com/zh/residential-proxies", 
                     wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(10000)
            print(f"  ✅ 页面加载完成: {page.url}")
            result.results["访问代理页"] = "PASSED"
            
            # ===== 步骤3: 选择套餐 =====
            print("\n[步骤3] 选择1GB套餐...")
            
            # 滚动到页面底部找到订单摘要区域
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(3000)
            
            # 使用 JS 点击 1GB 元素
            clicked = page.evaluate('''
                () => {
                    const elements = document.querySelectorAll('div,span,p');
                    for (let el of elements) {
                        if (el.textContent && el.textContent.trim() === '1 GB') {
                            // 找到父级可点击元素
                            let parent = el.parentElement;
                            while (parent) {
                                if (parent.click) {
                                    parent.click();
                                    return true;
                                }
                                parent = parent.parentElement;
                            }
                        }
                    }
                    return false;
                }
            ''')
            
            if clicked:
                print("  ✅ 已选择1GB套餐")
                result.results["选择套餐"] = "PASSED"
            else:
                # 如果点击失败，尝试默认的继续结账（当前选中的是50GB）
                print("  ⚠️ 无法选择1GB，使用当前选中套餐")
                result.results["选择套餐"] = "BLOCKED"
            
            page.wait_for_timeout(2000)
            
            # ===== 步骤4: 点击继续结账 =====
            print("\n[步骤4] 点击继续结账...")
            try:
                page.click('text=继续结账', timeout=10000)
                page.wait_for_timeout(10000)
                print(f"  ✅ 进入结账页面: {page.url}")
                result.results["结账"] = "PASSED"
            except Exception as e:
                print(f"  ⚠️ 结账: {e}")
                result.results["结账"] = "BLOCKED"
            
            # ===== 步骤5: 支付方式测试 =====
            print("\n[步骤5] 支付方式测试...")
            
            # 获取当前页面内容
            page_content = page.inner_text('body')
            
            # 检查各种支付方式
            payment_methods = [
                ("信用卡", ["信用卡", "Credit Card", "Stripe"]),
                ("支付宝", ["支付宝", "Alipay"]),
                ("PayPal", ["PayPal"]),
                ("加密币", ["加密", "Crypto", "Bitcoin"]),
            ]
            
            for method_name, keywords in payment_methods:
                found = any(kw in page_content for kw in keywords)
                if found:
                    print(f"  ✅ {method_name}: 可用")
                    result.results[f"支付-{method_name}"] = "PASSED"
                else:
                    print(f"  ⚠️ {method_name}: 未找到")
                    result.results[f"支付-{method_name}"] = "BLOCKED"
            
            # 截图保存
            page.screenshot(path='/home/test/ai-test/screenshots/payment_page.png', full_page=True)
            print(f"  📸 截图保存")
            
        except Exception as e:
            print(f"\n❌ 测试出错: {e}")
            result.results["错误"] = str(e)
        
        finally:
            browser.close()
    
    return result


def generate_html_report(result: PaymentTestResult):
    """生成 HTML 报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"/home/test/ai-test/reports/payment_test_report_{timestamp}.html"
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>支付测试报告</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); padding: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; }}
        h1 {{ color: #333; }}
        .result {{ padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .pass {{ background: #d4edda; color: #155724; }}
        .fail {{ background: #f8d7da; color: #721c24; }}
        .blocked {{ background: #fff3cd; color: #856404; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>💳 支付测试报告</h1>
        <p>测试时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <hr>
"""
    
    for name, status in result.results.items():
        cls = "pass" if status == "PASSED" else ("fail" if status == "FAILED" else "blocked")
        emoji = "✅" if status == "PASSED" else ("❌" if status == "FAILED" else "⚠️")
        html += f'<div class="result {cls}">{emoji} {name}: {status}</div>'
    
    html += """
    </div>
</body>
</html>"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return report_path


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Thordata 支付测试 (完整流程)")
    print("=" * 60 + "\n")
    
    result = run_payment_test()
    
    print("\n" + "=" * 60)
    print("测试执行完成!")
    print("=" * 60)
    
    # 生成报告
    report_path = generate_html_report(result)
    print(f"\n📊 报告路径: {report_path}")
    
    # 打印结果摘要
    print("\n测试结果摘要:")
    for name, status in result.results.items():
        print(f"  {name}: {status}")
    
    return result


if __name__ == "__main__":
    main()
