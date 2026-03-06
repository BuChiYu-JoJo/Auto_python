#!/usr/bin/env python3
"""
百度搜索自动化测试脚本
用法: python3 baidu_demo.py
"""

from playwright.sync_api import sync_playwright
import os

def main():
    # 设置字体环境变量
    os.environ['LANG'] = 'zh_CN.UTF-8'
    
    with sync_playwright() as p:
        # 启动浏览器 (headless 模式)
        browser = p.chromium.launch(
            headless=True, 
            args=[
                '--disable-blink-features=AutomationControlled',
                '--font-render-hinting=none',
                '--disable-font-subpixel-positioning',
            ]
        )
        
        # 创建新页面，设置视口大小
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # 1. 打开百度
        page.goto('https://www.baidu.com')
        page.wait_for_load_state('domcontentloaded')
        print('1. 打开百度:', page.title())
        
        # 2. 输入搜索词并搜索
        page.keyboard.type('OpenClaw AI 助手')
        page.keyboard.press('Enter')
        page.wait_for_load_state('networkidle')
        
        print('2. 搜索完成:', page.title())
        
        # 3. 获取搜索结果
        results = page.locator('.result.c-container').all_text_contents()[:5]
        print('3. 前5条结果:')
        for i, r in enumerate(results, 1):
            print(f'   {i}. {r[:80]}')
        
        # 4. 截图保存
        page.screenshot(path='/root/.openclaw/workspace/baidu_openclaw.png', full_page=True)
        print('4. 截图已保存到: /root/.openclaw/workspace/baidu_openclaw.png')
        
        browser.close()
        print('\n✅ 执行完成!')

if __name__ == '__main__':
    main()
