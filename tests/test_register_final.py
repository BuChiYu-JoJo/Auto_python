"""
Thordata 注册功能测试
测试目标：验证注册流程是否出现邮箱激活提示
"""

import os
import sys
from datetime import datetime

def generate_random_email():
    """生成随机邮箱"""
    import random
    return f"test{random.randint(10000, 99999)}@example.com"


def run_test():
    """运行注册测试"""
    import subprocess
    
    test_email = 'testzhuce@thordata.com'
    test_password = 'Zxs6412915@'
    
    script = f'''
const puppeteer = require('puppeteer');

async function testRegister() {{
  const browser = await puppeteer.launch({{
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  }});
  
  const page = await browser.newPage();
  
  try {{
    // 访问注册页面
    await page.goto('https://dashboard.thordata.com/zh/register', {{
      waitUntil: 'domcontentloaded',
      timeout: 60000
    }});
    
    // 等待 Cloudflare
    for (let i = 0; i < 30; i++) {{
      const text = await page.evaluate(() => document.body ? document.body.innerText : '');
      if (!text.includes('请稍候') && !text.includes('just a moment')) break;
      await new Promise(r => setTimeout(r, 1000));
    }}
    
    await new Promise(r => setTimeout(r, 3000));
    
    // 填写表单
    await page.type('input[placeholder="邮箱地址"]', '{test_email}', {{ delay: 50 }});
    await page.type('input[placeholder="密码"]', '{test_password}', {{ delay: 50 }});
    
    // 点击注册按钮
    await page.click('.login-container-body-E-btn');
    
    await new Promise(r => setTimeout(r, 5000));
    
    await page.screenshot({{ path: '/home/test/ai-test/reports/register_result.png', fullPage: true }});
    
    const pageText = await page.evaluate(() => document.body.innerText);
    const finalUrl = page.url();
    
    // 检查结果
    const hasActivation = ['验证', '激活', '确认', '邮件'].some(k => 
      pageText.toLowerCase().includes(k.toLowerCase()));
    const hasError = ['错误', '失败', '已存在'].some(k => 
      pageText.toLowerCase().includes(k.toLowerCase()));
    
    console.log('RESULT:', JSON.stringify({{
      url: finalUrl,
      hasActivation,
      hasError,
      pageText: pageText.substring(0, 500)
    }}));
    
  }} catch(e) {{
    console.log('ERROR:', e.message);
  }}
  
  await browser.close();
}}

testRegister();
'''
    
    # 保存测试脚本
    with open('/home/test/ai-test/tests/test_register.js', 'w') as f:
        f.write(script)
    
    print("测试脚本已保存: tests/test_register.js")
    print("运行: node tests/test_register.js")


if __name__ == "__main__":
    run_test()
