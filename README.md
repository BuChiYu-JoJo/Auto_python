# Thordata Web Automation Test

Thordata 官网的自动化测试项目，基于 Playwright 框架。

## 功能

- 登录测试 (test_login_v2.py)
- 支付测试 (test_payment_v2.py)
- 注册测试 (test_register_v3.py)

## 环境要求

- Node.js
- Python 3.10+
- Playwright

## 安装

```bash
npm install
pip install -r requirements.txt
playwright install
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试
pytest tests/test_login_v2.py
pytest tests/test_payment_v2.py
pytest tests/test_register_v3.py
```

## 配置

配置文件位于 `config.yaml`，可配置：
- 测试目标 URL
- 代理设置
- 测试账号

## 技术栈

- Playwright
- Pytest
- Python
