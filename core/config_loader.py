# core/config_loader.py
import os
from typing import Any, Dict

import yaml

from utils.path_helper import join_project_path


class ConfigError(Exception):
    """配置相关异常，用于在配置错误时给出明确提示。"""
    pass


def _load_yaml_file(path: str) -> Dict[str, Any]:
    """
    内部工具函数：从指定路径加载 YAML 文件，返回字典。

    :param path: YAML 文件的绝对路径
    :return: 解析后的字典
    """
    if not os.path.exists(path):
        raise ConfigError(f"配置文件不存在: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        raise ConfigError(f"解析配置文件失败: {path}, 错误: {e}")
    return data


# 使用“模块级缓存”，避免每次调用都重新读文件
_settings_cache: Dict[str, Any] | None = None
_web_env_cache: Dict[str, Any] | None = None
_android_env_cache: Dict[str, Any] | None = None
_ios_env_cache: Dict[str, Any] | None = None


def get_settings() -> Dict[str, Any]:
    """
    获取全局 settings 配置（来自 config/settings.yaml）。

    返回一个字典，包含：
    - platform: 当前平台（web/android/ios）
    - env: 当前环境（dev/test/prod）
    - log: 日志相关配置
    """
    global _settings_cache
    if _settings_cache is None:
        path = join_project_path("config", "settings.yaml")
        _settings_cache = _load_yaml_file(path)
    return _settings_cache


def get_current_platform() -> str:
    """
    获取当前平台字符串：web / android / ios
    """
    settings = get_settings()
    platform = settings.get("platform")
    if platform not in ("web", "android", "ios"):
        raise ConfigError(f"配置错误：不支持的平台 '{platform}'，请检查 settings.yaml")
    return platform


def get_current_env() -> str:
    """
    获取当前环境字符串：dev / test / prod
    """
    settings = get_settings()
    env = settings.get("env")
    if env not in ("dev", "test", "prod"):
        raise ConfigError(f"配置错误：不支持的环境 '{env}'，请检查 settings.yaml")
    return env


def get_log_config() -> Dict[str, Any]:
    """
    获取日志相关配置。

    返回示例：
    {
        "level": "INFO",
        "to_console": True,
        "to_file": True,
        "file_name_pattern": "logs/ui_test_{date}.log",
        "max_size_mb": 10,
        "backup_count": 5
    }
    """
    settings = get_settings()
    log_config = settings.get("log", {})
    return log_config


def get_web_config(env: str | None = None) -> Dict[str, Any]:
    """
    获取 Web 环境配置（来自 config/web_env.yaml）。

    :param env: 环境名（dev/test/prod），默认使用 settings.yaml 中的 env。
    :return: 对应环境的配置字典。
    """
    global _web_env_cache
    if _web_env_cache is None:
        path = join_project_path("config", "web_env.yaml")
        _web_env_cache = _load_yaml_file(path)

    env = env or get_current_env()
    if env not in _web_env_cache:
        raise ConfigError(f"web_env.yaml 中不存在环境 '{env}' 的配置")
    return _web_env_cache[env]


def get_android_config(env: str | None = None) -> Dict[str, Any]:
    """
    获取 Android 环境配置（来自 config/android_env.yaml）。

    :param env: 环境名（dev/test/prod），默认使用 settings.yaml 中的 env。
    :return: 对应环境的配置字典。
    """
    global _android_env_cache
    if _android_env_cache is None:
        path = join_project_path("config", "android_env.yaml")
        _android_env_cache = _load_yaml_file(path)

    env = env or get_current_env()
    if env not in _android_env_cache:
        raise ConfigError(f"android_env.yaml 中不存在环境 '{env}' 的配置")
    return _android_env_cache[env]


def get_ios_config(env: str | None = None) -> Dict[str, Any]:
    """
    获取 iOS 环境配置（来自 config/ios_env.yaml）。

    :param env: 环境名（dev/test/prod），默认使用 settings.yaml 中的 env。
    :return: 对应环境的配置字典。
    """
    global _ios_env_cache
    if _ios_env_cache is None:
        path = join_project_path("config", "ios_env.yaml")
        _ios_env_cache = _load_yaml_file(path)

    env = env or get_current_env()
    if env not in _ios_env_cache:
        raise ConfigError(f"ios_env.yaml 中不存在环境 '{env}' 的配置")
    return _ios_env_cache[env]
