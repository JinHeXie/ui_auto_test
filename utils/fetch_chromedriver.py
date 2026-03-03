"""
手动下载/准备 chromedriver 的脚本（建议在有外网的机器上跑一次）
目标：把 chromedriver 放到 bin/drivers/ 里，项目运行时走 driver_path，避免 Selenium Manager 联网。
"""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen
import zipfile
import io

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "bin" / "drivers"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()

def detect_chrome_major() -> int:
    system = platform.system().lower()

    candidates = []
    if system.startswith("win"):
        # Windows 上用注册表最稳，但这里用简单方式：让用户保证 chrome 在 PATH 或自己改造
        candidates = [["chrome", "--version"]]
    elif system == "darwin":
        candidates = [["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"], ["google-chrome", "--version"], ["chrome", "--version"]]
    else:
        candidates = [["google-chrome", "--version"], ["chromium-browser", "--version"], ["chromium", "--version"], ["chrome", "--version"]]

    for cmd in candidates:
        try:
            out = _run(cmd)
            m = re.search(r"(\d+)\.", out)
            if m:
                return int(m.group(1))
        except Exception:
            continue

    raise RuntimeError("无法检测 Chrome/Chromium 版本。请确保 chrome/google-chrome/chromium 在 PATH，或手动指定版本。")

def platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system.startswith("win"):
        return "win64"
    if system == "darwin":
        # Apple Silicon vs Intel
        return "mac-arm64" if ("arm" in machine or "aarch64" in machine) else "mac-x64"
    # linux
    return "linux64"

def download_chromedriver_for_major(major: int) -> Path:
    """
    使用 Chrome for Testing 的公开链接下载指定 major 对应的 chromedriver。
    """
    tag = platform_tag()

    # 获取 latest patch version（JSON）
    # endpoint：https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json
    url = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json"
    data = urlopen(url, timeout=30).read().decode("utf-8")

    # 粗暴解析：找 milestone major 对应的 chromedriver 下载 url（避免引入额外依赖）
    # 你也可以改成 json.loads 更严谨
    import json
    j = json.loads(data)
    milestone = j["milestones"][str(major)]
    downloads = milestone["downloads"]["chromedriver"]
    dl = next((x for x in downloads if x["platform"] == tag), None)
    if not dl:
        raise RuntimeError(f"未找到 {major=} {tag=} 的 chromedriver 下载信息")

    zip_url = dl["url"]
    print(f"Downloading: {zip_url}")

    zbytes = urlopen(zip_url, timeout=60).read()
    z = zipfile.ZipFile(io.BytesIO(zbytes))

    # zip 内部一般是 chromedriver-<platform>/chromedriver(.exe)
    member = [m for m in z.namelist() if m.endswith("chromedriver") or m.endswith("chromedriver.exe")][0]
    extracted = z.read(member)

    exe_name = "chromedriver.exe" if platform.system().lower().startswith("win") else "chromedriver"
    out_path = OUT_DIR / exe_name
    out_path.write_bytes(extracted)

    if not platform.system().lower().startswith("win"):
        out_path.chmod(0o755)

    return out_path

if __name__ == "__main__":
    major = detect_chrome_major()
    print(f"Detected Chrome major version: {major}")
    p = download_chromedriver_for_major(major)
    print(f"Saved chromedriver to: {p}")
    print("Now set web_env.yaml driver_path to: bin/drivers/chromedriver (or .exe on Windows)")
