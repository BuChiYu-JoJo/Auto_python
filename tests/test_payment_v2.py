#!/usr/bin/env python3
"""
Thordata 支付测试 - 优化版
- 参数化配置
- 失败自动截图
- 支付成功截图
"""

import os
import sys
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
    
    # 测试账号
    "account": {
        "email": "lightsong@thordata.com",
        "password": "Zxs6412915@+"
    },
    
    # 目标URL
    "urls": {
        "login": "https://dashboard.thordata.com/zh/login",
        "residential_proxies": "https://dashboard.thordata.com/zh/residential-proxies"
    },
    
    # 套餐选择
    "package": "1 GB",
    
    # 截图目录
    "screenshot_dir": "/home/test/ai-test/screenshots",
    
    # 报告目录
    "report_dir": "/home/test/ai-test/reports"
}


class PaymentTestResult:
    def __init__(self):
        self.name = "Thordata 支付测试"
        self.start_time = datetime.now()
        self.end_time = None
        self.results = {}
        self.screenshots = []
        self.error_message = ""


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


def run_payment_test(config=None):
    """运行支付测试"""
    if config:
        CONFIG.update(config)
    
    result = PaymentTestResult()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            proxy=CONFIG["proxy"],
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            print("=" * 60)
            print("Thordata 支付测试")
            print("=" * 60)
            print(f"账号: {CONFIG['account']['email']}")
            print(f"套餐: {CONFIG['package']}")
            print("=" * 60)
            
            # ===== 步骤1: 登录 =====
            print("\n[步骤1] 登录...")
            page.goto(CONFIG["urls"]["login"], wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            
            page.fill('input[placeholder="电子邮件地址"]', CONFIG["account"]["email"])
            page.wait_for_timeout(500)
            page.fill('input[placeholder="密码"]', CONFIG["account"]["password"])
            page.wait_for_timeout(500)
            page.keyboard.press('Enter')
            page.wait_for_timeout(15000)
            
            if "login" in page.url.lower():
                print("  ❌ 登录失败")
                take_screenshot(page, "login_failed", "登录失败")
                result.results["登录"] = "FAILED"
                result.error_message = "登录失败"
                return result
            else:
                print("  ✅ 登录成功")
                result.results["登录"] = "PASSED"
            
            # ===== 步骤2: 访问代理页 =====
            print("\n[步骤2] 访问住宅代理页面...")
            page.goto(CONFIG["urls"]["residential_proxies"], wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(10000)
            print(f"  ✅ 页面加载: {page.url}")
            result.results["访问代理页"] = "PASSED"
            
            # ===== 步骤3: 选择套餐 =====
            print("\n[步骤3] 选择套餐...")
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(3000)
            
            # JS 点击套餐
            clicked = page.evaluate(f'''
                () => {{
                    const elements = document.querySelectorAll('div,span,p');
                    for (let el of elements) {{
                        if (el.textContent && el.textContent.trim() === '{CONFIG["package"]}') {{
                            let parent = el.parentElement;
                            while (parent) {{
                                if (parent.click) {{
                                    parent.click();
                                    return true;
                                }}
                                parent = parent.parentElement;
                            }}
                        }}
                    }}
                    return false;
                }}
            ''')
            
            if clicked:
                print(f"  ✅ 已选择 {CONFIG['package']} 套餐")
                result.results["选择套餐"] = "PASSED"
            else:
                print(f"  ⚠️ 无法选择套餐")
                take_screenshot(page, "select_package_failed", "选择套餐失败")
                result.results["选择套餐"] = "BLOCKED"
            
            page.wait_for_timeout(2000)
            
            # ===== 步骤4: 点击结账 =====
            print("\n[步骤4] 点击继续结账...")
            try:
                page.click('text=继续结账', timeout=10000)
                page.wait_for_timeout(10000)
                print(f"  ✅ 进入结账: {page.url}")
                result.results["结账"] = "PASSED"
                
                # 支付调起成功截图
                screenshot = take_screenshot(page, "payment_success", "支付调起成功")
                if screenshot:
                    result.screenshots.append(screenshot)
                    
            except Exception as e:
                print(f"  ❌ 结账失败: {e}")
                take_screenshot(page, "checkout_failed", "结账失败")
                result.results["结账"] = "FAILED"
                result.error_message = str(e)
                return result
            
            # ===== 步骤5: 支付方式检测 =====
            print("\n[步骤5] 检测支付方式...")
            page_content = page.inner_text('body')
            
            payment_methods = [
                ("信用卡", ["信用卡", "Credit Card", "Stripe"]),
                ("支付宝", ["支付宝", "Alipay"]),
                ("加密币", ["加密", "Crypto", "Bitcoin"]),
            ]
            
            for method_name, keywords in payment_methods:
                found = any(kw in page_content for kw in keywords)
                status = "PASSED" if found else "BLOCKED"
                result.results[f"支付-{method_name}"] = status
                emoji = "✅" if found else "⚠️"
                print(f"  {emoji} {method_name}: {'可用' if found else '未找到'}")
            
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            take_screenshot(page, "exception", "异常截图")
            result.error_message = str(e)
            result.results["错误"] = "FAILED"
        
        finally:
            browser.close()
    
    result.end_time = datetime.now()
    return result


def generate_report(result: PaymentTestResult):
    """生成HTML报告"""
    duration = (result.end_time - result.start_time).total_seconds()
    timestamp = result.start_time.strftime("%Y%m%d_%H%M%S")
    
    passed = sum(1 for v in result.results.values() if v == "PASSED")
    failed = sum(1 for v in result.results.values() if v == "FAILED")
    blocked = sum(1 for v in result.results.values() if v == "BLOCKED")
    
    report_path = f"{CONFIG['report_dir']}/payment_test_report_{timestamp}.html"
    
    # 生成截图链接HTML
    screenshots_html = ""
    for shot in result.screenshots:
        filename = os.path.basename(shot)
        screenshots_html += f'<div class="screenshot"><img src="{filename}" alt="截图"></div>'
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - Thordata</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; padding: 40px 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px 40px; color: white; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .content {{ padding: 30px 40px; }}
        .summary {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ flex: 1; background: #f8f9fa; padding: 20px; border-radius: 12px; text-align: center; }}
        .summary-card .label {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
        .summary-card .value {{ font-size: 32px; font-weight: bold; }}
        .summary-card.passed .value {{ color: #28a745; }}
        .summary-card.failed .value {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ padding: 16px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #333; font-size: 14px; }}
        td {{ font-size: 14px; }}
        .status {{ display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 500; }}
        .status.pass {{ background: #d4edda; color: #155724; }}
        .status.fail {{ background: #f8d7da; color: #721c24; }}
        .status.blocked {{ background: #fff3cd; color: #856404; }}
        .footer {{ background: #f8f9fa; padding: 20px 40px; font-size: 13px; color: #666; display: flex; justify-content: space-between; }}
        .screenshot {{ margin-top: 20px; }}
        .screenshot img {{ max-width: 100%; border-radius: 8px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💳 Thordata 支付测试报告</h1>
            <div class="meta">测试时间: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')} | 耗时: {duration:.1f}秒</div>
        </div>
        <div class="content">
            <div class="summary">
                <div class="summary-card passed">
                    <div class="label">通过</div>
                    <div class="value">{passed}</div>
                </div>
                <div class="summary-card failed">
                    <div class="label">失败</div>
                    <div class="value">{failed}</div>
                </div>
                <div class="summary-card">
                    <div class="label">跳过/未找到</div>
                    <div class="value">{blocked}</div>
                </div>
            </div>
            <h2 style="margin-bottom: 20px; color: #333; font-size: 18px;">测试结果详情</h2>
            <table>
                <thead>
                    <tr><th>测试项目</th><th>状态</th><th>备注</th></tr>
                </thead>
                <tbody>
"""
    
    status_map = {
        "PASSED": ("pass", "✅ 通过"),
        "FAILED": ("fail", "❌ 失败"),
        "BLOCKED": ("blocked", "⚠️ 未找到")
    }
    
    for name, status in result.results.items():
        css_class, status_text = status_map.get(status, ("blocked", status))
        html += f'                    <tr><td>{name}</td><td><span class="status {css_class}">{status_text}</span></td><td>-</td></tr>\n'
    
    if result.error_message:
        html += f'                    <tr><td>错误信息</td><td colspan="2">{result.error_message}</td></tr>\n'
    
    html += f"""                </tbody>
            </table>
"""
    
    if screenshots_html:
        html += f"            <h2 style='margin: 30px 0 20px;'>支付成功截图</h2>\n            {screenshots_html}\n"
    
    html += f"""        </div>
        <div class="footer">
            <span>Agent: OpenClaw Automation</span>
            <span>{result.start_time.strftime('%Y-%m-%d %H:%M:%S')}</span>
        </div>
    </div>
</body>
</html>"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return report_path


def main():
    print("\n" + "=" * 60)
    print("Thordata 支付测试 (优化版)")
    print("=" * 60 + "\n")
    
    result = run_payment_test()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    
    # 生成报告
    report_path = generate_report(result)
    print(f"\n📊 报告: {report_path}")
    
    # 打印摘要
    print("\n结果摘要:")
    for name, status in result.results.items():
        print(f"  {name}: {status}")
    
    return result


if __name__ == "__main__":
    main()
