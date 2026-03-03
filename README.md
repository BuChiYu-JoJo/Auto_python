# AI Test Framework

基于 Playwright 的自动化测试框架

## 📁 项目结构

```
ai-test/
├── baidu_demo.py          # 百度Demo测试脚本
├── config.yaml            # 配置文件
├── package.json          # Node依赖
├── pages/                 # 页面对象
│   ├── __init__.py
│   ├── login_page.py      # 登录页面
│   └── payment_page.py    # 支付页面
├── tests/                 # 测试用例
│   ├── test_login.py      # 登录测试
│   └── test_payment.py    # 支付测试
├── reports/              # 测试报告
└── test-results/         # 测试结果
```

## 🚀 快速开始

### 安装依赖

```bash
npm install
pip install playwright
playwright install chromium
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行单个测试
python tests/test_login.py
```

## 📝 测试用例

### 登录测试 (test_login.py)
- 测试用户登录功能
- 验证登录成功/失败场景
- 验证码识别

### 支付测试 (test_payment.py)
- 信用卡支付
- 支付宝支付
- PayPal支付
- 加密货币支付

## 🔧 技术栈

- **Playwright** - 浏览器自动化
- **Python** - 测试脚本
- **Node.js** - 依赖管理

## 📊 测试报告

测试报告生成在 `reports/` 目录
