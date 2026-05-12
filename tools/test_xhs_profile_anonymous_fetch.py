# -*- coding: utf-8 -*-
"""
匿名 GET 用户主页（不读 data/xhs_browser_cookies.json、不注入 Cookie），
探测 HTML 中是否包含笔记 id 等结构化信息。

用法（项目根目录）:
    python tools/test_xhs_profile_anonymous_fetch.py [可选：完整用户主页 URL]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Optional, Set

import httpx

DEFAULT_URL = (
    "https://www.xiaohongshu.com/user/profile/599a866c6a6a691b72914f22/"
    "?xsec_token=ABUoa8EkF6TS7kYqrHt2-J5908KLYwpJfDjAaN-lQHjIs=&xsec_source=pc_user"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.xiaohongshu.com/",
}


def _load_known_note_ids(jsonl_path: Path) -> Set[str]:
    ids: Set[str] = set()
    if not jsonl_path.is_file():
        return ids
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            nid = json.loads(line).get("note_id")
            if isinstance(nid, str) and len(nid) == 24:
                ids.add(nid)
        except json.JSONDecodeError:
            continue
    return ids


def _extract_initial_state(html: str) -> Optional[Any]:
    m = re.search(r"<script>window.__INITIAL_STATE__=(.+?)</script>", html, re.S)
    if not m:
        m = re.search(r"window.__INITIAL_STATE__=({.*})</script>", html, re.S)
    if not m:
        return None
    raw = m.group(1).replace(":undefined", ":null").replace("undefined", '""')
    try:
        return json.loads(raw, strict=False)
    except json.JSONDecodeError:
        return None


def _collect_24hex_note_ids(obj: Any, acc: Set[str], depth: int = 0) -> None:
    if depth > 40:
        return
    pat = re.compile(r"^[0-9a-f]{24}$")
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("noteId", "note_id", "id") and isinstance(v, str) and pat.match(v):
                acc.add(v)
            _collect_24hex_note_ids(v, acc, depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            _collect_24hex_note_ids(item, acc, depth + 1)
    elif isinstance(obj, str) and pat.match(obj):
        acc.add(obj)


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    root = Path(__file__).resolve().parents[1]

    jsonl_candidates = sorted(
        (root / "data" / "taiji_xuanna_creator" / "xhs" / "jsonl").glob("creator_contents_*.jsonl")
    )
    jsonl_path = jsonl_candidates[-1] if jsonl_candidates else Path()
    known = _load_known_note_ids(jsonl_path) if jsonl_path.is_file() else set()

    print(f"[anonymous_fetch] URL={url}")
    print(f"[anonymous_fetch] compare_with={jsonl_path} ({len(known)} ids)")

    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=45.0) as client:
        r = client.get(url)

    print(f"[anonymous_fetch] status={r.status_code} final_url={r.url}")
    print(f"[anonymous_fetch] html_len={len(r.text)}")

    hints = []
    for kw in ("请通过验证", "verify", "captcha", "登录后", "注册"):
        if kw in r.text:
            hints.append(kw)
    if hints:
        print(f"[anonymous_fetch] page_text_hints={hints}")

    st = _extract_initial_state(r.text)
    if st is None:
        print("[anonymous_fetch] __INITIAL_STATE__ 未解析到或 JSON 无效")
        href_ids = set(re.findall(r"/explore/([0-9a-f]{24})", r.text))
        print(f"[anonymous_fetch] regex /explore/ 24hex count={len(href_ids)}")
        if href_ids:
            print(f"[anonymous_fetch] sample={list(href_ids)[:8]}")
    else:
        top = list(st.keys())[:25]
        print(f"[anonymous_fetch] __INITIAL_STATE__ top_keys={top}")
        found: Set[str] = set()
        _collect_24hex_note_ids(st, found)
        print(f"[anonymous_fetch] 24hex ids in state tree (heuristic)={len(found)}")
        for i in sorted(found)[:30]:
            print(f"  {i}")
        if known:
            inter = known & found
            print(f"[anonymous_fetch] overlap_with_saved_jsonl={len(inter)}/{len(known)}")
            if len(inter) < len(known):
                print(
                    f"[anonymous_fetch] only_in_saved (sample)="
                    f"{list(known - found)[:5]}"
                )

    snippet = root / "data" / "xhs_anonymous_profile_snippet.txt"
    snippet.write_text(r.text[:120_000], encoding="utf-8")
    print(f"[anonymous_fetch] wrote first 120k chars -> {snippet}")

    # 附加：用已保存 jsonl 中首行笔记 explore 链接再测一次（仍无 Cookie、无 xsec）
    if known and jsonl_path.is_file():
        first_line = jsonl_path.read_text(encoding="utf-8").splitlines()[0].strip()
        sample_id = json.loads(first_line).get("note_id")
        if sample_id:
            note_url = f"https://www.xiaohongshu.com/explore/{sample_id}"
            print(f"[anonymous_fetch] extra GET note explore (no xsec): {note_url}")
            with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=45.0) as client:
                nr = client.get(note_url)
            print(f"[anonymous_fetch] note_status={nr.status_code} final_url={nr.url}")
            print(f"[anonymous_fetch] note_html_len={len(nr.text)}")
            nst = _extract_initial_state(nr.text)
            print(f"[anonymous_fetch] note_page_has_INITIAL_STATE={nst is not None}")
            if "暂时无法" in nr.text or "300031" in nr.text:
                print("[anonymous_fetch] note_page_hint=当前笔记可能限制匿名浏览(300031 等)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
