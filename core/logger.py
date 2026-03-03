# core/logger.py
"""
统一日志模块

职责：
- 初始化全局日志配置（根 logger）。
- 支持控制台输出 + 文件输出（带滚动）。
- 所有模块通过 get_logger(name) 获取 logger 使用。

配置来源：
- config/settings.yaml 中的 log 字段：
    log:
      level: INFO
      to_console: true
      to_file: true
      file_name_pattern: "logs/ui_test_{date}.log"
      max_size_mb: 10
      backup_count: 5
"""

from __future__ import annotations

import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any

from core.config_loader import get_log_config
from utils.path_helper import join_project_path, ensure_dir_exists


# 标记是否已经初始化过根 logger，避免重复添加 Handler
_LOGGER_INITIALIZED = False


def _level_str_to_int(level_str: str) -> int:
    """
    将字符串形式的日志级别转换为 logging 对应的常量。

    :param level_str: 如 "DEBUG" / "INFO" / "WARNING" / "ERROR"
    :return: logging.DEBUG / logging.INFO 等
    """
    mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return mapping.get(level_str.upper(), logging.INFO)


def _build_log_file_path(pattern: str) -> str:
    """
    根据配置中的 file_name_pattern 构造日志文件绝对路径。

    支持 {date} 占位符，会替换为当前日期（格式：YYYY-MM-DD）。

    :param pattern: 例如 "logs/ui_test_{date}.log"
    :return: 日志文件的绝对路径，如 "/xxx/ui_automation_framework/logs/ui_test_2025-12-08.log"
    """
    # 替换 {date}
    today = datetime.now().strftime("%Y-%m-%d")
    relative_path = pattern.format(date=today)

    # 相对路径 -> 项目根目录下的绝对路径
    abs_path = join_project_path(relative_path)

    # 确保日志目录存在
    # 例如 abs_path = /project/logs/ui_test_2025-12-08.log
    # 则目录为 /project/logs
    import os
    log_dir = os.path.dirname(abs_path)
    ensure_dir_exists(log_dir)

    return abs_path


def _init_root_logger() -> None:
    """
    初始化根 logger（只调用一次）。

    - 从配置读取日志级别、输出方式等
    - 添加控制台 Handler（可选）
    - 添加文件 Handler（可选、带滚动）
    """
    global _LOGGER_INITIALIZED
    if _LOGGER_INITIALIZED:
        return

    log_config: Dict[str, Any] = get_log_config()

    level_str = log_config.get("level", "INFO")
    level = _level_str_to_int(level_str)

    to_console = bool(log_config.get("to_console", True))
    to_file = bool(log_config.get("to_file", True))
    file_pattern = log_config.get("file_name_pattern", "logs/ui_test_{date}.log")
    max_size_mb = int(log_config.get("max_size_mb", 10))
    backup_count = int(log_config.get("backup_count", 5))

    # 获取根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 为避免重复 add handler，先清空已有 Handler（谨慎使用，只在我们控制环境下）
    if root_logger.handlers:
        root_logger.handlers.clear()

    # 日志输出格式
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1) 控制台输出
    if to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 2) 文件输出（滚动日志）
    if to_file:
        log_file_path = _build_log_file_path(file_pattern)
        max_bytes = max_size_mb * 1024 * 1024

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 标记为已初始化
    _LOGGER_INITIALIZED = True

    # 初始化完成后，可以打印一条日志（此时 Handler 已就位）
    root_logger.info(
        "日志系统初始化完成: level=%s, to_console=%s, to_file=%s, file_pattern=%s",
        level_str,
        to_console,
        to_file,
        file_pattern,
    )


def get_logger(name: str | None = None) -> logging.Logger:
    """
    对外提供的统一获取 logger 的方法。

    使用方式：
        from core.logger import get_logger

        logger = get_logger(__name__)
        logger.info("xxx")

    :param name: logger 名称，通常传 __name__。
    :return: logging.Logger 实例
    """
    # 确保根 logger 已初始化（只会初始化一次）
    if not _LOGGER_INITIALIZED:
        _init_root_logger()

    return logging.getLogger(name)
