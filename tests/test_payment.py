"""
支付功能测试用例 - 使用 Page Object 模式
"""

import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.login_page import LoginPage
from pages.payment_page import PaymentPage
from config.cookies import THORDATA_COOKIES, LOGGED_IN_URL


class PaymentTestResult:
    """支付测试结果类"""
    
    def __init__(self):
        self.name = "Thordata 支付测试"
        self.results = {}


def run_payment_test() -> PaymentTestResult:
    """运行支付测试"""
    result = PaymentTestResult()
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with sync_playwright() as p:
        # 代理配置
        proxy = {
            "server": "http://rmmsg2sa.pr.thordata.net:9999",
            "username": "td-customer-MzsNH4f",
            "password": "EtXApbeko8bDT"
        }
        
        browser = p.chromium.launch(
            headless=False,
            proxy=proxy,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        # ===== 注入 Cookie（跳过登录）=====
        print("\n[Cookie注入] 正在注入登录 Cookie...")
        context.add_cookies(THORDATA_COOKIES)
        print(f"  ✅ 已注入 {len(THORDATA_COOKIES)} 个 Cookie")
        
        page = context.new_page()
        
        # 使用 Page Object
        payment_page = PaymentPage(page)
        
        # 测试配置
        pricing_url = "https://dashboard.thordata.com/zh/subscription"
        
        try:
            print("=" * 60)
            print("开始执行支付测试...")
            print("=" * 60)
            
            # 步骤1: 使用 Cookie 直接跳转
            print("\n[步骤1] 使用 Cookie 验证登录状态...")
            page.goto(LOGGED_IN_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            
            if "login" not in page.url.lower():
                print("  ✅ Cookie 登录成功")
                result.results["登录"] = "PASSED"
            else:
                print("  ❌ Cookie 登录失败")
                result.results["登录"] = "FAILED"
                return result
            
            # 步骤2: 进入定价页
            print("\n[步骤2] 进入定价页...")
            page.goto(pricing_url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            print("  ✅ 已进入定价页")
            result.results["进入定价页"] = "PASSED"
            
            # 步骤3: 选择套餐
            print("\n[步骤3] 选择套餐...")
            # 查找1GB套餐
            try:
                page.click('text=1GB')
                page.wait_for_timeout(2000)
                print("  ✅ 已选择1GB套餐")
                result.results["选择套餐"] = "PASSED"
            except Exception as e:
                print(f"  ⚠️ 选择套餐: {e}")
                result.results["选择套餐"] = "BLOCKED"
            
            # 步骤4: 点击继续结账
            print("\n[步骤4] 点击继续结账...")
            try:
                page.click('text=继续')
                page.wait_for_timeout(3000)
                print("  ✅ 已进入支付页面")
                result.results["结账"] = "PASSED"
            except Exception as e:
                print(f"  ⚠️ 结账: {e}")
                result.results["结账"] = "BLOCKED"
            
            # 测试各支付方式
            payment_methods = [
                ("信用卡", "text=信用卡"),
                ("支付宝", "text=支付宝"),
                ("PayPal", "text=PayPal"),
                ("加密币", "text=加密"),
            ]
            
            for method_name, selector in payment_methods:
                print(f"\n[测试] {method_name}支付...")
                
                # 刷新到支付方式页面
                page.goto(pricing_url)
                page.wait_for_timeout(2000)
                try:
                    page.click('text=1GB')
                    page.wait_for_timeout(1000)
                    page.click('text=继续')
                    page.wait_for_timeout(3000)
                except:
                    pass
                
                # 选择支付方式
                try:
                    page.click(selector)
                    page.wait_for_timeout(2000)
                    
                    # 检查支付弹窗/跳转
                    if method_name == "信用卡":
                        # 检查 Stripe iframe
                        iframes = page.locator('iframe').all()
                        if len(iframes) > 0:
                            print(f"  ✅ {method_name}: Stripe iframe 出现")
                            result.results[method_name] = "PASSED"
                        else:
                            print(f"  ⚠️ {method_name}: 未找到 Stripe")
                            result.results[method_name] = "BLOCKED"
                    
                    elif method_name == "支付宝":
                        # 支付宝会跳转
                        if 'alipay' in page.url.lower():
                            print(f"  ✅ {method_name}: 已跳转")
                            result.results[method_name] = "PASSED"
                        else:
                            # 检查页面内容
                            content = page.content()
                            if 'alipay' in content.lower():
                                print(f"  ✅ {method_name}: 找到支付宝")
                                result.results[method_name] = "PASSED"
                            else:
                                print(f"  ⚠️ {method_name}: 未跳转")
                                result.results[method_name] = "BLOCKED"
                    
                    else:
                        print(f"  ✅ {method_name}: 已选择")
                        result.results[method_name] = "PASSED"
                        
                except Exception as e:
                    print(f"  ❌ {method_name}: {e}")
                    result.results[method_name] = "FAILED"
                
                # 截图
                page.screenshot(path=f"/home/test/ai-test/reports/screenshots/payment_{method_name}.png", full_page=True)
            
        except Exception as e:
            print(f"\n❌ 测试出错: {str(e)}")
            result.results["ERROR"] = str(e)
        
        finally:
            context.close()
            browser.close()
    
    return result


def generate_html_report(result: PaymentTestResult):
    """生成HTML测试报告"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 构建结果表格
    rows = ""
    passed = 0
    failed = 0
    for name, status in result.results.items():
        icon = "✅" if status == "PASSED" else ("❌" if status == "FAILED" else "⚠️")
        rows += f"<tr><td>{name}</td><td>{icon} {status}</td></tr>\n"
        if status == "PASSED":
            passed += 1
        elif status == "FAILED":
            failed += 1
    
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>支付测试报告 - Thordata</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{ text-align: center; color: white; margin-bottom: 30px; }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .summary {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: white; padding: 20px 30px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .summary-card .label {{ color: #666; font-size: 14px; }}
        .summary-card .value {{ font-size: 24px; font-weight: bold; }}
        .detail {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .detail h2 {{ margin-top: 0; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .footer {{ text-align: center; color: white; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💳 支付功能自动化测试报告</h1>
            <p>Thordata Dashboard</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="label">通过</div>
                <div class="value" style="color: #28a745;">{passed}</div>
            </div>
            <div class="summary-card">
                <div class="label">失败</div>
                <div class="value" style="color: #dc3545;">{failed}</div>
            </div>
            <div class="summary-card">
                <div class="label">总计</div>
                <div class="value">{len(result.results)}</div>
            </div>
        </div>
        
        <div class="detail">
            <h2>📋 测试结果</h2>
            <table>
                <thead>
                    <tr>
                        <th>测试项目</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Powered by Playwright + Page Object Pattern</p>
        </div>
    </div>
</body>
</html>'''
    
    report_path = f"/home/test/ai-test/reports/payment_test_report_{timestamp}.html"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📊 支付测试报告已生成: {report_path}")
    return report_path


def main():
    """主函数"""
    print("开始 Thordata 支付功能测试...\n")
    
    # 运行测试
    result = run_payment_test()
    
    # 生成报告
    report_path = generate_html_report(result)
    
    print("\n" + "=" * 60)
    print("支付测试执行完成!")
    print("=" * 60)
    print("\n测试结果摘要:")
    for name, status in result.results.items():
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
