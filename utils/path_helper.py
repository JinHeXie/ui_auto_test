# utils/path_helper.py
import os
from typing import Optional


def get_project_root() -> str:
    """
    获取项目根目录路径。

    思路：
    - 假设此文件位于项目中的 utils/path_helper.py
    - 那么项目根目录就是此文件的上上级目录。
    """
    # 当前文件路径：.../ui_auto_test/utils/path_helper.py
    current_file = os.path.abspath(__file__)
    # utils 目录
    utils_dir = os.path.dirname(current_file)
    # 项目根目录（再上一级）
    project_root = os.path.dirname(utils_dir)
    return project_root


def join_project_path(*paths: str) -> str:
    """
    基于项目根目录拼接相对路径，返回绝对路径。

    使用示例：
        config_path = join_project_path("config", "settings.yaml")
    """
    return os.path.join(get_project_root(), *paths)


def ensure_dir_exists(dir_path: str) -> None:
    """
    确保目标目录存在，如果不存在则创建。

    常用于：日志目录、报告目录等。
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
