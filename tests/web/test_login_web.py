# tests/web/test_login_web.py（修正后）
"""
Web 登录用例 - 适配弹窗登录和验证码处理
"""

from __future__ import annotations

import pytest
import allure
import time

from pages.web.login_page import LoginPage
from utils.data_loader import load_yaml

# 预先加载测试数据
_login_data = load_yaml("data/web/login_data.yaml")
_valid_data = _login_data["valid"]
_invalid_cases = _login_data["invalid"]


@allure.epic("Web UI 自动化")
@allure.feature("登录模块")
class TestWebLogin:
    """登录测试用例 - 适配弹窗登录"""

    @allure.story("登录成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "regression")
    def test_login_success(self, driver):
        """登录成功用例 - 适配弹窗登录"""
        login_page = LoginPage(driver)

        with allure.step("1. 打开登录弹窗"):
            login_page.open_login_modal()
            allure.attach(
                driver.get_screenshot_as_png(),
                name="login_modal_opened",
                attachment_type=allure.attachment_type.PNG
            )

        with allure.step("2. 输入正确的用户名和密码"):
            username = _valid_data["username"]
            password = _valid_data["password"]

            login_page.enter_credentials(username, password)
            login_page.check_agreement()

            allure.attach(
                driver.get_screenshot_as_png(),
                name="credentials_filled",
                attachment_type=allure.attachment_type.PNG
            )

        with allure.step("3. 点击登录并处理验证码"):
            login_page.click_login_button()
            time.sleep(2)

            if login_page.is_captcha_visible():
                allure.step("检测到验证码，开始处理")
                captcha_success = login_page.solve_slider_captcha()

                allure.attach(
                    driver.get_screenshot_as_png(),
                    name="captcha_processing",
                    attachment_type=allure.attachment_type.PNG
                )

                assert captcha_success, "验证码处理失败"
            else:
                allure.step("未检测到验证码，继续登录")

        with allure.step("4. 验证登录成功"):
            time.sleep(3)
            assert login_page.is_login_success(), "登录未成功"

            allure.attach(
                driver.get_screenshot_as_png(),
                name="login_success",
                attachment_type=allure.attachment_type.PNG
            )

    @allure.story("登录失败 - 数据驱动")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "case_name, username, password, expected_error",
        [
            (c["case"], c["username"], c["password"], c["expected_error"])
            for c in _invalid_cases
        ],
        ids=[c["case"] for c in _invalid_cases],
    )
    def test_login_fail(
            self,
            driver,
            case_name: str,
            username: str,
            password: str,
            expected_error: str,
    ):
        """登录失败用例（数据驱动）"""
        login_page = LoginPage(driver)

        with allure.step(f"[{case_name}] 打开登录弹窗"):
            login_page.open_login_modal()

        with allure.step(f"[{case_name}] 输入用户名和密码"):
            login_page.enter_credentials(username, password)
            login_page.check_agreement()

            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"input_{case_name}",
                attachment_type=allure.attachment_type.PNG
            )

        with allure.step(f"[{case_name}] 点击登录"):
            login_page.click_login_button()

            # 对于空用户名/密码，可能不会触发验证码
            if username and password:
                time.sleep(2)

                if login_page.is_captcha_visible(timeout=3):
                    allure.step("检测到验证码，尝试处理")
                    login_page.solve_slider_captcha()
                    time.sleep(2)

        with allure.step(f"[{case_name}] 获取错误提示并断言"):
            time.sleep(2)
            actual_error = login_page.get_error_message()

            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"error_{case_name}",
                attachment_type=allure.attachment_type.PNG
            )

            assert expected_error in actual_error, (
                f"期望错误提示包含: {expected_error!r}, 实际: {actual_error!r}"
            )

    @allure.story("使用集成登录方法")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_integrated_login_method(self, driver):
        """测试集成登录方法"""
        login_page = LoginPage(driver)

        with allure.step("使用集成登录方法"):
            success = login_page.login(
                username=_valid_data["username"],
                password=_valid_data["password"],
                auto_handle_captcha=True
            )

            allure.attach(
                driver.get_screenshot_as_png(),
                name="integrated_login_result",
                attachment_type=allure.attachment_type.PNG
            )

            assert success, "集成登录方法失败"

    @allure.story("验证码可见性检查")
    def test_captcha_visibility(self, driver):
        """测试验证码是否会出现"""
        login_page = LoginPage(driver)

        with allure.step("1. 打开登录弹窗"):
            login_page.open_login_modal()

        with allure.step("2. 输入账号密码"):
            login_page.enter_credentials(_valid_data["username"], _valid_data["password"])
            login_page.check_agreement()

        with allure.step("3. 点击登录触发验证码"):
            login_page.click_login_button()
            time.sleep(2)

            allure.attach(
                driver.get_screenshot_as_png(),
                name="before_captcha_check",
                attachment_type=allure.attachment_type.PNG
            )

        with allure.step("4. 检查验证码是否可见"):
            is_visible = login_page.is_captcha_visible(timeout=5)

            if is_visible:
                allure.step("✅ 验证码可见")
                captcha_success = login_page.solve_slider_captcha()
                assert captcha_success, "验证码解决失败"
            else:
                allure.step("ℹ️ 验证码不可见，可能不需要验证码")
                pytest.skip("验证码未出现，跳过验证码相关测试")