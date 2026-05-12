# -*- coding: utf-8 -*-
"""分析匿名 GET 小红书页面时，响应里实际包含哪些可提取信息。"""
from __future__ import annotations

import re
import sys
from html import unescape
from urllib.parse import parse_qs, urlparse

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.xiaohongshu.com/",
}

PROFILE_URL = (
    "https://www.xiaohongshu.com/user/profile/599a866c6a6a691b72914f22/"
    "?xsec_token=ABUoa8EkF6TS7kYqrHt2-J5908KLYwpJfDjAaN-lQHjIs=&xsec_source=pc_user"
)
NOTE_ID = "69fe8d4d0000000023015caa"
EXPLORE_URL = f"https://www.xiaohongshu.com/explore/{NOTE_ID}"


def _meta_content(html: str, prop_or_name: str, *, prop: bool = True) -> list[str]:
    attr = "property" if prop else "name"
    pat = rf'<meta[^>]+{attr}="{re.escape(prop_or_name)}"[^>]+content="([^"]*)"'
    found = re.findall(pat, html, flags=re.I)
    alt = rf'<meta[^>]+content="([^"]*)"[^>]+{attr}="{re.escape(prop_or_name)}"'
    found += re.findall(alt, html, flags=re.I)
    return [unescape(x) for x in found]


def _title_tag(html: str) -> str | None:
    m = re.search(r"<title>([^<]*)</title>", html, re.I)
    return unescape(m.group(1).strip()) if m else None


def _url_query_info(url: str) -> dict:
    q = parse_qs(urlparse(url).query)
    out: dict = {}
    for k in ("error_code", "error_msg", "redirectPath", "uuid", "verifyMsg", "source"):
        if k in q:
            out[k] = q[k][0] if len(q[k]) == 1 else q[k]
    return out


def analyze(label: str, url: str) -> None:
    print(f"\n========== {label} ==========")
    print(f"URL: {url}")
    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=45.0) as c:
        r = c.get(url)
    html = r.text
    print(f"status={r.status_code}")
    print(f"final_url={r.url}")
    print(f"html_bytes={len(html.encode('utf-8'))}")

    print("\n--- 从最终 URL 查询串可读的「页面意图」---")
    qi = _url_query_info(str(r.url))
    for k, v in qi.items():
        print(f"  {k}: {v}")

    print("\n--- HTML 中的 <title> ---")
    print(f"  {_title_tag(html)!r}")

    print("\n--- 常见 Open Graph / SEO meta ---")
    for key in ("og:title", "og:description", "og:url", "og:image", "description", "keywords", "robots"):
        prop = key.startswith("og:")
        vals = _meta_content(html, key, prop=prop)
        if vals:
            print(f"  {key}: {vals[0][:500]!r}{'...' if len(vals[0]) > 500 else ''}")

    print("\n--- 正文中的关键标记 ---")
    markers = [
        "__INITIAL_STATE__",
        "noteDetailMap",
        "userPageData",
        "请通过验证",
        "登录",
        "访问链接异常",
        "暂时无法浏览",
        "300017",
        "300031",
    ]
    for m in markers:
        print(f"  contains {m!r}: {m in html}")

    ld = re.findall(
        r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        flags=re.S | re.I,
    )
    print(f"\n--- application/ld+json 块数量: {len(ld)} ---")
    for i, block in enumerate(ld[:3]):
        print(f"  block[{i}] len={len(block)} preview={block[:180]!r}...")

    # 是否出现笔记 id 字面量
    print(f"\n--- 笔记 id 在正文中出现次数: {html.count(NOTE_ID)} (仅 explore 测试有意义) ---")


def main() -> int:
    analyze("用户主页（匿名）", PROFILE_URL)
    analyze("笔记详情 explore（匿名，无 xsec）", EXPLORE_URL)
    print(
        "\n说明：以上为当前网络环境下、单次请求观测结果；"
        "小红书可能随时间调整返回结构与风控策略。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
