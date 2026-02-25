import os
import time

import pytest
from playwright.sync_api import Page, TimeoutError, sync_playwright

VIEWPORT = {"width": 1920, "height": 1080}


def _capture_diag(page: Page, tag: str) -> tuple[str, str]:
    ts = int(time.time())
    out_dir = os.path.abspath("./artifacts")
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, f"{tag}_{ts}.png")
    html = os.path.join(out_dir, f"{tag}_{ts}.html")
    page.screenshot(path=png, full_page=True)
    with open(html, "w", encoding="utf-8") as f:
        f.write(page.content())
    return png, html


def _dismiss_interfering_component(page: Page) -> None:
    close_selectors = [
        "button[aria-label='Hide greeting']",
        "button[aria-label='Close']",
        ".ant-modal-close",
        ".ant-drawer-close",
    ]
    for selector in close_selectors:
        locator = page.locator(selector)
        if locator.count() > 0:
            try:
                locator.first.click(timeout=1000)
            except Exception:
                pass

    page.evaluate(
        """
        const candidates = [
            '[data-lc-id="1"].css-zsgaow.efsb37y0',
            '[data-lc-id="1"]',
            '.css-zsgaow.efsb37y0'
        ];
        for (const sel of candidates) {
            const el = document.querySelector(sel);
            if (el) {
                el.style.setProperty('display','none','important');
                el.style.setProperty('visibility','hidden','important');
                el.style.setProperty('pointer-events','none','important');
            }
        }
        """
    )


def _fill_credentials(page: Page, username: str, password: str) -> None:
    email = page.locator("input#email, input[placeholder*='mail'], input[placeholder='Email address']").first
    passwd = page.locator("input#psw, input[placeholder*='assword'], input[placeholder='Password']").first
    email.wait_for(state="visible", timeout=20000)
    email.fill(username)
    passwd.fill(password)


def _read_alert(page: Page, timeout_ms: int = 50000) -> str:
    candidates = [
        ".ant-message-notice-content",
        ".ant-message-custom-content",
        ".ant-form-item-explain-error",
        "[role='alert']",
    ]
    for selector in candidates:
        try:
            item = page.locator(selector).first
            item.wait_for(state="visible", timeout=timeout_ms)
            text = item.inner_text().strip()
            if text:
                return text
        except TimeoutError:
            continue
    raise AssertionError("超时：未找到弹窗或错误提示内容")


def login(page: Page, base_url: str, username: str, password: str) -> str:
    page.goto(base_url, wait_until="domcontentloaded")
    _dismiss_interfering_component(page)
    _fill_credentials(page, username, password)
    page.locator("#login").click(timeout=20000)
    return _read_alert(page)


@pytest.fixture(scope="function")
def page() -> Page:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT)
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


@pytest.mark.parametrize(
    "username,password,expected_alert",
    [
        ("lightsong@thordata.com", "Zxs6412915@+", "Login successful"),
        ("1261977221@qq.com", "Zxs123456##", "Account or password error, please confirm and re-enter."),
        ("", "DFjj55621!", "Please enter your email address"),
        ("lightsong@thordata.com", "", "Please enter your password"),
    ],
)
def test_login_zs(page: Page, username: str, password: str, expected_alert: str) -> None:
    try:
        alert_text = login(page, "https://dashboard.thordata.com/login", username, password)
        assert alert_text == expected_alert, f"实际：{alert_text}，预期：{expected_alert}"
    except Exception as e:
        png, html = _capture_diag(page, "login_zs")
        raise AssertionError(f"登录测试失败: {e}（已保存 {png} 和 {html}）") from e


@pytest.mark.parametrize(
    "username,password,expected_alert",
    [
        ("lightsong@thordata.com", "Zxs6412915@+", "Login successful"),
    ],
)
def test_login_cs(page: Page, username: str, password: str, expected_alert: str) -> None:
    try:
        alert_text = login(page, "https://dashboard.acen.http.321174.com/login", username, password)
        assert alert_text == expected_alert, f"实际：{alert_text}，预期：{expected_alert}"
    except Exception as e:
        png, html = _capture_diag(page, "login_cs")
        raise AssertionError(f"测试服登录失败: {e}（已保存 {png} 和 {html}）") from e
