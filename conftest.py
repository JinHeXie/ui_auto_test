# conftest.py
"""
Pytest 全局配置 & fixture

主要内容：
- driver fixture：在 session 级别初始化并销毁 driver
- 示例：web_login_page fixture，方便 Web 登录用例直接使用
"""

from __future__ import annotations

import pytest
import allure

from core.driver_factory import create_driver, quit_driver
from core.config_loader import get_current_platform
from core.logger import get_logger

# Web 相关示例 PO
from pages.web.login_page import LoginPage


logger = get_logger(__name__)


@pytest.fixture(scope="session")
def driver():
    """
    session 级别的 driver fixture。

    - 在整个测试会话开始时创建 driver
    - 所有用例共享同一个 driver
    - 在会话结束时统一退出 driver

    注意：
    - 当前 platform 由 config/settings.yaml 中的 platform 字段决定。
    - 如果你要运行 Android/iOS，用例中也复用此 fixture 即可。
    """
    platform = get_current_platform()
    logger.info(f"[conftest] 即将创建 driver，platform={platform!r}")
    drv = create_driver()
    yield drv
    logger.info("[conftest] 测试结束，准备退出 driver")
    quit_driver(drv)


# ========== Web 登录页面 fixture 示例 ========== #

@pytest.fixture
def web_login_page(driver) -> LoginPage:
    """
    提供登录页面对象（适配弹窗登录）

    注意：现在会自动打开登录弹窗，而不是直接访问登录页
    """
    page = LoginPage(driver)
    page.open_login_modal()  # ✅ 改为弹窗登录
    return page


def pytest_configure(config):
    """配置Allure环境信息"""
    import os
    from datetime import datetime

    allure_dir = config.getoption("--alluredir")
    if allure_dir:
        # 创建环境信息文件
        env_file = os.path.join(allure_dir, "environment.properties")
        with open(env_file, "w") as f:
            f.write(f"测试时间={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"项目名称=UI自动化测试框架\n")
            f.write(f"测试环境={os.getenv('TEST_ENV', 'test')}\n")
            f.write(f"Python版本={os.sys.version}\n")
            f.write(f"操作系统={os.sys.platform}\n")
