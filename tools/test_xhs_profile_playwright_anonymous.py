# -*- coding: utf-8 -*-
"""
Playwright 打开小红书用户主页（全新上下文，不加载项目 data 下 Cookie / 不登录账号）。

支持尽量模拟真实用户：系统 Chrome、弱化自动化特征、先逛首页再进主页、滚动触发懒加载等。

用法（项目根目录）:
    python tools/test_xhs_profile_playwright_anonymous.py [可选 URL] \\
        [--headed] [--chrome] [--no-stealth] [--real] [--slowmo=80]

  --real   推荐：先打开首页、随机等待、再进用户页，并向下滚动多屏
  --headed 有头模式（更接近你手动浏览；需本机图形环境）
  --chrome 使用本机 Google Chrome（需已安装）
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
STEALTH = ROOT / "libs" / "stealth.min.js"

DEFAULT_PROFILE = (
    "https://www.xiaohongshu.com/user/profile/599a866c6a6a691b72914f22/"
    "?xsec_token=ABUoa8EkF6TS7kYqrHt2-J5908KLYwpJfDjAaN-lQHjIs=&xsec_source=pc_user"
)

# 较新的 Chrome UA（可按需更新）
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

EXTRA_HEADERS = {
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Upgrade-Insecure-Requests": "1",
}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="匿名 Playwright 打开小红书用户主页探测")
    p.add_argument("url", nargs="?", default=DEFAULT_PROFILE, help="用户主页完整 URL")
    p.add_argument("--headed", action="store_true", help="有头模式")
    p.add_argument("--chrome", action="store_true", help="使用 channel=chrome")
    p.add_argument("--no-stealth", action="store_true", help="不注入 stealth.min.js")
    p.add_argument(
        "--real",
        action="store_true",
        help="模拟真实路径：首页预热 + 随机等待 + 滚动懒加载",
    )
    p.add_argument("--slowmo", type=int, default=0, help="操作间隔毫秒，有头时更易观察")
    return p.parse_args(argv)


async def _warmup_and_profile(page, profile_url: str, use_real: bool) -> None:
    if use_real:
        print("[playwright_anon] warmup: goto https://www.xiaohongshu.com/explore")
        await page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded", timeout=60_000)
        await asyncio.sleep(random.uniform(2.0, 4.5))
        try:
            await page.mouse.move(random.randint(200, 800), random.randint(200, 600))
        except Exception:
            pass

    print(f"[playwright_anon] goto profile")
    resp = await page.goto(profile_url, wait_until="domcontentloaded", timeout=90_000)
    print(f"[playwright_anon] profile first_response_status={resp.status if resp else None}")

    try:
        await page.wait_for_load_state("networkidle", timeout=50_000)
    except Exception as e:
        print(f"[playwright_anon] networkidle: {e}")

    await asyncio.sleep(random.uniform(3.0, 5.5))

    if use_real:
        print("[playwright_anon] scroll to trigger lazy load")
        await page.evaluate(
            """async () => {
                const step = 700;
                const delay = (ms) => new Promise((r) => setTimeout(r, ms));
                for (let i = 0; i < 8; i++) {
                    window.scrollBy(0, step);
                    await delay(600 + Math.random() * 400);
                }
            }"""
        )
        await asyncio.sleep(2.0)


async def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    profile_url = args.url

    print(f"[playwright_anon] profile_url={profile_url}")
    print(
        f"[playwright_anon] headed={args.headed} chrome_channel={args.chrome} "
        f"no_stealth={args.no_stealth} real_user_flow={args.real} slowmo={args.slowmo}"
    )
    print("[playwright_anon] 不加载项目 Cookie 文件 / 不执行登录")

    launch_kwargs: dict = {
        "headless": not args.headed,
        "slow_mo": args.slowmo or None,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080",
        ],
        "ignore_default_args": ["--enable-automation"],
    }
    if launch_kwargs["slow_mo"] is None:
        del launch_kwargs["slow_mo"]
    if args.chrome:
        launch_kwargs["channel"] = "chrome"

    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=UA,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            color_scheme="light",
            extra_http_headers=EXTRA_HEADERS,
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
        )
        if STEALTH.is_file() and not args.no_stealth:
            await context.add_init_script(path=str(STEALTH))
        page = await context.new_page()

        await _warmup_and_profile(page, profile_url, args.real)

        final_url = page.url
        html = await page.content()
        title = await page.title()
        body_text = await page.evaluate("() => (document.body && document.body.innerText) || ''")

        print(f"[playwright_anon] final_url={final_url}")
        print(f"[playwright_anon] document.title={title!r}")
        print(f"[playwright_anon] html_len={len(html)} body_innerText_len={len(body_text)}")

        probe_titles = ("接纳节奏", "太极萱萱", "笔记", "explore", "安全限制", "访问链接异常")
        for kw in probe_titles:
            print(f"[playwright_anon] body has {kw!r}: {kw in body_text}")

        explore_hrefs = await page.evaluate(
            """() => [...document.querySelectorAll('a[href*="/explore/"]')]
                .map(a => a.getAttribute('href')).filter(Boolean)"""
        )
        uniq_h = list(dict.fromkeys(explore_hrefs))
        print(f"[playwright_anon] explore <a> count={len(explore_hrefs)} unique={len(uniq_h)}")
        for h in uniq_h[:15]:
            print(f"    {h}")

        note_ids = sorted(set(re.findall(r"/explore/([0-9a-f]{24})", html)))
        print(f"[playwright_anon] regex note_id in html: {len(note_ids)}")

        m = re.search(r"<script>window.__INITIAL_STATE__=(.+?)</script>", html, re.S)
        print(f"[playwright_anon] __INITIAL_STATE__ script matched: {bool(m)}")
        if m:
            print(f"[playwright_anon] __INITIAL_STATE__ raw_len={len(m.group(1))}")

        # 可见链接文案采样（便于肉眼看「像不像笔记列表」）
        link_samples = await page.evaluate(
            """() => {
                const out = [];
                for (const a of document.querySelectorAll('a')) {
                    const t = (a.innerText || '').trim().replace(/\\s+/g, ' ');
                    const h = a.getAttribute('href') || '';
                    if (t.length > 4 && t.length < 80) out.push({ text: t.slice(0, 60), href: h.slice(0, 120) });
                    if (out.length >= 40) break;
                }
                return out;
            }"""
        )
        print(f"[playwright_anon] visible link text samples: {len(link_samples)}")
        for item in link_samples[:20]:
            print(f"    {item}")

        report = {
            "profile_url": profile_url,
            "headed": args.headed,
            "chrome_channel": args.chrome,
            "no_stealth": args.no_stealth,
            "real_user_flow": args.real,
            "final_url": final_url,
            "document_title": title,
            "html_len": len(html),
            "body_inner_text_len": len(body_text),
            "body_preview": body_text[:4000],
            "explore_href_unique": uniq_h[:50],
            "note_ids_regex": note_ids[:50],
            "link_text_samples": link_samples[:30],
        }
        out_report = ROOT / "data" / "xhs_playwright_anon_report.json"
        out_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        out_html = ROOT / "data" / "xhs_headless_anonymous_profile.html"
        out_txt = ROOT / "data" / "xhs_headless_anonymous_profile_body.txt"
        out_html.write_text(html[:800_000], encoding="utf-8")
        out_txt.write_text(body_text[:200_000], encoding="utf-8")
        print(f"[playwright_anon] wrote {out_report}, {out_html}, {out_txt}")

        await browser.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
