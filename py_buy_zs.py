import os
import time

import pytest
from playwright.sync_api import Page, TimeoutError, sync_playwright

VIEWPORT = {"width": 1920, "height": 1080}
LOGIN_URL = "https://dashboard.thordata.com/login"


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


def _hide_chat_overlay(page: Page) -> None:
    page.evaluate(
        """
        const ids = ['chat-widget', 'chat-widget-minimized', 'chat-widget-container', 'livechat-eye-catcher', 'lc_container'];
        ids.forEach(id => {
          const el = document.getElementById(id);
          if (el) {
            el.style.setProperty('display','none','important');
            el.style.setProperty('visibility','hidden','important');
            el.style.setProperty('pointer-events','none','important');
          }
        });
        document.querySelectorAll('iframe').forEach(f => {
          const key = ((f.id || '') + (f.name || '') + (f.getAttribute('title') || '')).toLowerCase();
          if (key.includes('chat') || key.includes('livechat')) {
            f.style.setProperty('display','none','important');
            f.style.setProperty('visibility','hidden','important');
            f.style.setProperty('pointer-events','none','important');
          }
        });
        """
    )


def login(page: Page, username: str, password: str) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    _hide_chat_overlay(page)
    page.locator("input#email, input[placeholder='Email address']").first.fill(username)
    page.locator("input#psw, input[placeholder='Password']").first.fill(password)
    page.locator("#login").click(timeout=20000)
    page.locator(".ant-message-notice-content", has_text="Login successful").first.wait_for(timeout=30000)


def open_buy_entry(page: Page) -> None:
    entry_candidates = [
        "a:has-text('Buy')",
        "button:has-text('Buy')",
        "span:has-text('Buy now')",
    ]
    for selector in entry_candidates:
        target = page.locator(selector)
        if target.count() > 0:
            target.first.click(timeout=10000)
            return
    raise AssertionError("未找到购买入口（Buy）")


def verify_payment_page(page: Page) -> None:
    page.wait_for_load_state("domcontentloaded")
    _hide_chat_overlay(page)

    expected_keywords = ["Credit", "PayPal", "Alipay", "Local payments"]
    body_text = page.locator("body").inner_text(timeout=15000)

    missing = [k for k in expected_keywords if k not in body_text]
    assert len(missing) < len(expected_keywords), f"支付页关键字全部缺失: {missing}"


def trigger_credit_checkout(page: Page) -> None:
    credit = page.locator("label.ant-radio-wrapper", has_text="Credit or debit card")
    if credit.count() > 0:
        credit.first.click(timeout=10000)

    continue_btn = page.locator("span:has-text('Continue'), button:has-text('Continue')")
    if continue_btn.count() > 0:
        continue_btn.first.click(timeout=15000)

    frame = page.frame_locator("iframe[id*='ams-checkout'], iframe[src*='alipay'], iframe[src*='paypal']")
    frame.locator("body").first.wait_for(timeout=20000)


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


@pytest.mark.parametrize("username,password", [("lightsong@thordata.com", "Zxs6412915@+")])
def test_login_and_buy(page: Page, username: str, password: str) -> None:
    try:
        login(page, username, password)
        open_buy_entry(page)
        verify_payment_page(page)
        trigger_credit_checkout(page)
    except (AssertionError, TimeoutError, Exception) as e:
        png, html = _capture_diag(page, "buy_flow")
        raise AssertionError(f"购买流程失败: {e}（已保存 {png} 和 {html}）") from e
