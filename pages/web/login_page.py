# pages/web/login_page.py
"""
Web 登录页面 Page Object - 适配弹窗登录
"""
from __future__ import annotations

import time
from selenium.webdriver.common.by import By

from core.web_base_page import WebBasePage
from utils.slider_solver import SliderCaptchaSolver


class LoginPage(WebBasePage):
    """
    登录页面 PO - 适配你的demo页面

    注意：这里使用demo中的定位器，需要根据实际页面调整
    """

    # ========== 首页元素 ==========
    LOGIN_ENTRY_BUTTON = (By.XPATH, '/html/body/div[13]/div/section/section/header/div[1]/div[2]/button')

    # ========== 登录弹窗元素 ==========
    # 登录方式标签
    ACCOUNT_LOGIN_TAB = (By.XPATH, '/html/body/div[7]/div/div/div/div/div[2]/div/div[1]/div[2]')

    # 登录表单
    USERNAME_INPUT = (By.XPATH, '/html/body/div[7]/div/div/div/div/div[2]/div/form/div[1]/div/div/div/input')
    PASSWORD_INPUT = (By.XPATH, '/html/body/div[7]/div/div/div/div/div[2]/div/form/div[2]/div/div/div/input')
    AGREEMENT_CHECKBOX = (By.XPATH, '/html/body/div[7]/div/div/div/div/div[2]/div/label/span[1]/span')
    LOGIN_BUTTON = (By.XPATH, '/html/body/div[7]/div/div/div/div/div[2]/div/button')

    # ========== 验证码元素（根据demo） ==========
    CAPTCHA_BG_IMG = (By.CSS_SELECTOR, 'img.slide-verify-bg-img')
    CAPTCHA_GAP_IMG = (By.CSS_SELECTOR, 'img.slide-verify-slide-img')
    CAPTCHA_SLIDER = (By.CSS_SELECTOR, 'div.slide-verify-slider-mask-item')

    # ========== 错误提示 ==========
    ERROR_MESSAGE = (By.CSS_SELECTOR, '.error-message')  # 根据实际页面调整

    def __init__(self, driver):
        super().__init__(driver)
        self.captcha_solver = SliderCaptchaSolver(driver)
        self.logger.info("LoginPage 初始化完成")

    # ========== 页面导航方法 ========== #

    def open_home_page(self):
        """打开首页"""
        self.logger.info("打开首页")
        self.open_url("/")  # 使用配置的base_url
        return self

    def open_login_modal(self):
        """
        打开登录弹窗（从首页）

        步骤：
        1. 点击首页的登录按钮
        2. 切换到账号登录标签
        3. 等待弹窗加载完成
        """
        self.logger.info("打开登录弹窗")

        # 1. 打开首页（如果不在首页）
        if "ai/" not in self.current_url:
            self.open_home_page()
            time.sleep(2)
        time.sleep(3)
        # 2. 点击登录入口按钮
        try:
            # self.click(self.LOGIN_ENTRY_BUTTON)
            login_btn = self.find(self.LOGIN_ENTRY_BUTTON)
            self.execute_js("arguments[0].click();",login_btn)
            self.logger.info("点击登录入口按钮")
            time.sleep(3)
        except Exception as e:
            self.logger.error(f"点击登录入口失败: {e}")
            self.screenshot("login_entry_failed")
            raise

        # 3. 切换到账号登录标签
        try:
            self.click(self.ACCOUNT_LOGIN_TAB)
            self.logger.info("切换到账号登录标签")
            time.sleep(1)
        except Exception as e:
            self.logger.warning(f"切换到账号登录标签失败: {e}")
            # 可能默认就是账号登录，继续执行

        return self

    def open(self, use_modal=True):
        """
        打开登录页面

        Args:
            use_modal: True-通过弹窗登录，False-直接访问登录页
        """
        if use_modal:
            return self.open_login_modal()
        else:
            self.logger.info("直接打开登录页面")
            self.open_url("/login")
            return self

    # ========== 登录操作 ========== #

    def enter_credentials(self, username: str, password: str):
        """输入用户名和密码"""
        self.logger.info(f"输入用户名密码: {username}")

        self.input_text(self.USERNAME_INPUT, username)
        self.input_text(self.PASSWORD_INPUT, password)

        return self

    def check_agreement(self):
        """勾选同意协议"""
        try:
            self.click(self.AGREEMENT_CHECKBOX)
            self.logger.info("勾选同意协议")
        except Exception as e:
            self.logger.warning(f"勾选协议失败，可能已勾选: {e}")

        return self

    def click_login_button(self):
        """点击登录按钮"""
        self.logger.info("点击登录按钮")
        self.click(self.LOGIN_BUTTON)
        return self

    # ========== 验证码处理 ========== #

    def is_captcha_visible(self, timeout=5):
        """检查验证码是否可见"""
        try:
            self.wait_visible(self.CAPTCHA_BG_IMG, timeout=timeout)
            return True
        except:
            return False

    def solve_slider_captcha(self):
        """解决滑动验证码"""
        self.logger.info("开始处理滑动验证码")

        try:
            # 等待验证码元素加载
            self.wait_visible(self.CAPTCHA_BG_IMG, timeout=10)
            self.wait_visible(self.CAPTCHA_GAP_IMG, timeout=10)
            self.wait_visible(self.CAPTCHA_SLIDER, timeout=10)

            # 获取元素
            bg_img = self.find(self.CAPTCHA_BG_IMG)
            gap_img = self.find(self.CAPTCHA_GAP_IMG)
            slider = self.find(self.CAPTCHA_SLIDER)

            # 获取图片src
            bg_src = bg_img.get_attribute("src")
            gap_src = gap_img.get_attribute("src")

            if not bg_src or not gap_src:
                self.logger.error("无法获取验证码图片src")
                return False

            # 解决验证码
            success = self.captcha_solver.solve_captcha(bg_src, gap_src, slider)

            if success:
                self.logger.info("✅ 验证码解决成功")
                # 等待验证结果
                time.sleep(2)
                return True
            else:
                self.logger.warning("❌ 验证码解决失败")
                return False

        except Exception as e:
            self.logger.error(f"验证码处理失败: {e}")
            self.screenshot("captcha_error")
            return False

    # ========== 登录流程封装 ========== #

    def login(self, username: str, password: str, auto_handle_captcha=True):
        """
        完整的登录流程（适配demo）

        Args:
            username: 用户名
            password: 密码
            auto_handle_captcha: 是否自动处理验证码

        Returns:
            bool: 登录是否成功
        """
        self.logger.info(f"开始登录流程: {username}")

        try:
            # 1. 打开登录弹窗
            self.open_login_modal()

            # 2. 输入凭证
            self.enter_credentials(username, password)

            # 3. 勾选协议
            self.check_agreement()

            # 4. 点击登录按钮（触发验证码）
            self.click_login_button()

            # 5. 处理验证码（如果需要）
            if auto_handle_captcha:
                time.sleep(2)  # 等待验证码弹出

                if self.is_captcha_visible():
                    self.logger.info("检测到验证码，开始处理...")
                    captcha_success = self.solve_slider_captcha()

                    if not captcha_success:
                        self.logger.error("验证码处理失败，登录中止")
                        return False
                else:
                    self.logger.info("未检测到验证码，继续登录")

            # 6. 等待登录结果
            time.sleep(3)
            return self.is_login_success()

        except Exception as e:
            self.logger.error(f"登录流程异常: {e}")
            self.screenshot("login_error")
            return False

    def login_without_captcha(self, username: str, password: str):
        """不带验证码处理的登录（用于测试）"""
        self.logger.info(f"执行简单登录: {username}")

        self.open_login_modal()
        self.enter_credentials(username, password)
        self.check_agreement()
        self.click_login_button()

        # 不处理验证码，直接等待结果
        time.sleep(3)
        return self.is_login_success()

    # ========== 状态检查方法 ========== #

    def is_login_success(self):
        """检查是否登录成功"""
        try:
            # 检查是否有用户相关元素（根据实际页面调整）
            user_selectors = [
                (By.XPATH, "/html/body/div[13]/div/section/section/header/div[1]/div[2]/div[4]/div[1]/div[3]/span"),
                (By.XPATH, '//*[@id="outer-container"]/section/header/div[1]/div[2]/div[5]/div[1]/div/img')
            ]

            for selector in user_selectors:
                try:
                    elements = self.driver.find_elements(*selector)
                    if elements and elements[0].is_displayed():
                        self.logger.info(f"检测到用户元素，登录成功: {selector}")
                        return True
                except:
                    continue

            # 方法3：检查登录弹窗是否消失
            try:
                modal_element = self.driver.find_element(*self.LOGIN_BUTTON)
                if not modal_element.is_displayed():
                    self.logger.info("登录弹窗已关闭，可能登录成功")
                    return True
            except:
                self.logger.info("登录按钮元素不存在，可能登录成功")
                return True

            # 默认返回False
            return False

        except Exception as e:
            self.logger.error(f"检查登录状态失败: {e}")
            return False

    def get_error_message(self):
        """获取错误提示信息"""
        try:
            return self.get_text(self.ERROR_MESSAGE)
        except:
            return "未知错误"

    # ========== 辅助方法 ========== #

    def wait_for_captcha_and_solve(self, timeout=10):
        """等待验证码出现并解决"""
        self.logger.info(f"等待验证码出现，超时时间: {timeout}秒")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_captcha_visible(timeout=1):
                return self.solve_slider_captcha()
            time.sleep(0.5)

        self.logger.warning(f"等待{timeout}秒未检测到验证码")
        return False