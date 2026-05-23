# -*- coding: utf-8 -*-
"""
飞书多维表同步相关配置。

凭证优先顺序：
1) 环境变量 FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_APP_TOKEN / FEISHU_TABLE_ID
2) 本机文件 config/feishu_secrets_local.py（见 feishu_secrets_local.example.py）

开关 FEISHU_SYNC_ENABLED：若设置环境变量则优先生效，否则使用 secrets 文件中的默认值。
"""

from __future__ import annotations

import os

try:
    from . import feishu_secrets_local as _secrets  # type: ignore
except ImportError:
    _secrets = None  # type: ignore


def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name)
    return (v or default).strip()


def _from_local_or_env(key: str) -> str:
    if _secrets is not None:
        v = getattr(_secrets, key, None)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return _env(key)


def _parse_env_bool(name: str) -> bool | None:
    raw = os.environ.get(name)
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if s == "":
        return None
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return None


_env_sync = _parse_env_bool("FEISHU_SYNC_ENABLED")
if _env_sync is not None:
    FEISHU_SYNC_ENABLED = _env_sync
else:
    FEISHU_SYNC_ENABLED = bool(
        getattr(_secrets, "FEISHU_SYNC_ENABLED", False) if _secrets is not None else False
    )

FEISHU_APP_ID = _from_local_or_env("FEISHU_APP_ID")
FEISHU_APP_SECRET = _from_local_or_env("FEISHU_APP_SECRET")
FEISHU_APP_TOKEN = _from_local_or_env("FEISHU_APP_TOKEN")
FEISHU_TABLE_ID = _from_local_or_env("FEISHU_TABLE_ID")
FEISHU_VIEW_ID = _from_local_or_env("FEISHU_VIEW_ID")

# 多维表格段名（与方案及确认的列名一致）
FEISHU_FIELD_NOTE_ID = _env("FEISHU_FIELD_NOTE_ID", "笔记ID") or "笔记ID"
FEISHU_FIELD_TITLE = _env("FEISHU_FIELD_TITLE", "笔记标题") or "笔记标题"
FEISHU_FIELD_LINK = _env("FEISHU_FIELD_LINK", "笔记链接") or "笔记链接"
FEISHU_FIELD_PUBLISH = _env("FEISHU_FIELD_PUBLISH", "是否发布") or "是否发布"
FEISHU_PUBLISH_VALUE_ON_CREATE = _env("FEISHU_PUBLISH_VALUE_ON_CREATE", "否") or "否"
# 多平台「是否发布」列（项目级 publish_fields_on_create 覆盖；默认空）
FEISHU_PUBLISH_FIELDS_ON_CREATE: dict[str, str] = {}

# 链接列：plain 纯文本 | object 飞书 URL 字段常用 {"link","text"}
FEISHU_LINK_FIELD_FORMAT = (_env("FEISHU_LINK_FIELD_FORMAT", "object") or "object").lower()

FEISHU_HTTP_TIMEOUT_SEC = int(_env("FEISHU_HTTP_TIMEOUT_SEC", "30") or "30")
FEISHU_MAX_OR_CONDITIONS = int(_env("FEISHU_MAX_OR_CONDITIONS", "25") or "25")
FEISHU_RETRIES = int(_env("FEISHU_RETRIES", "3") or "3")
FEISHU_RETRY_BACKOFF_SEC = float(_env("FEISHU_RETRY_BACKOFF_SEC", "1") or "1")

# 逗号分隔：creator | search | detail；默认仅 creator，避免搜索/指定笔记模式误写表
_raw_ct = _env("FEISHU_SYNC_CRAWLER_TYPES", "creator")
FEISHU_SYNC_CRAWLER_TYPES: frozenset[str] = frozenset(
    x.strip().lower() for x in _raw_ct.split(",") if x.strip()
)
