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
    page.evaluate(
        """
        const selector = '[data-lc-id="1"].css-zsgaow.efsb37y0';
        const el = document.querySelector(selector);
        if (el) {
          el.style.setProperty('display','none','important');
          el.style.setProperty('visibility','hidden','important');
          el.style.setProperty('pointer-events','none','important');
        }
        """
    )


def _get_alert_text(page: Page, timeout_ms: int = 60000) -> str:
    selectors = [
        ".ant-message-custom-content",
        ".ant-message-notice-content",
        ".ant-form-item-explain-error",
        "[role='alert']",
    ]
    for selector in selectors:
        try:
            item = page.locator(selector).first
            item.wait_for(state="visible", timeout=timeout_ms)
            text = item.inner_text().strip()
            if text:
                return text
        except TimeoutError:
            continue
    raise AssertionError("超时：未找到弹窗内容")


def register(page: Page, base_url: str, username: str, password: str, invitation: str | None = None) -> str:
    page.goto(base_url, wait_until="domcontentloaded")
    _dismiss_interfering_component(page)

    page.locator("input#email, input[placeholder*='mail']").first.fill(username)
    page.locator("input#psw, input[placeholder*='assword']").first.fill(password)

    if invitation:
        invitation_input = page.locator("input[placeholder*='Invitation']")
        if invitation_input.count() > 0:
            invitation_input.first.fill(invitation)

    signup_btn = page.locator("div.login-container-body-E-btn", has_text="Sign up").first
    signup_btn.click(timeout=20000)
    return _get_alert_text(page)


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
    "base_url,username,password,invitation,expected_alert",
    [
        ("https://dashboard.thordata.com/register", "goopkk23213@thordata.com", "Zxs6412915@+", "5522", "Email sent successful"),
    ],
)
def test_register(base_url: str, username: str, password: str, invitation: str, expected_alert: str, page: Page) -> None:
    try:
        alert_text = register(page, base_url, username, password, invitation)
        assert expected_alert == alert_text, f"预期：'{expected_alert}'，实际：'{alert_text}'"
    except Exception as e:
        png, html = _capture_diag(page, "register_zs")
        raise AssertionError(f"正式服注册失败: {e}（已保存 {png} 和 {html}）") from e


@pytest.mark.parametrize(
    "base_url,username,password,invitation,expected_alert",
    [
        ("https://dashboard.acen.http.321174.com/register", "mmkkook@thordata.com", "Zxs6412915@+", "5522", "Verify your email"),
    ],
)
def test_register_cs(base_url: str, username: str, password: str, invitation: str, expected_alert: str, page: Page) -> None:
    try:
        alert_text = register(page, base_url, username, password, invitation)
        assert expected_alert == alert_text, f"预期：'{expected_alert}'，实际：'{alert_text}'"
    except Exception as e:
        png, html = _capture_diag(page, "register_cs")
        raise AssertionError(f"测试服注册失败: {e}（已保存 {png} 和 {html}）") from e
