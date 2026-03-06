"""
注册功能测试用例 - 使用 Page Object 模式
"""

import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.register_page import RegisterPage


class RegisterTestResult:
    """注册测试结果类"""
    
    def __init__(self):
        self.name = "Thordata 注册测试"
        self.status = "PASSED"
        self.email_activation_hint = False
        self.activation_message = ""
        self.start_time = ""
        self.end_time = ""
        self.duration = 0


def run_test() -> RegisterTestResult:
    """运行注册测试"""
    result = RegisterTestResult()
    result.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # 使用 Page Object
        register_page = RegisterPage(page)
        
        # 测试配置
        test_email = "testzhuce@thordata.com"
        test_password = "Zxs6412915@+"
        
        try:
            print("=" * 60)
            print("开始执行注册测试...")
            print("=" * 60)
            
            # 步骤1: 导航到注册页
            print("\n[步骤1] 访问注册页面...")
            register_page.navigate()
            print(f"  ✅ 页面标题: {page.title()}")
            print(f"  ✅ URL: {page.url}")
            
            # 截图
            page.screenshot(path="/home/test/ai-test/reports/screenshots/register_page.png", full_page=True)
            print("  ✅ 截图: screenshots/register_page.png")
            
            # 步骤2: 填写注册信息
            print("\n[步骤2] 填写注册信息...")
            register_page.fill_email(test_email)
            register_page.fill_password(test_password)
            print(f"  ✅ 邮箱: {test_email}")
            print(f"  ✅ 密码: {'*' * len(test_password)}")
            
            # 截图
            page.screenshot(path="/home/test/ai-test/reports/screenshots/register_filled.png", full_page=True)
            print("  ✅ 截图: screenshots/register_filled.png")
            
            # 步骤3: 勾选协议
            print("\n[步骤3] 勾选用户协议...")
            register_page.check_agreement()
            print("  ✅ 已勾选")
            
            # 步骤4: 点击注册按钮
            print("\n[步骤4] 点击注册按钮...")
            register_page.click_register()
            print("  ✅ 已点击注册按钮")
            
            # 等待结果
            register_page.wait_for_result(8000)
            
            # 截图
            page.screenshot(path="/home/test/ai-test/reports/screenshots/register_result.png", full_page=True)
            print("  ✅ 截图: screenshots/register_result.png")
            
            # 步骤5: 检查结果
            print("\n[步骤5] 检查结果...")
            print(f"  📍 当前URL: {page.url}")
            
            # 检查是否有激活提示
            result.email_activation_hint = register_page.has_activation_hint()
            result.activation_message = register_page.get_activation_message()
            
            if result.email_activation_hint:
                result.status = "PASSED"
                print(f"  ✅ 测试通过: 找到邮箱激活提示")
                if result.activation_message:
                    print(f"  📧 激活提示: {result.activation_message}")
            else:
                # 检查是否有错误
                error_msg = register_page.get_error_message()
                if error_msg:
                    result.status = "FAILED"
                    print(f"  ❌ 注册失败: {error_msg}")
                else:
                    result.status = "BLOCKED"
                    print("  ⚠️ 无法确定测试结果")
            
        except Exception as e:
            print(f"\n❌ 测试执行出错: {str(e)}")
            result.status = "ERROR"
            page.screenshot(path="/home/test/ai-test/reports/screenshots/register_error.png", full_page=True)
        
        finally:
            context.close()
            browser.close()
    
    result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start = datetime.strptime(result.start_time, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(result.end_time, "%Y-%m-%d %H:%M:%S")
    result.duration = (end - start).total_seconds()
    
    return result


def generate_html_report(result: RegisterTestResult, test_email: str = ""):
    """生成HTML格式测试报告"""
    
    status_colors = {
        "PASSED": "#28a745",
        "FAILED": "#dc3545",
        "BLOCKED": "#ffc107",
        "ERROR": "#dc3545"
    }
    
    status_icons = {
        "PASSED": "✅",
        "FAILED": "❌",
        "BLOCKED": "⚠️",
        "ERROR": "❌"
    }
    
    status_color = status_colors.get(result.status, "#666")
    status_icon = status_icons.get(result.status, "❓")
    
    # 激活提示HTML
    if result.email_activation_hint:
        activation_html = f'''
        <div class="detail-row">
            <div class="detail-label">激活提示</div>
            <div class="detail-value" style="color: #28a745;">✅ {result.activation_message or "已显示邮箱验证提示"}</div>
        </div>
        '''
    else:
        activation_html = ''
    
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>注册功能自动化测试报告</title>
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
        .summary {{ display: flex; justify-content: center; gap: 30px; margin-bottom: 30px; }}
        .summary-card {{ background: white; padding: 20px 40px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .summary-card .label {{ color: #666; font-size: 14px; }}
        .summary-card .value {{ font-size: 24px; font-weight: bold; color: {status_color}; }}
        .detail {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .detail h2 {{ margin-top: 0; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .detail-row {{ display: flex; padding: 12px 0; border-bottom: 1px solid #eee; }}
        .detail-label {{ width: 150px; color: #666; font-weight: bold; }}
        .detail-value {{ flex: 1; color: #333; }}
        .screenshot {{ margin-top: 20px; }}
        .screenshot img {{ max-width: 100%; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .footer {{ text-align: center; color: white; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 注册功能自动化测试报告</h1>
            <p>Thordata Dashboard</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="label">测试状态</div>
                <div class="value">{status_icon} {result.status}</div>
            </div>
            <div class="summary-card">
                <div class="label">邮箱激活提示</div>
                <div class="value" style="color: {'#28a745' if result.email_activation_hint else '#dc3545'};">
                    {'✅ 有' if result.email_activation_hint else '❌ 无'}
                </div>
            </div>
        </div>
        
        <div class="detail">
            <h2>📋 测试详情</h2>
            <div class="detail-row">
                <div class="detail-label">测试名称</div>
                <div class="detail-value">{result.name}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">测试URL</div>
                <div class="detail-value">https://dashboard.thordata.com/zh/register</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">测试邮箱</div>
                <div class="detail-value">{test_email}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">开始时间</div>
                <div class="detail-value">{result.start_time}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">结束时间</div>
                <div class="detail-value">{result.end_time}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">测试耗时</div>
                <div class="detail-value">{result.duration:.2f}秒</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">测试结果</div>
                <div class="detail-value" style="color: {status_color}; font-weight: bold;">{status_icon} {result.status}</div>
            </div>
            {activation_html}
        </div>
        
        <div class="detail">
            <h2>📸 测试截图</h2>
            <div class="screenshot">
                <p><strong>注册页面</strong></p>
                <img src="screenshots/register_page.png" alt="注册页面">
            </div>
            <div class="screenshot">
                <p><strong>填写信息</strong></p>
                <img src="screenshots/register_filled.png" alt="填写信息">
            </div>
            <div class="screenshot">
                <p><strong>注册结果</strong></p>
                <img src="screenshots/register_result.png" alt="注册结果">
            </div>
        </div>
        
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Powered by Playwright + Page Object Pattern</p>
        </div>
    </div>
</body>
</html>'''
    
    report_path = "/home/test/ai-test/reports/register_test_report.html"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📊 测试报告已生成: {report_path}")
    return report_path


def main():
    """主函数"""
    test_email = "testzhuce@thordata.com"
    
    print("开始 Thordata 注册功能测试...\n")
    
    # 运行测试
    result = run_test()
    
    # 生成报告
    report_path = generate_html_report(result, test_email)
    
    print("\n" + "=" * 60)
    print("测试执行完成!")
    print("=" * 60)
    print(f"测试状态: {result.status}")
    print(f"邮箱激活提示: {'有' if result.email_activation_hint else '无'}")


if __name__ == "__main__":
    main()
