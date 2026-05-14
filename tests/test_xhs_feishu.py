# -*- coding: utf-8 -*-
"""Tests for Feishu XHS URL normalization and sink deduplication."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from var import crawler_type_var


def test_normalize_xhs_keeps_query_drops_fragment():
    from tools.feishu.xhs_note_url import normalize_xhs_note_url

    u = "https://www.xiaohongshu.com/explore/abc?xsec_token=XX&xsec_source=pc#frag"
    out = normalize_xhs_note_url(u, international=False)
    assert "xsec_token=XX" in out
    assert "#frag" not in out


def test_xhs_note_type_helpers():
    from media_platform.xhs.help import is_xhs_video_note, should_skip_xhs_note_detail_fetch

    assert is_xhs_video_note({"type": "video", "note_id": "1"}) is True
    assert is_xhs_video_note({"type": "normal", "note_id": "1"}) is False
    assert should_skip_xhs_note_detail_fetch({"type": "normal"}) is True
    assert should_skip_xhs_note_detail_fetch({"type": "video"}) is False
    assert should_skip_xhs_note_detail_fetch({"type": ""}) is False
    assert should_skip_xhs_note_detail_fetch({}) is False


def test_normalize_xhs_swaps_host_when_international():
    from tools.feishu.xhs_note_url import normalize_xhs_note_url

    u = "https://www.xiaohongshu.com/explore/abc?x=1"
    out = normalize_xhs_note_url(u, international=True)
    assert "rednote.com" in out
    assert "x=1" in out


@pytest.mark.asyncio
async def test_feishu_sink_enqueue_dedup_and_flush(monkeypatch):
    import config
    from tools.feishu import xhs_feishu_sink

    xhs_feishu_sink.reset_for_tests()
    monkeypatch.setattr(config, "FEISHU_SYNC_ENABLED", True)
    monkeypatch.setattr(config, "PLATFORM", "xhs")
    monkeypatch.setattr(config, "FEISHU_APP_ID", "app")
    monkeypatch.setattr(config, "FEISHU_APP_SECRET", "sec")
    monkeypatch.setattr(config, "FEISHU_APP_TOKEN", "tok")
    monkeypatch.setattr(config, "FEISHU_TABLE_ID", "tbl")
    monkeypatch.setattr(config, "FEISHU_SYNC_CRAWLER_TYPES", frozenset({"creator"}))
    monkeypatch.setattr(config, "XHS_INTERNATIONAL", False)
    monkeypatch.setattr(config, "FEISHU_FIELD_NOTE_ID", "笔记ID")
    monkeypatch.setattr(config, "FEISHU_FIELD_TITLE", "笔记标题")
    monkeypatch.setattr(config, "FEISHU_FIELD_LINK", "笔记链接")
    monkeypatch.setattr(config, "FEISHU_FIELD_PUBLISH", "是否发布")
    monkeypatch.setattr(config, "FEISHU_PUBLISH_VALUE_ON_CREATE", "否")
    monkeypatch.setattr(config, "FEISHU_LINK_FIELD_FORMAT", "object")
    monkeypatch.setattr(config, "FEISHU_HTTP_TIMEOUT_SEC", 30)
    monkeypatch.setattr(config, "FEISHU_MAX_OR_CONDITIONS", 25)
    monkeypatch.setattr(config, "FEISHU_RETRIES", 3)
    monkeypatch.setattr(config, "FEISHU_RETRY_BACKOFF_SEC", 1.0)

    crawler_type_var.set("creator")

    mock_inst = MagicMock()
    mock_inst.search_existing_note_ids.return_value = set()
    mock_inst.batch_create_xhs_notes.return_value = (1, 0)

    with patch("tools.feishu.lark_bitable_client.LarkBitableClient", return_value=mock_inst):
        await xhs_feishu_sink.enqueue("n1", "t1", "https://www.xiaohongshu.com/explore/n1?x=1")
        await xhs_feishu_sink.enqueue("n1", "t2", "https://www.xiaohongshu.com/explore/n1?x=2")
        await xhs_feishu_sink.flush()

    mock_inst.batch_create_xhs_notes.assert_called_once()
    args, _ = mock_inst.batch_create_xhs_notes.call_args
    assert len(args[0]) == 1
    assert args[0][0][0] == "n1"


@pytest.mark.asyncio
async def test_feishu_sink_skips_when_existing(monkeypatch):
    import config
    from tools.feishu import xhs_feishu_sink

    xhs_feishu_sink.reset_for_tests()
    monkeypatch.setattr(config, "FEISHU_SYNC_ENABLED", True)
    monkeypatch.setattr(config, "PLATFORM", "xhs")
    monkeypatch.setattr(config, "FEISHU_APP_ID", "app")
    monkeypatch.setattr(config, "FEISHU_APP_SECRET", "sec")
    monkeypatch.setattr(config, "FEISHU_APP_TOKEN", "tok")
    monkeypatch.setattr(config, "FEISHU_TABLE_ID", "tbl")
    monkeypatch.setattr(config, "FEISHU_SYNC_CRAWLER_TYPES", frozenset({"creator"}))
    monkeypatch.setattr(config, "XHS_INTERNATIONAL", False)
    for name, val in (
        ("FEISHU_FIELD_NOTE_ID", "笔记ID"),
        ("FEISHU_FIELD_TITLE", "笔记标题"),
        ("FEISHU_FIELD_LINK", "笔记链接"),
        ("FEISHU_FIELD_PUBLISH", "是否发布"),
        ("FEISHU_PUBLISH_VALUE_ON_CREATE", "否"),
        ("FEISHU_LINK_FIELD_FORMAT", "plain"),
        ("FEISHU_HTTP_TIMEOUT_SEC", 30),
        ("FEISHU_MAX_OR_CONDITIONS", 25),
        ("FEISHU_RETRIES", 3),
        ("FEISHU_RETRY_BACKOFF_SEC", 1.0),
    ):
        monkeypatch.setattr(config, name, val)

    crawler_type_var.set("creator")

    mock_inst = MagicMock()
    mock_inst.search_existing_note_ids.return_value = {"n1"}
    mock_inst.batch_create_xhs_notes.return_value = (0, 0)

    with patch("tools.feishu.lark_bitable_client.LarkBitableClient", return_value=mock_inst):
        await xhs_feishu_sink.enqueue("n1", "t1", "https://www.xiaohongshu.com/explore/n1")
        await xhs_feishu_sink.flush()

    mock_inst.batch_create_xhs_notes.assert_not_called()
