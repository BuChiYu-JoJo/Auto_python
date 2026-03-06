"""
页面对象 - 登录页面
"""

from playwright.sync_api import Page


class LoginPage:
    """登录页面对象"""
    
    def __init__(self, page: Page):
        self.page = page
        
        # 页面元素定位器 - 根据实际页面结构调整
        self.username_input = '#email'
        self.password_input = '#psw'
        self.login_button = 'div:has-text("登录"):right-of(input)'
        self.success_popup = 'text=登录成功'
        self.captcha_container = '.geetest_panel'
        self.error_message = '.ant-message-error'
    
    def navigate(self, url: str):
        """导航到登录页"""
        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        self.page.wait_for_timeout(3000)  # 等待页面稳定
    
    def login(self, username: str, password: str):
        """执行登录操作"""
        # 输入用户名
        self.page.fill(self.username_input, username)
        
        # 输入密码
        self.page.fill(self.password_input, password)
        
        # 点击登录按钮
        login_btn = self.page.locator('div:has-text("登录")').last
        login_btn.click()
    
    def wait_for_success_popup(self, timeout: int = 15000):
        """等待登录成功弹窗"""
        try:
            self.page.wait_for_selector(
                self.success_popup, 
                timeout=timeout,
                state='visible'
            )
            return True
        except Exception:
            return False
    
    def is_captcha_present(self) -> bool:
        """检查是否出现验证码"""
        try:
            # 检查验证码相关元素
            captcha_elements = self.page.locator('.geetest_panel, .geetest_wrap, [class*="geetest"]').all()
            return len(captcha_elements) > 0
        except Exception:
            return False
    
    def get_error_message(self) -> str:
        """获取错误信息"""
        try:
            return self.page.locator(self.error_message).text_content()
        except Exception:
            return ""
    
    def is_login_successful(self) -> bool:
        """检查是否登录成功"""
        return self.wait_for_success_popup()
