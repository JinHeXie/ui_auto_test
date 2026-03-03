# verify_framework.py
"""
验证框架配置、驱动创建、页面访问的完整链条
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from core.config_loader import get_current_platform, get_web_config
from core.driver_factory import create_driver, quit_driver


def main():
    print("=" * 50)
    print("开始验证自动化测试框架")
    print("=" * 50)

    # 1. 验证配置加载
    try:
        platform = get_current_platform()
        print(f"✅ 配置加载成功 - 当前平台: {platform}")

        web_config = get_web_config()
        print(f"✅ Web配置加载成功 - 环境: {web_config.get('_env', 'unknown')}")
        print(f"   浏览器: {web_config.get('browser')}")
        print(f"   基础URL: {web_config.get('base_url')}")
        print(f"   无头模式: {web_config.get('headless')}")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

    # 2. 验证驱动创建和网页访问
    driver = None
    try:
        print("\n[2] 尝试创建WebDriver...")
        driver = create_driver()
        print("✅ WebDriver创建成功")

        target_url = web_config.get('base_url')
        print(f"   正在访问: {target_url}")
        driver.get(target_url)

        actual_title = driver.title
        actual_url = driver.current_url
        print(f"✅ 页面访问成功")
        print(f"   标题: {actual_title[:50]}...")
        print(f"   当前URL: {actual_url}")

        # 简单截图验证（即使在headless模式下）
        screenshot_path = "verify_screenshot.png"
        driver.save_screenshot(screenshot_path)
        if os.path.exists(screenshot_path):
            print(f"✅ 截图成功: {screenshot_path}")

        return True

    except Exception as e:
        print(f"❌ 驱动创建或页面访问失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            print("\n清理中...")
            quit_driver(driver)


if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 50)
    print(f"验证结果: {'✅ 全部通过' if success else '❌ 存在错误'}")
    print("=" * 50)
    sys.exit(0 if success else 1)