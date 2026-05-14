# -*- coding: utf-8 -*-
"""从 Playwright storage_state 或旧版 CDP 用户目录导出小红书 Cookie 列表。

默认读取 cookiesFile/xhs/session.json（由爬虫正常结束且登录成功时自动写入）。
若不存在，可尝试旧路径 browser_data/cdp_xhs_user_data_dir（需关闭占用该目录的 Chrome）。

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
from tools.playwright_session import (  # noqa: E402
    chromium_shared_launch_args,
    session_path_for_platform,
)


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


def _cookies_from_storage_state(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    raw = data.get("cookies")
    if not isinstance(raw, list):
        return []
    return raw


async def _main() -> int:
    site_key = "rednote.com" if config.XHS_INTERNATIONAL else "xiaohongshu"
    session_path = session_path_for_platform("xhs")
    cookies: list[dict] = []

    if session_path.is_file():
        try:
            cookies = _cookies_from_storage_state(str(session_path))
        except (OSError, json.JSONDecodeError) as e:
            print(f"[export_xhs_cookies] 读取 {session_path} 失败: {e}")
            return 1
        print(f"[export_xhs_cookies] 自 {session_path} 读取 storage_state")
    else:
        prof = _cdp_profile_dir()
        if not os.path.isdir(prof):
            print(
                f"[export_xhs_cookies] 未找到 {session_path}，也未找到旧目录 {prof}。\n"
                "请先运行一次小红书爬虫并完成登录（会生成 cookiesFile/xhs/session.json）。"
            )
            return 1

        async with async_playwright() as p:
            try:
                context = await p.chromium.launch_persistent_context(
                    prof,
                    headless=True,
                    channel="chrome",
                    viewport={"width": 1280, "height": 800},
                    args=chromium_shared_launch_args(),
                )
            except Exception as e:
                print(
                    f"[export_xhs_cookies] 无法用 channel=chrome 打开旧 CDP 配置目录: {e}\n"
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
            finally:
                await context.close()
        print(f"[export_xhs_cookies] 自旧目录导出: {prof}")

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
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
