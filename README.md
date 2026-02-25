# Auto_python (Playwright + Python 3.10)

该项目已从 Selenium 脚本升级为 **Playwright + Pytest** 自动化框架，覆盖：

- 注册（`pytest_register_new.py`）
- 登录（`pytest_login1.py`）
- 购买（`py_buy_zs.py`）

并保留了原有钉钉机器人推送能力（`zhengshifu_2025_07_29.py`）。

## 环境要求

- Python 3.10
- pip

## 安装依赖

```bash
python3.10 -m pip install -U pytest pytest-html playwright requests beautifulsoup4
python3.10 -m playwright install chromium
```

## 执行单项用例

```bash
pytest pytest_login1.py::test_login_zs -v --html=reports/login.html --self-contained-html
pytest pytest_register_new.py::test_register -v --html=reports/register.html --self-contained-html
pytest py_buy_zs.py::test_login_and_buy -v --html=reports/buy.html --self-contained-html
```

## 执行整套流程（含钉钉推送）

```bash
python3.10 zhengshifu_2025_07_29.py
```

运行后会生成：

- HTML 报告：`reports/zhengshifu/`
- 报告截图：`report_images/YYYYMMDD/`
- 失败诊断（截图+HTML）：`artifacts/`

> 注意：请根据实际情况修改测试账号、密码和钉钉 webhook。
