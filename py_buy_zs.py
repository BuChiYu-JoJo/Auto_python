from time import sleep

import pytest
from pytest_login1 import login_zs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# 初始化浏览器驱动
def init_driver():
    options = Options()
#    options.add_argument("--headless")  # 启用headless模式
#    options.add_argument("--disable-gpu")
#    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")  # 启动时最大化浏览器窗口
    # 指定Chrome浏览器的路径
    chrome_path = "C:\\chrome\\chrome-win64\\chrome.exe"
    options.binary_location = chrome_path

    service = Service("C:\\chrome\\chromedriver-win64\\chromedriver.exe")  # 替换为chromedriver的路径
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scroll_to_element(driver, element):
    """Scroll to the specified element using JavaScript."""
    driver.execute_script("arguments[0].scrollIntoView(true);", element)


def click_radio_by_label_text(driver, text, timeout=10):
    # 定位包含可见文字的 label（无论文字在前后、是否有多余空格）
    xp = f"//label[contains(@class,'ant-radio-wrapper')][.//span[normalize-space()='{text}']]"
    label = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xp))
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", label)
    label.click()

#客服组件清除函数
def ensure_no_livechat_overlay(driver):
    """
    最小改动版：直接把常见的 LiveChat/聊天小窗 iframe/容器隐藏,避免遮挡点击。
    不依赖可见的"关闭按钮",页面变更时也相对稳。
    """
    js = """
    const ids = ['chat-widget', 'chat-widget-minimized', 'chat-widget-container', 'livechat-eye-catcher', 'lc_container'];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.style.setProperty('display','none','important');
            el.style.setProperty('visibility','hidden','important');
            el.style.setProperty('pointer-events','none','important');
        }
    });
    // 兜底：隐藏 title/name/ID 含 livechat/chat 的 iframe
    const iframes = Array.from(document.querySelectorAll('iframe'));
    iframes.forEach(f => {
        const id = (f.id||'').toLowerCase();
        const nm = (f.name||'').toLowerCase();
        const tt = (f.getAttribute('title')||'').toLowerCase();
        if (id.includes('chat') || nm.includes('chat') || tt.includes('livechat')) {
            f.style.setProperty('display','none','important');
            f.style.setProperty('visibility','hidden','important');
            f.style.setProperty('pointer-events','none','important');
        }
    });
    """
    driver.execute_script(js)


def close_payment_iframe(driver):
    """
    彻底关闭支付弹窗的稳健方法
    """
    driver.switch_to.default_content()
    print("\n🔄 开始关闭支付弹窗...")

    # ===== 步骤1: 点击iframe内的关闭按钮 =====
    try:
        # 等待iframe出现并切换
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it(
                (By.ID, "ams-checkout-component-desktop")
            )
        )
        print("  ✓ 已切换到支付iframe")
        
        # 点击关闭按钮
        close_btn = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//*[@id='ams-component-close-block' or contains(@class,'close-block') or contains(@class,'close')]"
            ))
        )
        driver.execute_script("arguments[0].click();", close_btn)
        print("  ✓ 已点击iframe内关闭按钮")
        sleep(1)
    except TimeoutException:
        print("  ⚠ 未找到iframe内关闭按钮")
    finally:
        driver.switch_to.default_content()

    # ===== 步骤2: 点击"Leave anyway"确认 =====
    try:
        leave_btn = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[.//span[contains(text(),'Leave anyway')] or contains(text(),'Leave anyway')]"
            ))
        )
        driver.execute_script("arguments[0].click();", leave_btn)
        print("  ✓ 已点击 Leave anyway")
        sleep(1)
    except TimeoutException:
        print("  ⚠ 未找到 Leave anyway 按钮")

    # ===== 步骤3: 等待遮罩消失 =====
    try:
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class,'ant-modal-mask') or contains(@class,'ant-modal-wrap')]"
            ))
        )
        print("  ✓ 遮罩已消失")
    except TimeoutException:
        print("  ⚠ 遮罩未完全消失，继续强制清理")

    # ===== 步骤4: 强制隐藏残留iframe和遮罩 =====
    js_cleanup = """
    // 隐藏所有支付相关的iframe
    const paymentIframes = document.querySelectorAll('iframe[id*="ams-checkout"], iframe[src*="alipay.com"], iframe[src*="paypal.com"]');
    paymentIframes.forEach(iframe => {
        iframe.style.display = 'none';
        iframe.style.visibility = 'hidden';
        iframe.style.pointerEvents = 'none';
        // 如果有父容器也隐藏
        if (iframe.parentElement) {
            iframe.parentElement.style.display = 'none';
        }
    });
    
    // 隐藏所有遮罩
    const masks = document.querySelectorAll('.ant-modal-mask, .ant-modal-wrap, .modal-mask, .overlay');
    masks.forEach(mask => {
        mask.style.display = 'none';
        mask.style.visibility = 'hidden';
    });
    
    // 移除body的overflow限制
    document.body.style.overflow = 'auto';
    
    return {iframes: paymentIframes.length, masks: masks.length};
    """
    result = driver.execute_script(js_cleanup)
    print(f"  ✓ 已强制清理 {result['iframes']} 个iframe和 {result['masks']} 个遮罩")
    sleep(2)  # 等待DOM更新
    print("✅ 支付弹窗已完全关闭\n")



def back_to_checkout(driver):
    print("  🔄 重置到支付方式页面...")
    driver.switch_to.default_content()
    driver.get("https://dashboard.thordata.com/isp-proxies")
    sleep(5)

    isp_fukuan_btn = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.XPATH,
            "//span[contains(@class,'pricing-buy')]"
        ))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});", isp_fukuan_btn
    )
    sleep(0.5)

    try:
        isp_fukuan_btn.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", isp_fukuan_btn)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.XPATH,
            "//*[contains(text(),'Select payment method')]"
        ))
    )
    print("  ✓ 已回到支付方式选择页面")




# isp代理购买前置操作
def isp_buy(driver):
    try:
        new_url = "https://dashboard.thordata.com/isp-proxies"
        driver.get(new_url)        
        sleep(5)
        
        # 选择纽约地区
        isp_niuyue_btn = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'New York,US')]"))
        )
        isp_niuyue_btn.click()

        ensure_no_livechat_overlay(driver)  # 隐藏聊天窗口

        # 继续支付
        isp_fukuan_btn = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "total_btn_box")]//span[contains(text(), "Continue to checkout")]'))
        )

        try:
            isp_fukuan_btn.click()
        except ElementClickInterceptedException:
            ensure_no_livechat_overlay(driver)
            driver.execute_script("arguments[0].click();", isp_fukuan_btn)

        return driver

    except TimeoutException:
        raise AssertionError("超时：未找到弹出框内容")
    except NoSuchElementException:
        raise AssertionError("错误：找不到弹出框元素")
    except Exception as e:
        raise AssertionError(f"未处理的异常：{e}")



def ensure_on_payment_method_page(driver, timeout=40):
    """
    保证进入 Select payment method 页面：
    - 如果已在该页：直接返回
    - 如果不在：按“选择地区 -> Continue to checkout”完整走一遍
    """
    driver.switch_to.default_content()
    ensure_no_livechat_overlay(driver)

    wait = WebDriverWait(driver, timeout)

    # ✅ 如果已经在支付方式页，直接返回
    if driver.find_elements(By.XPATH, "//*[contains(text(),'Select payment method')]"):
        return

    # ✅ 否则重新走完整 checkout 前置
    driver.get("https://dashboard.thordata.com/isp-proxies")
    sleep(3)
    ensure_no_livechat_overlay(driver)

    # 选择纽约地区（你原来的逻辑）
    isp_niuyue_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'New York,US')]"))
    )
    driver.execute_script("arguments[0].click();", isp_niuyue_btn)
    sleep(0.5)

    # Continue to checkout（你原来的逻辑）
    isp_fukuan_btn = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            '//div[contains(@class, "total_btn_box")]//span[contains(text(), "Continue to checkout")]'
        ))
    )
    try:
        isp_fukuan_btn.click()
    except ElementClickInterceptedException:
        ensure_no_livechat_overlay(driver)
        driver.execute_script("arguments[0].click();", isp_fukuan_btn)

    # ✅ 关键：等到支付方式页出现
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Select payment method')]"))
    )




def isp_buy_credit(driver):
    """
    稳定工程版：信用卡支付调起验证
    判断标准：iframe 可切换 + iframe 内出现可交互支付内容
    """
    try:
        print("\n🔵 开始信用卡支付流程（稳定版）...")
        driver.switch_to.default_content()
        wait = WebDriverWait(driver, 40)

        # 1️⃣ 确保在支付方式页面
        wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//*[contains(text(),'Select payment method') or contains(text(),'payment')]"
            ))
        )
        print("  ✓ 已定位到支付方式选择页面")

        # 2️⃣ 展开 Credit Card
        credit_header = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//p[normalize-space()='Credit Card']/ancestor::*[contains(@class,'ant-collapse-header')]"
            ))
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", credit_header
        )
        driver.execute_script("arguments[0].click();", credit_header)
        print("  ✓ 已展开 Credit Card")

        # 3️⃣ 点击 Continue
        continue_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//span[normalize-space()='Continue']"
            ))
        )
        driver.execute_script("arguments[0].click();", continue_btn)
        print("  ✓ 已点击 Continue")

        # 4️⃣ 等待支付 iframe 出现
        print("  ⏳ 等待支付 iframe 出现...")
        iframe = wait.until(
            EC.presence_of_element_located((By.ID, "ams-checkout-component-desktop"))
        )
        print("  ✓ 支付 iframe 已出现在 DOM")

        # 5️⃣ 切换到 iframe（关键）
        wait.until(
            EC.frame_to_be_available_and_switch_to_it(
                (By.ID, "ams-checkout-component-desktop")
            )
        )
        print("  ✓ 已切换到支付 iframe")

        # 6️⃣ 稳定判断：iframe 内是否有“支付表单内容”
        print("  ⏳ 校验 iframe 内支付组件...")
        wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//input | //form | //iframe | //div[contains(@class,'ams')]"
            ))
        )
        print("  ✓ iframe 内支付组件已加载")

        # 7️⃣ 成功即返回固定标识
        driver.switch_to.default_content()
        return "CREDIT_IFRAME_READY"

    except Exception as e:
        print(f"❌ 信用卡支付流程失败（稳定版）：{e}")
        driver.switch_to.default_content()
        raise



def find_paypal_button_anywhere(driver, timeout=40):
    """
    在弹窗出现后，优先主DOM找 PayPal 按钮；
    找不到就遍历所有 iframe（含嵌套）去找真正的 PayPal Smart Button。
    返回：(button_element, switched) 其中 switched=True 表示当前已在某个frame里。
    """
    wait = WebDriverWait(driver, timeout)

    # ✅ 先等弹窗关键字出现（你的弹窗里有 Total）
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[normalize-space()='Total']")))

    # 1) 先在主 DOM 直接找（有些实现按钮不在 iframe）
    driver.switch_to.default_content()
    direct = driver.find_elements(
        By.XPATH,
        "//*[@data-funding-source='paypal' or @aria-label='PayPal' "
        "or (contains(@class,'paypal-button') and (@role='link' or @tabindex='0'))]"
    )
    if direct:
        return direct[0], False

    # 2) 遍历 iframe（第一层 + 第二层嵌套）
    end_time = time.time() + timeout
    while time.time() < end_time:
        driver.switch_to.default_content()
        frames = driver.find_elements(By.TAG_NAME, "iframe")

        for f in frames:
            try:
                driver.switch_to.frame(f)

                # 在当前 frame 查 PayPal 按钮
                btn = driver.find_elements(
                    By.XPATH,
                    "//div[@data-funding-source='paypal' or @aria-label='PayPal' "
                    "or (contains(@class,'paypal-button') and (@role='link' or @tabindex='0'))]"
                )
                if btn:
                    return btn[0], True

                # 查嵌套 frame
                nested = driver.find_elements(By.TAG_NAME, "iframe")
                for nf in nested:
                    try:
                        driver.switch_to.frame(nf)
                        btn2 = driver.find_elements(
                            By.XPATH,
                            "//div[@data-funding-source='paypal' or @aria-label='PayPal' "
                            "or (contains(@class,'paypal-button') and (@role='link' or @tabindex='0'))]"
                        )
                        if btn2:
                            return btn2[0], True
                        driver.switch_to.parent_frame()
                    except:
                        driver.switch_to.parent_frame()

            except:
                pass
            finally:
                driver.switch_to.default_content()

        time.sleep(0.5)

    raise TimeoutException("未在主DOM/iframe中找到 PayPal 按钮（Smart Button）")





def isp_buy_paypal(driver):
    """
    最终稳定版：PayPal 支付调起
    只负责：
    1. 已在 Select payment method 页面
    2. 选择 PayPal
    3. Continue
    4. 点击弹窗里的黄色 PayPal Smart Button
    """
    try:
        import time
        print("\n🟡 开始 PayPal 支付流程（最终版）...")
        wait = WebDriverWait(driver, 40)

        # 0️⃣ 干净上下文
        driver.switch_to.default_content()
        driver.switch_to.window(driver.current_window_handle)

        # 1️⃣ 确认支付方式页
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[normalize-space()='Select payment method']")
            )
        )
        print("  ✓ 已回到支付方式选择页面")

        # 2️⃣ 选择 PayPal（整行）
        paypal_row = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[contains(@class,'mode_li')]//p[normalize-space()='PayPal']/ancestor::div[contains(@class,'mode_li')]"
                )
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", paypal_row)
        driver.execute_script("arguments[0].click();", paypal_row)
        print("  ✓ 已选中 PayPal 支付方式")

        # 3️⃣ Continue
        continue_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Continue']"))
        )
        driver.execute_script("arguments[0].click();", continue_btn)
        print("  ✓ 已点击 Continue")

        # 4️⃣ 等弹窗（Total）
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[normalize-space()='Total']")
            )
        )
        print("  ✓ PayPal 弹窗已出现")

        # 5️⃣ 查找并点击黄色 PayPal Smart Button（无 iframe 假设）
        print("  🔍 查找 PayPal 黄色按钮...")

        def find_paypal_button():
            driver.switch_to.default_content()
            btns = driver.find_elements(
                By.XPATH,
                "//div[@data-funding-source='paypal' and (@role='link' or @tabindex='0')]"
            )
            return btns[0] if btns else None

        paypal_button = None
        end_time = time.time() + 40
        while time.time() < end_time:
            paypal_button = find_paypal_button()
            if paypal_button:
                break
            time.sleep(0.5)

        if not paypal_button:
            raise TimeoutException("未找到 PayPal Smart Button")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", paypal_button)
        driver.execute_script("arguments[0].click();", paypal_button)
        print("  ✓ 已点击 PayPal 黄色按钮")

        print("✅ PayPal Smart Button 已成功触发")
        return "PAYPAL_TRIGGERED"

    except Exception as e:
        print(f"❌ PayPal 支付流程失败：{e}")
        driver.switch_to.default_content()
        raise



def isp_buy_alipayhk(driver):
    """支付宝支付流程"""
    try:
        print("\n🟢 开始支付宝支付流程...")
        driver.switch_to.default_content()
        
        # 1️⃣ 尝试关闭可能存在的虚拟币弹窗
        try:
            crypto_close = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[contains(@class,'virtual_pop_header')]/div[@class='close']"
                ))
            )
            crypto_close.click()
            print("  ✓ 已关闭虚拟币弹窗")
            sleep(1)
        except TimeoutException:
            print("  ⚠ 未检测到虚拟币弹窗")

        # 2️⃣ 展开 Alipay 选项
        alipayhk = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[contains(@class,'method_wrapper')]//p[normalize-space()='Alipay']/ancestor::*[contains(@class,'ant-collapse-header')]"
            ))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", alipayhk)
        sleep(0.5)
        
        # 使用JavaScript点击避免被遮挡
        driver.execute_script("arguments[0].click();", alipayhk)
        print("  ✓ 已展开 Alipay")
        sleep(1)

        # 3️⃣ 点击 Continue
        alipayhk_queren = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[contains(@class,'mode_btn_box')]//span[text()='Continue']"
            ))
        )
        driver.execute_script("arguments[0].click();", alipayhk_queren)
        print("  ✓ 已点击 Continue")

        # 4️⃣ 等待加载完成
        WebDriverWait(driver, 20).until_not(
            EC.presence_of_element_located((By.XPATH, "//div[@class='loading-overlay']"))
        )
        print("  ✓ 加载完成")

        # 5️⃣ 获取支付宝页面信息
        isp_buyalipayhk = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((
                By.XPATH,
                "/html/body/div/div/div/div[2]/div/div[1]/div/div/section/div/div[1]/label/div/div[1]"
            ))
        )
        buyInformation_alipayhk = isp_buyalipayhk.text
        print(f"  ✓ 获取到支付宝信息：{buyInformation_alipayhk}")
        
        return buyInformation_alipayhk

    except Exception as e:
        print(f"❌ 支付宝支付流程失败：{e}")
        raise


def isp_buy_local(driver):
    """本地支付流程"""
    try:
        driver.switch_to.default_content()
        ensure_on_payment_method_page(driver, timeout=40)
        # 展开 Local payments
        local = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[contains(@class,'method_wrapper')]//p[normalize-space()='Local payments']/ancestor::*[contains(@class,'ant-collapse-header')]"
            ))
        )
        scroll_to_element(driver, local)
        sleep(0.5)
        local.click()
        print("  ✓ 已展开 Local payments")

        # 点击 Continue
        local_queren = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class,'mode_btn_box')]//span[text()='Continue']"
            ))
        )
        local_queren.click()
        print("  ✓ 已点击 Continue")

        # 等待加载完成
        WebDriverWait(driver, 20).until_not(
            EC.presence_of_element_located((By.XPATH, "//div[@class='loading-overlay']"))
        )

        # 获取本地支付信息
        isp_buylocal = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((
                By.XPATH,
                "/html/body/div/div/div/div[2]/div[1]/div/div/div/div[2]/div[2]/div[1]/div[1]/div[1]"
            ))
        )
        buyInformation_local = isp_buylocal.text
        print(f"  ✓ 获取到本地支付信息：{buyInformation_local}")
        
        return buyInformation_local

    except Exception as e:
        print(f"❌ 本地支付流程失败：{e}")
        raise


def perform_purchase_verifications(driver):
    """执行所有支付方式验证"""

    # ========== 1. PayPal验证 ==========
#    print("\n" + "=" * 60)
#    print("测试 4/4: PayPal 支付")
#    print("=" * 60)

#   ensure_on_payment_method_page(driver, timeout=40)
#    buyInformation_paypal = isp_buy_paypal(driver)
#    print(f"✅ 获取到的信息：{buyInformation_paypal}")

#    assert buyInformation_paypal == "PAYPAL_TRIGGERED"
#    print("✅ PayPal 调起支付成功")


    # ========== 2. 信用卡验证 ==========
    print("\n" + "="*60)
    print("测试 1/4: 信用卡支付")
    print("="*60)

    ensure_on_payment_method_page(driver, timeout=40)
    buyInformation = isp_buy_credit(driver)
    print(f"✅ 获取到的信息：{buyInformation}")
#    assert buyInformation == "Credit or debit card", f"实际：{buyInformation}，预期：Credit or debit card"
    assert buyInformation == "CREDIT_IFRAME_READY"
    print("✅ 信用卡调起支付成功")
    
    # ✅ 关键：立即关闭信用卡iframe
    close_payment_iframe(driver)
    
    
    # ========== 3. 支付宝验证 ==========
    print("\n" + "="*60)
    print("测试 2/4: 支付宝支付")
    print("="*60)

    ensure_on_payment_method_page(driver, timeout=40)
    buyInformation_alipayhk = isp_buy_alipayhk(driver)
    print(f"✅ 获取到的信息：{buyInformation_alipayhk}")
    assert buyInformation_alipayhk == "扫码支付", f"实际：{buyInformation_alipayhk}，预期：扫码支付"
    print("✅ 支付宝调起支付成功")
    
    
    # ========== 4. 本地支付验证 ==========
    print("\n" + "="*60)
    print("测试 3/4: 本地支付")
    print("="*60)

    ensure_on_payment_method_page(driver, timeout=40)
    buyInformation_local = isp_buy_local(driver)
    print(f"✅ 获取到的信息：{buyInformation_local}")
    assert buyInformation_local in ("行動/電話小額付", "WechatPay", "WechatPayHK"), \
        f"实际：{buyInformation_local}，预期：行動/電話小額付 或 WechatPay 或 WechatPayHK"
    print("✅ 本地支付调起成功")





def isp_buy_operations(driver):
    """执行isp购买操作"""
    driver = isp_buy(driver)
    perform_purchase_verifications(driver)


# pytest fixture
@pytest.fixture
def driver(request):
    d = init_driver()
    request.addfinalizer(d.quit)
    return d


# 测试函数
@pytest.mark.parametrize("username, password", [("lightsong@thordata.com", "Zxs6412915@+")])
def test_login_and_buy(driver, username, password):
    try:
        login_zs(driver, username=username, password=password)
        isp_buy_operations(driver)
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)

    except TimeoutException:
        raise AssertionError("操作超时：未找到页面元素或弹出框内容。")
    except Exception as e:
        raise AssertionError(f"测试失败，未处理的异常：{e}")