# -*- coding: utf-8 -*-
"""Normalize Xiaohongshu note URLs for Feishu storage (keep xsec_token in query)."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse


def normalize_xhs_note_url(url: str, *, international: bool = False) -> str:
    """
    Strip fragment, normalize scheme/host; preserve query (xsec_token, xsec_source, etc.).
    """
    if not url or not isinstance(url, str):
        return ""
    u = url.strip()
    if not u:
        return ""
    parsed = urlparse(u)
    scheme = (parsed.scheme or "https").lower()
    if scheme not in ("http", "https"):
        scheme = "https"
    netloc = (parsed.netloc or "").strip().lower()
    path = parsed.path or "/"
    query = parsed.query or ""

    if international:
        if "xiaohongshu.com" in netloc:
            netloc = "www.rednote.com"
    else:
        if "rednote.com" in netloc:
            netloc = "www.xiaohongshu.com"

    return urlunparse((scheme, netloc, path, "", query, ""))
