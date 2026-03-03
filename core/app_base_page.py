# core/app_base_page.py
"""
AppBasePage：App 页面基础类（Android / iOS）

职责：
- 继承 BasePage，增加 App 特有操作：
  - 返回键
  - 各方向滑动
  - 查找 toast 等
"""

from __future__ import annotations

from typing import Optional

from appium.webdriver.webdriver import WebDriver as AppiumWebDriver

from core.base_page import BasePage
from core.logger import get_logger


class AppBasePage(BasePage):
    """
    App 页面对象基类，Android / iOS 页面均可继承此类。
    """

    def __init__(self, driver: AppiumWebDriver, timeout: int = 10):
        super().__init__(driver, timeout)
        self.logger = get_logger(self.__class__.__name__)

    # ========== 基本导航操作 ========== #

    def back(self) -> None:
        """返回上一页（系统返回键）。"""
        self.logger.info("执行返回操作")
        self.driver.back()

    # ========== 滑动操作（简单实现版） ========== #

    def _get_window_size(self):
        """
        获取屏幕尺寸，返回 (width, height)。
        """
        size = self.driver.get_window_size()
        return size["width"], size["height"]

    def swipe_up(self, duration: int = 800) -> None:
        """向上滑动（从下往上）。"""
        width, height = self._get_window_size()
        start_x = width * 0.5
        start_y = height * 0.8
        end_x = width * 0.5
        end_y = height * 0.2

        self.logger.info(
            f"向上滑动: start=({start_x}, {start_y}), end=({end_x}, {end_y}), duration={duration}"
        )
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)

    def swipe_down(self, duration: int = 800) -> None:
        """向下滑动（从上往下）。"""
        width, height = self._get_window_size()
        start_x = width * 0.5
        start_y = height * 0.2
        end_x = width * 0.5
        end_y = height * 0.8

        self.logger.info(
            f"向下滑动: start=({start_x}, {start_y}), end=({end_x}, {end_y}), duration={duration}"
        )
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)

    def swipe_left(self, duration: int = 800) -> None:
        """向左滑动（从右往左）。"""
        width, height = self._get_window_size()
        start_x = width * 0.8
        end_x = width * 0.2
        y = height * 0.5

        self.logger.info(
            f"向左滑动: start=({start_x}, {y}), end=({end_x}, {y}), duration={duration}"
        )
        self.driver.swipe(start_x, y, end_x, y, duration)

    def swipe_right(self, duration: int = 800) -> None:
        """向右滑动（从左往右）。"""
        width, height = self._get_window_size()
        start_x = width * 0.2
        end_x = width * 0.8
        y = height * 0.5

        self.logger.info(
            f"向右滑动: start=({start_x}, {y}), end=({end_x}, {y}), duration={duration}"
        )
        self.driver.swipe(start_x, y, end_x, y, duration)

    # ========== Toast 查找（简单示例） ========== #

    def find_toast(self, text: str, timeout: Optional[int] = 5):
        """
        查找包含指定文本的 toast 提示。

        注意：实际效果依赖于 Appium 配置，某些版本可能需要特定的 automationName 配置。

        :param text: toast 中包含的文本片段
        :param timeout: 超时时间（秒）
        :return: WebElement（如果找到），否则抛异常
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        xpath = f"//*[contains(@text,'{text}')]"
        self.logger.info(f"查找 toast: text={text!r}, xpath={xpath}, timeout={timeout}")

        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element
        except Exception as e:
            self.logger.error(f"查找 toast 失败: text={text!r}, 错误: {e}")
            self.screenshot(name_prefix="toast_not_found")
            raise
