# pages/app/android/login_page.py
"""
Android 登录页面 Page Object 示例

说明：
- 使用 AppBasePage 作为基类
- 元素定位使用 resource-id / xpath 等
"""

from __future__ import annotations

from selenium.webdriver.common.by import By  # Appium 也复用 By

from core.app_base_page import AppBasePage


class AndroidLoginPage(AppBasePage):
    """
    Android 登录页面 PO 示例。

    注意：以下 resource-id 为示例，请替换为你 App 的真实 id：
      - 用户名输入框 id: "com.example.dev:id/et_username"
      - 密码输入框 id: "com.example.dev:id/et_password"
      - 登录按钮 id: "com.example.dev:id/btn_login"
      - 错误 toast 文案：例如 "用户名或密码错误"
    """

    USERNAME_INPUT = (By.ID, "com.example.dev:id/et_username")
    PASSWORD_INPUT = (By.ID, "com.example.dev:id/et_password")
    LOGIN_BUTTON = (By.ID, "com.example.dev:id/btn_login")

    def __init__(self, driver):
        super().__init__(driver)

    def login(self, username: str, password: str):
        """
        执行 App 登录操作。
        """
        self.logger.info(f"[Android] 执行登录操作: username={username!r}")
        self.input_text(self.USERNAME_INPUT, username)
        self.input_text(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)

    def get_error_toast(self, expected_text: str, timeout: int = 5) -> str:
        """
        通过 toast 查找登录失败提示，返回实际 toast 文案。

        :param expected_text: 预期包含的文本片段
        :param timeout: 超时时间
        :return: 实际 toast 文案（如果找到），否则抛异常
        """
        element = self.find_toast(expected_text, timeout=timeout)
        toast_text = element.text
        self.logger.info(f"[Android] 获取到的 toast 文案: {toast_text!r}")
        return toast_text
