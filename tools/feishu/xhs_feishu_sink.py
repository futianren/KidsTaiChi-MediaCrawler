# -*- coding: utf-8 -*-
"""
Buffer Xiaohongshu notes and sync new rows to Feishu Bitable (dedupe by 笔记ID).
"""

from __future__ import annotations

import asyncio
import logging

import config
from tools import utils
from var import crawler_type_var

_lock = asyncio.Lock()
_pending: list[tuple[str, str, str]] = []
_session_enqueued: set[str] = set()
_created_this_run: set[str] = set()
_client: LarkBitableClient | None = None
_warned_incomplete = False

# 统计指标
_stats_crawled = 0  # 本次抓取总数
_stats_new = 0  # 新增到飞书
_stats_duplicate = 0  # 重复跳过
_stats_failed = 0  # 写入失败


def _lark_settings() -> dict:
    return {
        "app_id": config.FEISHU_APP_ID,
        "app_secret": config.FEISHU_APP_SECRET,
        "app_token": config.FEISHU_APP_TOKEN,
        "table_id": config.FEISHU_TABLE_ID,
        "field_note_id": config.FEISHU_FIELD_NOTE_ID,
        "field_title": config.FEISHU_FIELD_TITLE,
        "field_link": config.FEISHU_FIELD_LINK,
        "field_publish": config.FEISHU_FIELD_PUBLISH,
        "publish_value": config.FEISHU_PUBLISH_VALUE_ON_CREATE,
        "link_field_format": config.FEISHU_LINK_FIELD_FORMAT,
        "xhs_international": bool(getattr(config, "XHS_INTERNATIONAL", False)),
        "timeout_sec": config.FEISHU_HTTP_TIMEOUT_SEC,
        "max_or_conditions": config.FEISHU_MAX_OR_CONDITIONS,
        "retries": config.FEISHU_RETRIES,
        "retry_backoff_sec": config.FEISHU_RETRY_BACKOFF_SEC,
    }


def _credentials_ok() -> bool:
    return bool(
        config.FEISHU_APP_ID
        and config.FEISHU_APP_SECRET
        and config.FEISHU_APP_TOKEN
        and config.FEISHU_TABLE_ID
    )


def _should_sync() -> bool:
    if not getattr(config, "FEISHU_SYNC_ENABLED", False):
        return False
    if getattr(config, "PLATFORM", "") != "xhs":
        return False
    ct = (crawler_type_var.get() or "").strip().lower()
    allowed = getattr(config, "FEISHU_SYNC_CRAWLER_TYPES", frozenset({"creator"}))
    return ct in allowed


def _get_client() -> LarkBitableClient:
    global _client
    if _client is None:
        from tools.feishu.lark_bitable_client import LarkBitableClient

        _client = LarkBitableClient(_lark_settings())
    return _client


def reset_for_tests() -> None:
    """Clear module state (tests only)."""
    global _pending, _session_enqueued, _created_this_run, _client, _warned_incomplete
    global _stats_crawled, _stats_new, _stats_duplicate, _stats_failed
    _pending = []
    _session_enqueued = set()
    _created_this_run = set()
    _client = None
    _warned_incomplete = False
    _stats_crawled = 0
    _stats_new = 0
    _stats_duplicate = 0
    _stats_failed = 0


async def enqueue(note_id: str | None, title: str | None, note_url: str | None) -> None:
    global _warned_incomplete, _stats_crawled
    if not _should_sync():
        return
    if not _credentials_ok():
        if not _warned_incomplete:
            _warned_incomplete = True
            utils.logger.warning(
                "[xhs_feishu_sink] FEISHU_SYNC_ENABLED 已开启但凭证不完整，跳过飞书写入"
            )
        return
    nid = (note_id or "").strip()
    if not nid:
        return
    async with _lock:
        if nid in _session_enqueued:
            return
        _session_enqueued.add(nid)
        _pending.append((nid, (title or "").strip(), (note_url or "").strip()))
        _stats_crawled += 1


async def flush() -> None:
    if not getattr(config, "FEISHU_SYNC_ENABLED", False):
        return
    if getattr(config, "PLATFORM", "") != "xhs":
        return
    if not _credentials_ok():
        return

    async with _lock:
        if not _pending:
            return
        snapshot = list(_pending)
        _pending.clear()

    deduped: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for item in snapshot:
        nid = item[0]
        if nid in seen:
            continue
        seen.add(nid)
        deduped.append(item)

    ids = [nid for nid, _, _ in deduped if nid not in _created_this_run]
    if not ids:
        return

    loop = asyncio.get_running_loop()
    client = _get_client()

    try:
        existing = await loop.run_in_executor(None, client.search_existing_note_ids, ids)
    except Exception as exc:
        utils.logger.exception("[xhs_feishu_sink] 飞书判重失败: %s", exc)
        async with _lock:
            _pending.extend([x for x in deduped if x[0] not in _created_this_run])
        return

    to_insert = [
        (nid, title, url)
        for nid, title, url in deduped
        if nid not in existing and nid not in _created_this_run
    ]

    # 统计重复数量
    global _stats_duplicate
    duplicate_count = len(deduped) - len(to_insert)
    _stats_duplicate += duplicate_count

    if not to_insert:
        utils.logger.info(
            "[xhs_feishu_sink] 飞书无需新增（均在表中或本轮已写） note_count=%s",
            len(deduped),
        )
        return

    try:
        ok, fail = await loop.run_in_executor(
            None, lambda: client.batch_create_xhs_notes(to_insert)
        )
    except Exception as exc:
        utils.logger.exception("[xhs_feishu_sink] 飞书 batch_create 失败: %s", exc)
        async with _lock:
            _pending.extend(to_insert)
        return

    # 更新统计
    global _stats_new, _stats_failed
    _stats_new += ok
    _stats_failed += fail

    utils.logger.info(
        "[xhs_feishu_sink] 飞书写入完成 ok=%s fail=%s submitted=%s",
        ok,
        fail,
        len(to_insert),
    )
    if fail:
        logging.error("[xhs_feishu_sink] 飞书写入失败条数: %s", fail)

    async with _lock:
        if fail == 0:
            for nid, _, _ in to_insert:
                _created_this_run.add(nid)
        else:
            _pending.extend(to_insert)


def get_stats() -> dict[str, int]:
    """
    获取当前运行的统计数据

    Returns:
        包含统计指标的字典
    """
    return {
        "crawled": _stats_crawled,
        "new": _stats_new,
        "duplicate": _stats_duplicate,
        "failed": _stats_failed,
    }
