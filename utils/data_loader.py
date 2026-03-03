# utils/data_loader.py
"""
数据加载工具

目前提供：
- load_yaml: 从项目相对路径读取 YAML 文件，返回 Python 对象
"""

from __future__ import annotations

from typing import Any

import yaml

from utils.path_helper import join_project_path


def load_yaml(relative_path: str) -> Any:
    """
    从项目相对路径加载 YAML 文件。

    使用示例：
        data = load_yaml("data/web/login_data.yaml")

    :param relative_path: 相对项目根目录的路径，例如 "data/web/login_data.yaml"
    :return: 解析后的 Python 对象（dict / list 等）
    """
    abs_path = join_project_path(relative_path)
    with open(abs_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
