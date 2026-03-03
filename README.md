# UI 自动化测试框架（Web + App）

## 1. 环境准备

```bash
# 建议创建虚拟环境
python -m venv venv
# Windows 激活
venv\Scripts\activate
# macOS/Linux 激活
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt


# 运行 Web 用例
pytest tests/web -m web

# 运行 Android 用例
pytest tests/app -m android

# 运行全部用例
pytest

