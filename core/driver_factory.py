# core/driver_factory.py
"""
驱动工厂（Driver Factory）

职责：
- 统一管理 Web / Android / iOS Driver 的创建与销毁。
- 从 config_loader 中读取对应平台的配置。
- 对外只暴露少量方法：create_driver、quit_driver，后续在 pytest fixture 中统一使用。

注意：
- 当前使用 Python 自带 logging 做简单日志输出。
- 后续可以用 core/logger.py 中封装好的 logger 替换此处的 logging。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver

from appium import webdriver as appium_webdriver
from appium.webdriver.webdriver import WebDriver as AppiumWebDriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from core.driver_manager import create_local_webdriver, create_remote_webdriver



from core.config_loader import (
    get_current_platform,
    get_web_config,
    get_android_config,
    get_ios_config,
)
from core.logger import get_logger

# 使用统一 logger
logger = get_logger(__name__)

# 为了类型提示方便，定义一个统一类型别名：
DriverType = SeleniumWebDriver | AppiumWebDriver


def create_driver() -> DriverType:
    """
    创建并返回一个 driver 实例。

    根据 settings.yaml 中的 platform 字段自动选择：
        - web     -> 创建 Selenium WebDriver
        - android -> 创建 Appium Android driver
        - ios     -> 创建 Appium iOS driver

    使用示例（后续建议在 Pytest fixture 中使用）：
        from core.driver_factory import create_driver, quit_driver

        driver = create_driver()
        driver.get("https://xxx")
        quit_driver(driver)
    """
    platform = get_current_platform()
    logger.info(f"[DriverFactory] 当前平台: {platform!r}")

    if platform == "web":
        return _create_web_driver()
    elif platform == "android":
        return _create_android_driver()
    elif platform == "ios":
        return _create_ios_driver()
    else:
        # 理论上在 config_loader 中已经校验过，这里是双重保护
        raise ValueError(f"不支持的平台类型: {platform}")


# =============== Web Driver 部分 =============== #

def _create_web_driver() -> SeleniumWebDriver:
    config: Dict[str, Any] = get_web_config()
    remote = bool(config.get("remote", False))

    if remote:
        driver = create_remote_webdriver(config)
    else:
        driver = create_local_webdriver(config)

    # 下面你的通用配置逻辑保持不变
    try:
        driver.maximize_window()
    except Exception:
        logger.warning("[DriverFactory] maximize_window 失败，可能运行在无头或远程环境")

    implicit_wait = config.get("implicit_wait", 5)
    page_load_timeout = config.get("page_load_timeout", 30)

    driver.implicitly_wait(implicit_wait)
    driver.set_page_load_timeout(page_load_timeout)

    return driver



def _init_webdriver_with_options(
    browser: str,
    options: Any,
    remote: bool,
    remote_url: str,
) -> SeleniumWebDriver:
    config = get_web_config()

    driver_path = (config.get("driver_path") or "").strip()

    if remote:
        if not remote_url:
            raise ValueError("remote=true 但未配置 remote_url")
        logger.info(f"[DriverFactory] 使用远程 WebDriver: {remote_url}")
        return webdriver.Remote(command_executor=remote_url, options=options)

    logger.info("[DriverFactory] 使用本地 WebDriver")

    # ---- Chrome ----
    if browser == "chrome":
        if driver_path:
            logger.info(f"[DriverFactory] 使用指定 chromedriver: {driver_path}")
            return webdriver.Chrome(
                service=ChromeService(executable_path=driver_path),
                options=options
            )
        return webdriver.Chrome(options=options)

    # ---- Edge ----
    if browser == "edge":
        if driver_path:
            logger.info(f"[DriverFactory] 使用指定 edgedriver: {driver_path}")
            return webdriver.Edge(
                service=EdgeService(executable_path=driver_path),
                options=options
            )
        return webdriver.Edge(options=options)

    # ---- Firefox ----
    if browser == "firefox":
        if driver_path:
            logger.info(f"[DriverFactory] 使用指定 geckodriver: {driver_path}")
            return webdriver.Firefox(
                service=FirefoxService(executable_path=driver_path),
                options=options
            )
        return webdriver.Firefox(options=options)

    raise ValueError(f"不支持的浏览器类型: {browser}")



# =============== Android Driver 部分 =============== #

def _create_android_driver(device_name: Optional[str] = None) -> AppiumWebDriver:
    """
    创建 Android Appium driver。

    配置来源：config/android_env.yaml + settings.yaml 中的 env。

    :param device_name: 可选，指定使用 android_env.yaml 中 devices 列表里的某个设备名。
                        若不指定，则使用 default_device。
    """
    config: Dict[str, Any] = get_android_config()

    appium_server: str = config.get("appium_server")
    common_caps: Dict[str, Any] = config.get("common_capabilities", {})
    default_device: Dict[str, Any] = config.get("default_device", {})
    devices: list[Dict[str, Any]] = config.get("devices", [])

    if not appium_server:
        raise ValueError("android_env.yaml 未配置 appium_server")

    # 选择设备配置
    device_caps = _select_android_device(device_name, default_device, devices)

    # 最终 capabilities = 公共配置 + 设备配置
    desired_caps: Dict[str, Any] = {**common_caps, **device_caps}

    logger.info(
        f"[DriverFactory] 创建 Android driver, "
        f"server={appium_server!r}, device={device_caps.get('deviceName')!r}"
    )
    logger.debug(f"[DriverFactory] Android desired capabilities: {desired_caps!r}")

    driver: AppiumWebDriver = appium_webdriver.Remote(
        command_executor=appium_server,
        desired_capabilities=desired_caps,
    )

    # Appium driver 一般不需要额外超时配置，这里先留接口，后续如有需要可补充
    return driver


def _select_android_device(
    device_name: Optional[str],
    default_device: Dict[str, Any],
    devices: list[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    根据 device_name 从 devices 列表中选择设备配置。
    如果 device_name 为空或找不到对应设备，则使用 default_device。

    :param device_name: 目标设备名，对应 android_env.yaml 中 devices[*].name
    :param default_device: 默认设备配置
    :param devices: 设备列表配置
    :return: 最终使用的设备配置字典
    """
    if device_name:
        for dev in devices:
            if dev.get("name") == device_name:
                logger.info(f"[DriverFactory] 使用指定设备: {device_name!r}")
                return dev
        logger.warning(
            f"[DriverFactory] 未找到名为 {device_name!r} 的设备配置，"
            f"将使用 default_device"
        )

    if not default_device:
        raise ValueError(
            "Android 配置中未指定 default_device，且未找到匹配的 devices[*]，请检查 android_env.yaml"
        )

    logger.info("[DriverFactory] 使用 default_device 设备配置")
    return default_device


# =============== iOS Driver 部分 =============== #

def _create_ios_driver(device_name: Optional[str] = None) -> AppiumWebDriver:
    """
    创建 iOS Appium driver。

    配置来源：config/ios_env.yaml + settings.yaml 中的 env。

    :param device_name: 预留参数，若未来在 ios_env.yaml 中也维护 devices 列表，可以按名称选择设备。
    """
    config: Dict[str, Any] = get_ios_config()

    appium_server: str = config.get("appium_server")
    common_caps: Dict[str, Any] = config.get("common_capabilities", {})
    default_device: Dict[str, Any] = config.get("default_device", {})

    if not appium_server:
        raise ValueError("ios_env.yaml 未配置 appium_server")

    # 简化处理：目前先只支持 default_device
    desired_caps: Dict[str, Any] = {**common_caps, **default_device}

    logger.info(
        f"[DriverFactory] 创建 iOS driver, "
        f"server={appium_server!r}, device={default_device.get('deviceName')!r}"
    )
    logger.debug(f"[DriverFactory] iOS desired capabilities: {desired_caps!r}")

    driver: AppiumWebDriver = appium_webdriver.Remote(
        command_executor=appium_server,
        desired_capabilities=desired_caps,
    )
    return driver


# =============== 公共销毁方法 =============== #

def quit_driver(driver: Optional[DriverType]) -> None:
    """
    统一关闭并销毁 driver。

    :param driver: WebDriver 或 AppiumDriver 实例；如果为 None 则直接返回。
    """
    if driver is None:
        return

    try:
        driver.quit()
        logger.info("[DriverFactory] Driver 已正常退出")
    except Exception as e:
        logger.error(f"[DriverFactory] 退出 driver 时发生异常: {e}")
