# tests/web/conftest.py (新建)
"""
Web 测试模块专属 fixture
"""
from __future__ import annotations

import pytest
from core.logger import get_logger
from pages.web.login_page import LoginPage

logger = get_logger(__name__)


@pytest.fixture(scope="function")
def web_driver(driver):
    """
    Web 专用的 driver wrapper

    自动在每个 Web 测试后清理：
    - 清除 cookies
    - 清除 localStorage/sessionStorage
    - 刷新页面

    解决测试状态污染问题
    """
    logger.info("[Web] 准备 Web 测试环境")
    yield driver

    logger.info("[Web] 清理 Web 测试环境")
    driver.delete_all_cookies()
    try:
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
    except Exception as e:
        logger.warning(f"清理存储失败: {e}")
    driver.refresh()


@pytest.fixture
def login_page(web_driver) -> LoginPage:
    """
    Web 登录页面 fixture

    自动打开登录弹窗，每个测试都能从干净的登录状态开始
    """
    logger.info("[Web] 创建 LoginPage 实例并打开登录弹窗")
    page = LoginPage(web_driver)
    page.open_login_modal()
    return page


@pytest.fixture
def logged_in_session(web_driver):
    """
    已登录状态的 fixture

    用于需要登录后才能测试的场景，自动处理登录和清理
    """
    from utils.data_loader import load_yaml

    logger.info("[Web] 创建已登录会话")
    login_data = load_yaml("data/web/login_data.yaml")
    page = LoginPage(web_driver)

    success = page.login(
        username=login_data["valid"]["username"],
        password=login_data["valid"]["password"],
        auto_handle_captcha=True
    )

    if not success:
        pytest.fail("登录失败，无法创建登录会话")

    logger.info("[Web] 登录会话创建成功")
    yield web_driver

    # 测试后自动退出登录
    logger.info("[Web] 退出登录")
    web_driver.delete_all_cookies()


@pytest.fixture(autouse=True, scope="module")
def web_module_setup_teardown():
    """Web 模块级别的 setup/teardown"""
    logger.info(">>> Web 测试模块开始 <<<")
    yield
    logger.info(">>> Web 测试模块结束 <<<")