# utils/slider_solver.py
"""
滑动验证码解决工具（适配项目框架）
"""
from __future__ import annotations  # ✅ 添加这个用于类型提示

import time
import random
from io import BytesIO
import base64
from typing import Optional, Tuple

import cv2
import numpy as np
import requests
from PIL import Image
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from core.logger import get_logger


class SliderCaptchaSolver:
    def __init__(self, driver: WebDriver):
        """
        初始化验证码解决器

        Args:
            driver: Selenium WebDriver 实例
        """
        self.driver = driver
        self.logger = get_logger(__name__)

    def solve_captcha(
            self,
            bg_img_src: str,
            gap_img_src: str,
            slider_element: WebElement,
            offset_from_api: Optional[int] = None
    ) -> bool:
        """
        解决滑动验证码

        Args:
            bg_img_src: 背景图的src属性
            gap_img_src: 缺口图的src属性
            slider_element: 滑块WebElement
            offset_from_api: 如果后端提供了偏移量，直接使用

        Returns:
            bool: 是否成功解决验证码
        """
        try:
            if offset_from_api is not None:
                raw_offset = offset_from_api
                self.logger.info(f"使用API提供的偏移量: {raw_offset}px")
            else:
                bg_img, gap_img = self._download_images(bg_img_src, gap_img_src)
                raw_offset = self._calculate_offset(bg_img, gap_img)
                self.logger.info(f"计算得到原始偏移量: {raw_offset}px")

            # 计算实际拖动距离
            distance = self._calculate_actual_distance(raw_offset, bg_img_src)

            # 执行拖动
            self._drag_slider(slider_element, distance)

            # 等待验证结果
            time.sleep(1.5)
            return True

        except Exception as e:
            self.logger.error(f"解决验证码失败: {e}")
            return False

    # ----------------- 图像获取 -----------------
    def _download_images(self, bg_url: str, gap_url: str) -> Tuple[Image.Image, Image.Image]:
        """下载背景图和缺口图"""

        def download_img(url: str) -> Image.Image:
            url = url.strip()
            if url.startswith("data:image"):
                _, b64data = url.split(",", 1)
                img_bytes = base64.b64decode(b64data)
                return Image.open(BytesIO(img_bytes))
            else:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                return Image.open(BytesIO(resp.content))

        return download_img(bg_url), download_img(gap_url)

    # ----------------- 图像匹配 -----------------
    def _calculate_offset(self, bg_img: Image.Image, gap_img: Image.Image) -> int:
        """
        针对拼图验证码的边缘检测 + 模板匹配

        Args:
            bg_img: 背景图
            gap_img: 缺口图

        Returns:
            int: 偏移量（像素）
        """
        # 灰度
        bg = cv2.cvtColor(np.array(bg_img), cv2.COLOR_RGB2GRAY)
        gap = cv2.cvtColor(np.array(gap_img), cv2.COLOR_RGB2GRAY)

        # 边缘处理
        bg_edge = cv2.Canny(bg, 100, 200)
        gap_edge = cv2.Canny(gap, 100, 200)

        # 模板匹配
        res = cv2.matchTemplate(bg_edge, gap_edge, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        x, y = max_loc

        # 调试信息
        h, w = gap_edge.shape[:2]
        debug = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2BGR)
        cv2.rectangle(debug, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.imwrite("debug_match_edge.png", debug)

        self.logger.info(f"[DEBUG] edge_match_score = {max_val}")

        return x

    # ----------------- 距离计算 -----------------
    def _calculate_actual_distance(self, raw_offset: int, bg_img_src: str) -> int:
        """计算实际需要拖动的距离（考虑页面缩放）"""
        try:
            # 获取图片显示尺寸
            displayed_width = self.driver.execute_script("""
                var img = document.querySelector('img.slide-verify-bg-img');
                return img ? (img.clientWidth || img.width) : null;
            """)

            # 获取原图宽度
            if bg_img_src.startswith("data:image"):
                # 对于base64图片，需要下载后获取尺寸
                bg_img = Image.open(BytesIO(base64.b64decode(bg_img_src.split(",")[1])))
                original_width = bg_img.width
            else:
                # 对于网络图片，尝试获取naturalWidth
                original_width = self.driver.execute_script("""
                    var img = document.querySelector('img.slide-verify-bg-img');
                    return img ? img.naturalWidth : null;
                """)

                if not original_width:
                    # 默认假设原图宽度为320
                    original_width = 320

            # 计算缩放比例
            if original_width and original_width > 0:
                scale = displayed_width / original_width if displayed_width else 1.0
            else:
                scale = 1.0

            distance = int(raw_offset * scale)

            # 经验调整
            distance -= 5  # 微调

            # 随机扰动
            distance += random.randint(-2, 2)

            self.logger.debug(f"距离计算: 原始{raw_offset}px × 比例{scale:.2f} = 实际{distance}px")
            return max(distance, 10)  # 确保最小距离

        except Exception as e:
            self.logger.warning(f"计算实际距离失败: {e}")
            return raw_offset

    # ----------------- 轨迹生成 -----------------
    @staticmethod
    def _generate_track(distance: int):
        """
        简单生成一个加速+减速的轨迹列表，每一步是位移
        """
        track = []
        current = 0
        mid = distance * 4 / 5  # 先加速到 80%，再减速
        t = 0.2
        v = 0

        while current < distance:
            if current < mid:
                a = random.uniform(2, 4)  # 加速
            else:
                a = -random.uniform(3, 5)  # 减速

            v0 = v
            v = v0 + a * t
            move = v0 * t + 0.5 * a * (t ** 2)
            if move < 0:
                move = 1
            current += move
            track.append(round(move))

        # 修正总距离误差
        diff = distance - sum(track)
        if diff != 0:
            track.append(diff)

        return track

    # ----------------- 拖动行为 -----------------
    def _drag_slider(self, slider_element: WebElement, distance: int):
        """
        快速滑动滑块到指定偏移位置（不模拟人手轨迹）
        """
        action = ActionChains(self.driver)
        action.click_and_hold(slider_element).perform()
        # 一次性移动指定距离
        action.move_by_offset(xoffset=distance, yoffset=0).perform()
        action.release().perform()
        self.logger.info(f"快速滑动完成：移动距离 {distance}px")

    # ----------------- 兼容原接口 -----------------
    def solve(self, offset_from_api: Optional[int] = None):
        """
        兼容原接口（保持向后兼容）

        Args:
            offset_from_api: 如果后端返回了偏移量，可以直接传入
        """
        # 这个接口需要bg_img_src、gap_img_src、slider_element
        # 但在新设计中，这些应该在solve_captcha方法中传入
        raise NotImplementedError("请使用solve_captcha方法，需传入图片src和滑块元素")