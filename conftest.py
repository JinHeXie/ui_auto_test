# conftest.py (修改后)
"""
Pytest 全局配置 - 仅保留基础 driver 和 Allure 配置
"""
from __future__ import annotations

import pytest
import allure
from datetime import datetime
import os

from core.driver_factory import create_driver, quit_driver
from core.config_loader import get_current_platform
from core.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def driver():
    """session 级别的 driver fixture - 全局共享"""
    platform = get_current_platform()
    logger.info(f"[Global] 创建全局 driver，platform={platform}")
    drv = create_driver()
    yield drv
    logger.info("[Global] 销毁全局 driver")
    quit_driver(drv)


def pytest_configure(config):
    """全局 Allure 配置"""
    allure_dir = config.getoption("--alluredir")
    if allure_dir:
        env_file = os.path.join(allure_dir, "environment.properties")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"测试时间={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"项目名称=UI自动化测试框架\n")
            f.write(f"测试环境={os.getenv('TEST_ENV', 'test')}\n")
            f.write(f"Python版本={os.sys.version}\n")
            f.write(f"操作系统={os.sys.platform}\n")