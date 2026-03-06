"""
页面对象 - 注册页面
"""

from playwright.sync_api import Page


class RegisterPage:
    """注册页面对象"""
    
    def __init__(self, page: Page):
        self.page = page
        
        # 页面元素定位器
        self.email_input = 'input[placeholder="邮箱地址"]'
        self.password_input = 'input[placeholder="密码"]'
        self.invite_code_input = 'input[placeholder="邀请码"]'
        self.register_button = '.login-container-body-E-btn'
        self.checkbox = '.check_p'
        
        # 激活提示关键词
        self.activation_keywords = [
            "验证您的邮箱地址",
            "确认链接",
            "确认邮件",
            "激活",
            "验证邮箱",
            "发送确认"
        ]
    
    def navigate(self, url: str = "https://dashboard.thordata.com/zh/register"):
        """导航到注册页"""
        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        self.page.wait_for_timeout(3000)
    
    def fill_email(self, email: str):
        """填写邮箱"""
        self.page.fill(self.email_input, email)
    
    def fill_password(self, password: str):
        """填写密码"""
        self.page.fill(self.password_input, password)
    
    def fill_invite_code(self, code: str):
        """填写邀请码"""
        if code:
            self.page.fill(self.invite_code_input, code)
    
    def check_agreement(self):
        """勾选用户协议"""
        try:
            self.page.click(self.checkbox)
            return True
        except:
            # 尝试其他方式
            self.page.evaluate('''() => {
                const labels = document.querySelectorAll('label');
                for (const label of labels) {
                    if (label.innerText.includes('我同意')) {
                        const checkbox = label.querySelector('input[type="checkbox"]');
                        if (checkbox) checkbox.click();
                    }
                }
            }''')
            return True
    
    def click_register(self):
        """点击注册按钮"""
        self.page.click(self.register_button)
    
    def register(self, email: str, password: str, invite_code: str = ""):
        """执行注册流程"""
        self.fill_email(email)
        self.fill_password(password)
        if invite_code:
            self.fill_invite_code(invite_code)
        self.check_agreement()
        self.click_register()
    
    def wait_for_result(self, timeout: int = 10000):
        """等待注册结果"""
        self.page.wait_for_timeout(timeout)
    
    def has_activation_hint(self) -> bool:
        """检查是否有邮箱激活提示"""
        page_text = self.page.content()
        return any(keyword in page_text for keyword in self.activation_keywords)
    
    def get_activation_message(self) -> str:
        """获取激活提示信息"""
        page_text = self.page.content()
        for keyword in self.activation_keywords:
            if keyword in page_text:
                # 尝试获取包含关键词的行
                lines = page_text.split('\n')
                for line in lines:
                    if keyword in line:
                        return line.strip()
        return ""
    
    def is_register_success(self) -> bool:
        """检查注册是否成功"""
        # 检查是否跳转到了 dashboard（排除 register 页面）
        current_url = self.page.url
        if "dashboard" in current_url and "register" not in current_url:
            return True
        
        # 或者检查是否有激活提示
        return self.has_activation_hint()
    
    def get_error_message(self) -> str:
        """获取错误信息"""
        error_keywords = ["错误", "失败", "已存在", "格式错误"]
        page_text = self.page.content()
        
        for keyword in error_keywords:
            if keyword in page_text:
                lines = page_text.split('\n')
                for line in lines:
                    if keyword in line:
                        return line.strip()
        return ""
