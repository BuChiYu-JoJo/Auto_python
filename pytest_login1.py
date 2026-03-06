# 导入所需的库
import pytest
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time, os

# ===================== 公共：初始化、等待、遮挡处理、诊断 =====================

def init_driver():
    options = Options()
    # 建议调试阶段先关掉 headless，更容易看到是什么挡住了
#    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    chrome_path = "C:\\chrome\\chrome-win64\\chrome.exe"
    options.binary_location = chrome_path
    service = Service("C:\\chrome\\chromedriver-win64\\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def wait_doc_ready(driver, timeout=20):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def capture_diag(driver, tag="diag"):
    ts = int(time.time())
    out = os.path.abspath("./artifacts")
    os.makedirs(out, exist_ok=True)
    png = os.path.join(out, f"{tag}_{ts}.png")
    html = os.path.join(out, f"{tag}_{ts}.html")
    try:
        driver.save_screenshot(png)
    except Exception:
        pass
    try:
        with open(html, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    except Exception:
        pass
    return png, html

def dismiss_interfering_component(driver):
    """
    关闭/隐藏顶部问候/营销条（多套选择器），避免覆盖输入框或按钮。
    """
    selectors_container = [
        '[data-lc-id="1"].css-zsgaow.efsb37y0',     # 你提供的结构
        '[data-lc-id="1"]',
        '.css-zsgaow.efsb37y0',
        '[aria-label="Greeting"],[aria-label="Banner"]'
    ]
    selectors_close = [
        'button[aria-label="Hide greeting"]',
        'button[aria-label="Close"], .close, .ant-modal-close, .ant-drawer-close'
    ]
    # 尝试点击关闭
    for c in selectors_close:
        try:
            btn = WebDriverWait(driver, 1.5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, c)))
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.2)
        except Exception:
            pass
    # 强制隐藏容器
    for sel in selectors_container:
        driver.execute_script("""
            var el = document.querySelector(arguments[0]);
            if(el){
              el.style.setProperty('display','none','important');
              el.style.setProperty('visibility','hidden','important');
              el.style.setProperty('pointer-events','none','important');
            }
        """, sel)

def kill_common_overlays(driver):
    """
    兜底：移除常见遮罩/蒙层/固定条（高 z-index 的 fixed/sticky）。
    尽量温和：仅隐藏疑似遮挡交互的层。
    """
    driver.execute_script("""
      const isCover = (el) => {
        const s = getComputedStyle(el);
        if(!s) return false;
        const pos = s.position;
        const zi = parseInt(s.zIndex) || 0;
        const h = el.offsetHeight || 0;
        const w = el.offsetWidth || 0;
        // 具备覆盖特征：fixed/sticky 且面积较大且 zIndex 高
        if ((pos === 'fixed' || pos === 'sticky') && zi >= 100 && h >= 40 && w >= 200) return true;
        // 常见类名/role
        const cls = (el.className || '') + ' ' + (el.id || '');
        if (/(cookie|consent|banner|toast|snackbar|guide|tour|modal|drawer|overlay)/i.test(cls)) return true;
        if (el.getAttribute('role') === 'dialog' || el.getAttribute('role') === 'alert') return true;
        return false;
      };
      const all = Array.from(document.body.querySelectorAll('*'));
      all.forEach(el => { try {
        if (isCover(el)) {
          el.style.setProperty('display','none','important');
          el.style.setProperty('visibility','hidden','important');
          el.style.setProperty('pointer-events','none','important');
        }
      } catch(e){} });
    """)

def scroll_into_view(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", el)

def safe_type(driver, locator, text, timeout=20):
    """
    等可见 -> 滚动居中 -> JS focus -> clear -> send_keys。
    """
    el = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
    scroll_into_view(driver, el)
    try:
        driver.execute_script("arguments[0].focus();", el)
    except Exception:
        pass
    try:
        el.clear()
    except Exception:
        # 某些自定义输入框不支持 clear，用 JS 清空 value
        try:
            driver.execute_script("if(arguments[0].value!==undefined){arguments[0].value='';}", el)
        except Exception:
            pass
    el.send_keys(text)
    return el

def safe_click(driver, locator, timeout=20):
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
    scroll_into_view(driver, el)
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].click();", el)

# ===================== 弹窗文本 =====================

def get_alert_text(driver, timeout=50):
    try:
        # 优先 ant message
        success_message = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'ant-message-notice-content'))
        )
        return success_message.text.strip()
    except TimeoutException:
        # 兜底：可能错误文案在表单 label/tooltip/snackbar
        candidates = [
            (By.CSS_SELECTOR, '.ant-form-item-explain-error, .ant-form-item-explain .ant-form-item-explain-error'),
            (By.CSS_SELECTOR, '[role="alert"], .toast, .snackbar, .ant-notification-notice-message'),
            (By.XPATH, "//*[contains(., 'Please enter') or contains(., 'password') or contains(., 'Login')]")
        ]
        for how, sel in candidates:
            try:
                el = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((how, sel)))
                txt = (el.text or el.get_attribute('innerText') or '').strip()
                if txt:
                    return txt
            except TimeoutException:
                continue
        png, html = capture_diag(driver, "alert_timeout")
        raise AssertionError(f"超时：未找到弹出框内容（已保存 {png} {html}）")

# ===================== 登录封装（测试服 / 正式服） =====================

def login(driver, username, password):
    driver.get("https://dashboard.acen.http.321174.com/login")  # 测试地址
    wait_doc_ready(driver)
    dismiss_interfering_component(driver)
    kill_common_overlays(driver)

    # 用户名
    admin_input_xpath = "//input[@id='email' or @placeholder='Email address']"
    safe_type(driver, (By.XPATH, admin_input_xpath), username, timeout=20)

    # 密码
    passwd_input_xpath = "//input[@id='psw' or @placeholder='Password']"
    safe_type(driver, (By.XPATH, passwd_input_xpath), password, timeout=20)

    # 点击登录按钮
    try:
        safe_click(driver, (By.ID, "login"), timeout=20)
    except TimeoutException:
        kill_common_overlays(driver)
        safe_click(driver, (By.ID, "login"), timeout=10)

    return get_alert_text(driver)

def login_zs(driver, username, password):
    driver.get("https://dashboard.thordata.com/login")  # 正式地址
    wait_doc_ready(driver)
    dismiss_interfering_component(driver)
    kill_common_overlays(driver)

    # 用户名
    admin_input_xpath = "//input[@id='email' or @placeholder='Email address']"
    safe_type(driver, (By.XPATH, admin_input_xpath), username, timeout=20)

    # 密码
    passwd_input_xpath = "//input[@id='psw' or @placeholder='Password']"
    safe_type(driver, (By.XPATH, passwd_input_xpath), password, timeout=20)

    # 点击登录按钮
    try:
        safe_click(driver, (By.ID, "login"), timeout=20)
    except TimeoutException:
        kill_common_overlays(driver)
        safe_click(driver, (By.ID, "login"), timeout=10)

    return get_alert_text(driver)

# ===================== 用例（保持你的参数化） =====================

@pytest.mark.parametrize("username, password, expected_alert", [
    ("lightsong@thordata.com", "Zxs6412915@+", "Login successful"),
    ("1261977221@qq.com", "Zxs123456##", "Account or password error, please confirm and re-enter."),
    ("", "DFjj55621!", "Please enter your email address"),
    ("lightsong@thordata.com", "", "Please enter your password"),
    ("zxsthreson@gmail.com", "s", "The password must be 6 to 15 characters long, consisting of uppercase and lowercase letters, numbers, and special symbols. Uppercase and lowercase letters and numbers are required. Special characters allowed are @#$%^&*?_:.!/-+"),
])
def test_login_zs(username, password, expected_alert):
    driver = None
    try:
        driver = init_driver()
        alert_text = login_zs(driver, username, password)
        print(f"预期: {expected_alert}")
        print(f"实际: {alert_text}")
        assert alert_text == expected_alert, f"实际：{alert_text}，预期：{expected_alert}"
    except TimeoutException:
        png, html = capture_diag(driver, "timeout_zs")
        raise AssertionError(f"操作超时：未找到页面元素或弹出框内容。已保存 {png} {html}")
    except Exception as e:
        png, html = capture_diag(driver, "error_zs")
        raise AssertionError(f"测试失败，未处理的异常：{e}（已保存 {png} {html}）")
    finally:
        if driver:
            driver.quit()

# 测试服
@pytest.mark.parametrize("username, password, expected_alert", [
    ("lightsong@thordata.com", "Zxs6412915@+", "Login successful"),
    ("1261977221@qq.com", "Zxs123456##", "Account or password error, please confirm and re-enter."),
    ("", "DFjj55621!", "Please enter your email address"),
    ("lightsong@thordata.com", "", "Please enter your password"),
    ("zxsthreson@gmail.com", "s", "The password must be 6 to 15 characters long, consisting of uppercase and lowercase letters, numbers, and special symbols. Uppercase and lowercase letters and numbers are required. Special characters allowed are @#$%^&*?_:.!/-+"),
])
def test_login_cs(username, password, expected_alert):
    driver = None
    try:
        driver = init_driver()
        alert_text = login(driver, username, password)
        print(f"预期: {expected_alert}")
        print(f"实际: {alert_text}")
        assert alert_text == expected_alert, f"实际：{alert_text}，预期：{expected_alert}"
    except TimeoutException:
        png, html = capture_diag(driver, "timeout_cs")
        raise AssertionError(f"操作超时：未找到页面元素或弹出框内容。已保存 {png} {html}")
    except Exception as e:
        png, html = capture_diag(driver, "error_cs")
        raise AssertionError(f"测试失败，未处理的异常：{e}（已保存 {png} {html}）")
    finally:
        if driver:
            driver.quit()
