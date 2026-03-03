# core/web_base_page.py
"""
WebBasePage：Web 页面基础类

职责：
- 继承 BasePage，增加 Web 特有操作：
  - 打开 URL
  - 获取当前 URL / 标题
  - 切换窗口 / iframe
  - 执行 JS 脚本 等
"""

from __future__ import annotations

from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver

from core.base_page import BasePage
from core.logger import get_logger
from core.config_loader import get_web_config


class WebBasePage(BasePage):
    """
    Web 页面对象基类，所有 Web 端 PO 继承自此类。
    """

    def __init__(self, driver: WebDriver, timeout: int = 10):
        super().__init__(driver, timeout)
        self.logger = get_logger(self.__class__.__name__)
        # 从 web_env.yaml 中获取 base_url，方便 open_url 使用
        web_conf = get_web_config()
        self.base_url: str = web_conf.get("base_url", "")

    # ========== URL & 页面导航 ========== #

    def open_url(self, path: str = "") -> None:
        """
        打开页面。

        :param path: URL 路径部分，例如 "/login"；
                     如果传入的是完整 URL（以 http 开头），则直接使用。
        """
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            url = self.base_url.rstrip("/") + "/" + path.lstrip("/")

        self.logger.info(f"打开 URL: {url}")
        self.driver.get(url)

    @property
    def current_url(self) -> str:
        """获取当前页面 URL。"""
        url = self.driver.current_url
        self.logger.debug(f"当前 URL: {url}")
        return url

    @property
    def title(self) -> str:
        """获取当前页面标题。"""
        title = self.driver.title
        self.logger.debug(f"当前页面标题: {title}")
        return title

    # ========== 窗口 / frame 切换 ========== #

    def switch_to_window(self, index: int = -1) -> None:
        """
        切换到指定索引的窗口句柄。

        :param index: 窗口索引，默认 -1 表示最新打开的窗口。
        """
        handles = self.driver.window_handles
        if not handles:
            self.logger.warning("当前无任何窗口句柄")
            return

        if index < 0:
            index = len(handles) - 1

        if index >= len(handles):
            self.logger.error(
                f"切换窗口失败：index={index} 超出范围，当前窗口数={len(handles)}"
            )
            return

        handle = handles[index]
        self.logger.info(f"切换到窗口: index={index}, handle={handle}")
        self.driver.switch_to.window(handle)

    def switch_to_frame(self, frame) -> None:
        """
        切换到 iframe。
        :param frame: 可以是 frame 的 name/id，或一个 WebElement。
        """
        self.logger.info(f"切换到 frame: {frame}")
        self.driver.switch_to.frame(frame)

    def switch_to_default_content(self) -> None:
        """切回主文档。"""
        self.logger.info("切回默认内容（主文档）")
        self.driver.switch_to.default_content()

    # ========== JS 操作 ========== #

    def execute_js(self, script: str, *args):
        """
        执行 JavaScript 脚本。

        :param script: JS 代码，如 "return document.title;"
        :param args: 传入 JS 的参数
        :return: JS 执行结果
        """
        self.logger.debug(f"执行 JS: script={script!r}, args={args}")
        return self.driver.execute_script(script, *args)
