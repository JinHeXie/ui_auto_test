# demo_run_web.py （纯示例）
from core.driver_factory import create_driver, quit_driver

if __name__ == "__main__":
    driver = create_driver()  # platform=web 时创建的是 Selenium WebDriver
    try:
        driver.get("http://192.168.1.20:31180/ai/")
        print(driver.title)
    finally:
        quit_driver(driver)
