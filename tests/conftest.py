# tests/conftest.py (新建)
"""
测试层通用 fixture
"""
from __future__ import annotations

import pytest
from core.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture(autouse=True)
def test_lifecycle_log(request):
    """自动记录测试用例生命周期"""
    test_name = request.node.name
    logger.info(f"\n{'=' * 50}\n开始测试: {test_name}\n{'=' * 50}")
    yield
    logger.info(f"\n{'=' * 50}\n结束测试: {test_name}\n{'=' * 50}")


@pytest.fixture(scope="function")
def clean_state(driver):
    """
    通用状态清理 fixture - 可选择使用
    在需要干净状态的测试中声明此 fixture 即可
    """
    yield
    logger.info("[Clean] 执行通用状态清理")
    driver.delete_all_cookies()
    driver.refresh()