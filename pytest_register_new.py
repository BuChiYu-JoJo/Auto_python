import pytest
from time import sleep, time
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# 初始化浏览器驱动
def init_driver():
    options = Options()
#    options.add_argument("--headless")  # 启用headless模式（排障期建议先可视化）
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
#    options.add_argument("--start-maximized")
    # 指定Chrome浏览器的路径
    chrome_path = "C:\\chrome\\chrome-win64\\chrome.exe"
    options.binary_location = chrome_path

    service = Service("C:\\chrome\\chromedriver-win64\\chromedriver.exe")  # 替换为chromedriver的路径
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def dismiss_interfering_component(driver, timeout=5):
    """
    关闭/隐藏顶部问候条，避免覆盖输入框或按钮。
    """
    try:
        # 组件容器是否存在
        container = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-lc-id="1"].css-zsgaow.efsb37y0'))
        )
        # 优先点击关闭按钮（更温和）
        try:
            close_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Hide greeting"]'))
            )
            # 有些组件遮挡可视区，用 JS 点击更稳
            driver.execute_script("arguments[0].click();", close_btn)
            WebDriverWait(driver, 2).until(EC.staleness_of(container))
            return
        except Exception:
            pass

        # 兜底：强制隐藏容器
        driver.execute_script("""
            const el = document.querySelector('[data-lc-id="1"].css-zsgaow.efsb37y0');
            if (el) { 
                el.style.setProperty('display','none','important'); 
                el.style.setProperty('visibility','hidden','important'); 
                el.style.setProperty('pointer-events','none','important'); 
            }
        """)
    except TimeoutException:
        # 没有这个组件，忽略
        return


def is_not_obscured(driver, element):
    """
    判断元素中心点是否被其他元素遮挡；若遮挡，返回 False。
    """
    rect = element.rect
    cx = rect['x'] + rect['width'] / 2
    cy = rect['y'] + rect['height'] / 2
    # 滚动确保在视口内
    driver.execute_script("window.scrollTo(0, arguments[0] - 200);", max(cy - 200, 0))
    elem_at_point = driver.execute_script(
        "return document.elementFromPoint(arguments[0], arguments[1]);", cx, cy
    )
    # 判断 elem_at_point 是否就是 element 或其后代
    return driver.execute_script(
        "return arguments[0] === arguments[1] || arguments[0].contains(arguments[1]);",
        element, elem_at_point
    )


def get_alert_text(driver, timeout=20):
    try:
        # 等待 Ant Design 弹窗出现
        alert_elem = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".ant-message-custom-content")
            )
        )
        message = alert_elem.text.strip()
        print(f"获取到的弹出框文本: '{message}'")
        return message

    except TimeoutException:
        raise AssertionError("超时：未找到弹窗内容")
    except NoSuchElementException:
        raise AssertionError("错误：找不到弹窗元素")
    except Exception as e:
        raise AssertionError(f"未处理的异常：{e}")



# 注册功能封装
def register(driver, base_url, username, password, invitation=None):
    driver.get(base_url)

    # ✅ 等页面加载完成，避免直接等待元素造成 Timeout
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # 先处理会遮挡表单的组件
    dismiss_interfering_component(driver)

    # ✅ 改 1：从 visibility 改成 presence，提高容忍度
    admin_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'mail') or contains(@id,'email')]"))
    )
    admin_input.clear()
    admin_input.send_keys(username)

    # ✅ 改 2：同样放宽密码框的等待条件
    passwd_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'assword') or contains(@id,'psw')]"))
    )
    passwd_input.clear()
    passwd_input.send_keys(password)

    # —— 邀请码（可选，同样放宽等待条件）——
    if invitation:
        try:
            invitation_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'Invitation')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", invitation_input)
            invitation_input.clear()
            invitation_input.send_keys(invitation)
        except TimeoutException:
            print("邀请码输入框未找到或不可交互，跳过填写邀请码。")


    # 注册按钮元素示例: <div class="login-container-body-E-btn" data-v-74af8ea3="">Sign up</div>
    register_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//div[contains(@class,'login-container-body-E-btn') and normalize-space()='Sign up']"
        ))
    )

    try:
        register_btn.click()
    except Exception:
        # 若被遮挡或动画导致不可点，用 JS 点击兜底
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", register_btn)
        driver.execute_script("arguments[0].click();", register_btn)

    # —— 后续保持原逻辑 —— #
    try:
        # ✅ 改为等待弹窗出现，而不是等待页面跳转元素
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".ant-message-custom-content"))
        )
    except TimeoutException:
        raise AssertionError("超时：新页面未完全加载")

    alert_text = get_alert_text(driver)
    return alert_text



@pytest.mark.parametrize("base_url, username, password, invitation, expected_alert", [
    ("https://dashboard.thordata.com/register", "goopkk23213@thordata.com", "Zxs6412915@+", "5522", "Email sent successful"),
])
def test_register(base_url, username, password, invitation, expected_alert):
    driver = None
    try:
        driver = init_driver()
        alert_text = register(driver, base_url, username, password, invitation)
        print(f"期望的弹出框文本: '{expected_alert}', 实际获取到的弹出框文本: '{alert_text}'")
        assert expected_alert == alert_text, f"预期：'{expected_alert}'，实际：'{alert_text}'"
        print("注册成功预期=实际")
    except TimeoutException:
        raise AssertionError("操作超时：未找到页面元素或弹出框内容。")
    except Exception as e:
        raise AssertionError(f"测试失败，未处理的异常：{e}")
    finally:
        if driver:
            driver.quit()


@pytest.mark.parametrize("base_url, username, password, invitation, expected_alert", [
    ("https://dashboard.acen.http.321174.com/register", "mmkkook@thordata.com", "Zxs6412915@+", "5522", "Verify your email"),
])
def test_register_cs(base_url, username, password, invitation, expected_alert):
    driver = None
    try:
        driver = init_driver()
        alert_text = register(driver, base_url, username, password, invitation)
        print(f"期望的弹出框文本: '{expected_alert}', 实际获取到的弹出框文本: '{alert_text}'")
        assert expected_alert == alert_text, f"预期：'{expected_alert}'，实际：'{alert_text}'"
        print("注册成功预期=实际")
    except TimeoutException:
        raise AssertionError("操作超时：未找到页面元素或弹出框内容。")
    except Exception as e:
        raise AssertionError(f"测试失败，未处理的异常：{e}")
    finally:
        if driver:
            driver.quit()
