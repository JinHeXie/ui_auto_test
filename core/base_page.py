# core/base_page.py
"""
BasePage：页面对象的基础类（Web & App 通用）

职责：
- 管理 driver
- 提供通用的查找、点击、输入、等待、截图等方法
- 集成日志记录与 Allure 截图附件
"""

from __future__ import annotations

import os
import time
from typing import Any, Tuple, List, Optional

import allure
from allure_commons.types import AttachmentType

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.logger import get_logger
from utils.path_helper import join_project_path, ensure_dir_exists


Locator = Tuple[str, str]  # 例如 (By.ID, "username")


class BasePage:
    """
    所有页面对象（PO）的基类。

    Web 页面继承 WebBasePage，App 页面继承 AppBasePage，
    而 WebBasePage / AppBasePage 又都是继承自本类。
    """

    def __init__(self, driver: WebDriver, timeout: int = 10):
        """
        :param driver: Selenium 或 Appium driver 实例
        :param timeout: 默认显式等待超时时间（秒）
        """
        self.driver = driver
        self.timeout = timeout
        # logger 名称用类名，便于区分不同页面
        self.logger = get_logger(self.__class__.__name__)

    # ========== 元素查找与操作 ========== #

    def find(self, locator: Locator, timeout: Optional[int] = None) -> WebElement:
        """
        查找单个元素（带显式等待，直到元素可见）。

        :param locator: 元素定位器，如 (By.ID, "username")
        :param timeout: 超时时间（秒），不传则使用默认 timeout
        :return: WebElement
        """
        wait_time = timeout or self.timeout
        by, value = locator

        self.logger.debug(f"查找元素: by={by}, value={value}, timeout={wait_time}")
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located(locator)
            )
            return element
        except Exception as e:
            self.logger.error(f"查找元素失败: {locator}, 错误: {e}")
            # 失败时截一张图方便排查
            self.screenshot(name_prefix="find_failed")
            raise

    def finds(self, locator: Locator, timeout: Optional[int] = None) -> List[WebElement]:
        """
        查找多个元素（等待至少有一个元素出现）。

        :param locator: 元素定位器
        :param timeout: 超时时间（秒）
        :return: 元素列表（可能为空）
        """
        wait_time = timeout or self.timeout
        by, value = locator

        self.logger.debug(f"查找多个元素: by={by}, value={value}, timeout={wait_time}")
        try:
            elements = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_all_elements_located(locator)
            )
            return elements
        except Exception as e:
            self.logger.error(f"查找多个元素失败: {locator}, 错误: {e}")
            self.screenshot(name_prefix="finds_failed")
            raise

    def click(self, locator: Locator, timeout: Optional[int] = None) -> None:
        """
        点击某个元素（等待元素可点击）。

        :param locator: 元素定位器
        :param timeout: 超时时间（秒）
        """
        wait_time = timeout or self.timeout
        self.logger.info(f"点击元素: {locator}, timeout={wait_time}")

        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.element_to_be_clickable(locator)
            )
            element.click()
        except Exception as e:
            self.logger.error(f"点击元素失败: {locator}, 错误: {e}")
            self.screenshot(name_prefix="click_failed")
            raise

    def input_text(
        self,
        locator: Locator,
        text: str,
        clear: bool = True,
        timeout: Optional[int] = None,
    ) -> None:
        """
        向输入框输入文本。

        :param locator: 元素定位器
        :param text: 要输入的文字
        :param clear: 输入前是否先清空
        :param timeout: 超时时间（秒）
        """
        self.logger.info(f"输入文本: locator={locator}, text={text!r}")
        element = self.find(locator, timeout)
        try:
            if clear:
                element.clear()
            element.send_keys(text)
        except Exception as e:
            self.logger.error(f"输入文本失败: locator={locator}, text={text!r}, 错误: {e}")
            self.screenshot(name_prefix="input_failed")
            raise

    def get_text(self, locator: Locator, timeout: Optional[int] = None) -> str:
        """
        获取元素的文本内容。

        :param locator: 元素定位器
        :param timeout: 超时时间（秒）
        :return: 文本
        """
        element = self.find(locator, timeout)
        text = element.text
        self.logger.info(f"获取元素文本: locator={locator}, text={text!r}")
        return text

    # ========== 显式等待封装 ========== #

    def wait_visible(self, locator: Locator, timeout: Optional[int] = None) -> WebElement:
        """
        等待元素可见。

        :param locator: 元素定位器
        :param timeout: 超时时间（秒）
        :return: WebElement
        """
        wait_time = timeout or self.timeout
        self.logger.debug(f"等待元素可见: {locator}, timeout={wait_time}")
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located(locator)
            )
        except Exception as e:
            self.logger.error(f"等待元素可见失败: {locator}, 错误: {e}")
            self.screenshot(name_prefix="wait_visible_failed")
            raise

    def wait_clickable(self, locator: Locator, timeout: Optional[int] = None) -> WebElement:
        """
        等待元素可点击。

        :param locator: 元素定位器
        :param timeout: 超时时间（秒）
        :return: WebElement
        """
        wait_time = timeout or self.timeout
        self.logger.debug(f"等待元素可点击: {locator}, timeout={wait_time}")
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.element_to_be_clickable(locator)
            )
        except Exception as e:
            self.logger.error(f"等待元素可点击失败: {locator}, 错误: {e}")
            self.screenshot(name_prefix="wait_clickable_failed")
            raise

    # ========== 截图 & Allure 集成 ========== #

    def screenshot(self, name_prefix: str = "screenshot") -> str:
        """
        截图并保存到 reports/screenshots 下，同时附加到 Allure 报告。

        :param name_prefix: 文件名前缀，用于区分不同场景，如 "click_failed"
        :return: 截图文件的绝对路径
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_name = f"{name_prefix}_{timestamp}.png"
        # 截图目录：reports/screenshots/
        screenshot_dir = join_project_path("reports", "screenshots")
        ensure_dir_exists(screenshot_dir)
        file_path = os.path.join(screenshot_dir, file_name)

        try:
            # 保存到文件
            self.driver.save_screenshot(file_path)
            self.logger.info(f"截图已保存: {file_path}")

            # 添加到 Allure 报告
            try:
                png_bytes = self.driver.get_screenshot_as_png()
                allure.attach(
                    png_bytes,
                    name=file_name,
                    attachment_type=AttachmentType.PNG,
                )
            except Exception as e:
                self.logger.warning(f"截图添加到 Allure 失败: {e}")

        except Exception as e:
            self.logger.error(f"截图失败: {e}")

        return file_path
