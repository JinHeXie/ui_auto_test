from __future__ import annotations

import os
import platform as pf
from pathlib import Path
from typing import Any, Dict

import logging
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService

logger = logging.getLogger(__name__)


def _project_root() -> Path:
    # core/driver_manager.py -> core -> project root
    return Path(__file__).resolve().parents[1]


def _resolve_driver_path(driver_path: str) -> str:
    """
    支持：
    - 绝对路径
    - 相对项目根路径（例如 bin/drivers/chromedriver）
    - Windows 自动补 .exe（如果没写）
    """
    if not driver_path:
        return ""

    p = Path(driver_path)
    if not p.is_absolute():
        p = _project_root() / p

    # Windows 补全 .exe
    if pf.system().lower().startswith("win") and p.suffix.lower() != ".exe":
        exe = Path(str(p) + ".exe")
        if exe.exists():
            p = exe

    return str(p)


def _apply_common_options(options: Any, config: Dict[str, Any]) -> None:
    headless = bool(config.get("headless", False))
    window_size = (config.get("window_size") or "").strip()

    if headless:
        # Selenium 4 推荐
        options.add_argument("--headless=new")

    if window_size:
        options.add_argument(f"--window-size={window_size}")

    # Docker/CI 常用
    if headless or os.getenv("CI") == "true":
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")


def create_local_webdriver(config: Dict[str, Any]) -> SeleniumWebDriver:
    browser = (config.get("browser", "chrome") or "chrome").lower()
    raw_driver_path = (config.get("driver_path") or "").strip()
    driver_path = _resolve_driver_path(raw_driver_path)

    if browser == "chrome":
        options = ChromeOptions()
        _apply_common_options(options, config)
        if driver_path:
            if not Path(driver_path).exists():
                raise FileNotFoundError(f"未找到 chromedriver: {driver_path}")
            logger.info(f"[DriverManager] 使用指定 chromedriver: {driver_path}")
            return webdriver.Chrome(service=ChromeService(driver_path), options=options)
        return webdriver.Chrome(options=options)

    if browser == "edge":
        options = EdgeOptions()
        _apply_common_options(options, config)
        if driver_path:
            if not Path(driver_path).exists():
                raise FileNotFoundError(f"未找到 edgedriver: {driver_path}")
            logger.info(f"[DriverManager] 使用指定 edgedriver: {driver_path}")
            return webdriver.Edge(service=EdgeService(driver_path), options=options)
        return webdriver.Edge(options=options)

    if browser == "firefox":
        options = FirefoxOptions()
        _apply_common_options(options, config)
        if driver_path:
            if not Path(driver_path).exists():
                raise FileNotFoundError(f"未找到 geckodriver: {driver_path}")
            logger.info(f"[DriverManager] 使用指定 geckodriver: {driver_path}")
            return webdriver.Firefox(service=FirefoxService(driver_path), options=options)
        return webdriver.Firefox(options=options)

    raise ValueError(f"不支持的浏览器类型: {browser}")


def create_remote_webdriver(config: Dict[str, Any]) -> SeleniumWebDriver:
    remote_url = (config.get("remote_url") or "").strip()
    if not remote_url:
        raise ValueError("remote=true 但 remote_url 为空")

    browser = (config.get("browser", "chrome") or "chrome").lower()

    if browser == "chrome":
        options = ChromeOptions()
    elif browser == "edge":
        options = EdgeOptions()
    elif browser == "firefox":
        options = FirefoxOptions()
    else:
        raise ValueError(f"不支持的浏览器类型: {browser}")

    _apply_common_options(options, config)
    logger.info(f"[DriverManager] 使用远程 WebDriver: {remote_url}")
    return webdriver.Remote(command_executor=remote_url, options=options)
