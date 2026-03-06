"""
页面对象 - 支付页面
"""

from playwright.sync_api import Page


class PaymentPage:
    """支付页面对象"""
    
    def __init__(self, page: Page):
        self.page = page
        
        # 定价页URL（公开页面）
        self.pricing_url = "https://www.thordata.com/zh/pricing"
        
        # 支付方式选择器
        self.credit_card_option = 'text=信用卡'
        self.alipay_option = 'text=支付宝'
        self.wechat_option = 'text=微信支付'
        self.paypal_option = 'text=PayPal'
        
        # 购买按钮
        self.buy_button = 'text=购买'
        
    def navigate(self):
        """导航到定价页（公开页面）"""
        self.page.goto(self.pricing_url, wait_until="domcontentloaded", timeout=60000)
        self.page.wait_for_timeout(3000)
    
    def click_buy(self):
        """点击购买按钮"""
        buttons = self.page.locator(self.buy_button).all()
        if buttons:
            buttons[0].click()
            return True
        return False
        
        # 支付弹窗/iframe
        self.stripe_iframe = 'iframe[class*="stripe"]'
        self.alipay_frame = 'iframe[class*="alipay"]'
        
    def select_credit_card(self):
        """选择信用卡支付"""
        # 查找信用卡选项 - 可能是一个label或div
        options = self.page.locator('text=信用卡').all()
        for opt in options:
            if opt.is_visible():
                opt.click()
                return True
        return False
    
    def select_alipay(self):
        """选择支付宝支付"""
        options = self.page.locator('text=支付宝').all()
        for opt in options:
            if opt.is_visible():
                opt.click()
                return True
        return False
    
    def select_wechat(self):
        """选择微信支付"""
        options = self.page.locator('text=微信').all()
        for opt in options:
            if opt.is_visible():
                opt.click()
                return True
        return False
    
    def is_stripe_popup_present(self) -> bool:
        """检查是否出现Stripe支付弹窗"""
        # Stripe通常在iframe中
        try:
            iframes = self.page.locator('iframe').all()
            return len(iframes) > 0
        except:
            return False
    
    def is_alipay_popup_present(self) -> bool:
        """检查是否出现支付宝跳转页面"""
        current_url = self.page.url
        # 支付宝会跳转到外部页面
        return 'alipay' in current_url.lower() or 'alipay.com' in current_url
    
    def wait_for_payment_popup(self, timeout: int = 10000) -> bool:
        """等待支付弹窗出现"""
        try:
            # 检查是否有弹窗或iframe出现
            self.page.wait_for_timeout(2000)
            
            # 检查URL变化（支付宝跳转）
            if 'alipay' in self.page.url.lower():
                return True
            
            # 检查iframe
            iframes = self.page.locator('iframe').all()
            if len(iframes) > 0:
                return True
                
            return False
        except:
            return False
