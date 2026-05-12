# -*- coding: utf-8 -*-
"""从 CDP 持久化目录导出小红书 Cookie，供无头或下次启动复用。

使用前请先在本项目用扫码登录跑过一次（生成 browser_data/cdp_xhs_user_data_dir）。
关闭爬虫打开的 Chrome 后再运行本脚本，避免用户目录被占用。

用法（在项目根目录）:
    python tools/export_xhs_cookies.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

from tools.crawler_util import convert_cookies  # noqa: E402


def _cdp_profile_dir() -> str:
    return os.path.join(ROOT, "browser_data", f"cdp_{config.USER_DATA_DIR % config.PLATFORM}")


def _sanitize_for_add(cookies: list[dict]) -> list[dict]:
    allowed = ("name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite")
    out: list[dict] = []
    valid_same = {"Strict", "Lax", "None"}
    for c in cookies:
        row = {k: c[k] for k in allowed if k in c and c[k] is not None}
        ss = row.get("sameSite")
        if isinstance(ss, str) and ss not in valid_same:
            row.pop("sameSite", None)
        if "name" in row and "value" in row and "domain" in row:
            out.append(row)
    return out


async def _main() -> int:
    prof = _cdp_profile_dir()
    if not os.path.isdir(prof):
        print(f"[export_xhs_cookies] 未找到目录: {prof}，请先在本项目完成一次小红书扫码登录。")
        return 1

    site_key = "rednote.com" if config.XHS_INTERNATIONAL else "xiaohongshu"

    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                prof,
                headless=True,
                channel="chrome",
                viewport={"width": 1280, "height": 800},
            )
        except Exception as e:
            print(
                f"[export_xhs_cookies] 无法用 channel=chrome 打开配置目录: {e}\n"
                "请确认已安装 Google Chrome，或关闭正在占用该用户目录的浏览器后重试。"
            )
            return 1

        try:
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(
                "https://www.rednote.com" if config.XHS_INTERNATIONAL else "https://www.xiaohongshu.com",
                wait_until="domcontentloaded",
                timeout=90000,
            )
            await asyncio.sleep(2)
            cookies = await context.cookies()
            filtered = [c for c in cookies if site_key in (c.get("domain") or "").lower()]
            cleaned = _sanitize_for_add(filtered)

            data_dir = os.path.join(ROOT, "data")
            os.makedirs(data_dir, exist_ok=True)
            jpath = os.path.join(data_dir, "xhs_browser_cookies.json")
            with open(jpath, "w", encoding="utf-8") as f:
                json.dump(cleaned, f, ensure_ascii=False, indent=2)

            cookie_str, _ = convert_cookies(filtered)
            spath = os.path.join(data_dir, "xhs_cookie_string.txt")
            with open(spath, "w", encoding="utf-8") as f:
                f.write(cookie_str)

            print(f"[export_xhs_cookies] 已写入 {jpath}（{len(cleaned)} 条）与 {spath}")
        finally:
            await context.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
