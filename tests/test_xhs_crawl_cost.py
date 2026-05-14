# -*- coding: utf-8 -*-
"""XHS crawl cost / preset helpers."""

from __future__ import annotations

import pytest


def test_feishu_minimal_preset_baseline(monkeypatch):
    import config
    from cmd_arg.arg import _maybe_apply_xhs_crawl_preset_baseline

    monkeypatch.setattr(config, "PLATFORM", "dy")
    monkeypatch.setattr(config, "ENABLE_GET_COMMENTS", True)
    _maybe_apply_xhs_crawl_preset_baseline("feishu_minimal")
    assert config.ENABLE_GET_COMMENTS is True

    monkeypatch.setattr(config, "PLATFORM", "xhs")
    monkeypatch.setattr(config, "ENABLE_GET_COMMENTS", True)
    monkeypatch.setattr(config, "ENABLE_GET_SUB_COMMENTS", True)
    monkeypatch.setattr(config, "ENABLE_GET_MEIDAS", True)
    monkeypatch.setattr(config, "XHS_FETCH_CREATOR_PROFILE", True)
    monkeypatch.setattr(config, "XHS_CREATOR_ONLY_VIDEO_NOTES", False)
    monkeypatch.setattr(config, "XHS_NOTE_PERSIST_MODE", "full")
    _maybe_apply_xhs_crawl_preset_baseline("feishu_minimal")
    assert config.ENABLE_GET_COMMENTS is False
    assert config.ENABLE_GET_SUB_COMMENTS is False
    assert config.ENABLE_GET_MEIDAS is False
    assert config.XHS_FETCH_CREATOR_PROFILE is False
    assert config.XHS_CREATOR_ONLY_VIDEO_NOTES is True
    assert config.XHS_NOTE_PERSIST_MODE == "feishu_plus"


def test_maybe_slim_xhs_local_item(monkeypatch):
    import config
    import store.xhs as sx

    full = {
        "note_id": "n1",
        "type": "video",
        "title": "t",
        "desc": "long",
        "video_url": "",
        "time": 1,
        "last_update_time": 0,
        "user_id": "u",
        "nickname": "nn",
        "avatar": "a",
        "liked_count": "1",
        "collected_count": "2",
        "comment_count": "3",
        "share_count": "4",
        "ip_location": "sh",
        "image_list": "",
        "tag_list": "",
        "last_modify_ts": 99,
        "note_url": "https://example.com/n1",
        "source_keyword": "",
        "xsec_token": "tok",
    }
    monkeypatch.setattr(config, "XHS_NOTE_PERSIST_MODE", "full")
    assert sx._maybe_slim_xhs_local_item(full) == full

    monkeypatch.setattr(config, "XHS_NOTE_PERSIST_MODE", "feishu_plus")
    monkeypatch.setattr(config, "SAVE_DATA_OPTION", "jsonl")
    slim = sx._maybe_slim_xhs_local_item(full)
    assert set(slim.keys()) == {"note_id", "title", "note_url", "type"}
    assert slim["note_id"] == "n1"
    assert slim["title"] == "t"
    assert slim["type"] == "video"
    assert slim["note_url"] == "https://example.com/n1"

    monkeypatch.setattr(config, "SAVE_DATA_OPTION", "sqlite")
    assert sx._maybe_slim_xhs_local_item(full) == full


def test_creator_list_item_to_note_item():
    from media_platform.xhs.help import creator_list_item_to_note_item, xhs_creator_list_note_id

    raw = {
        "id": "abc123",
        "title": "hello",
        "type": "video",
        "xsec_token": "tok1",
        "xsec_source": "pc_note",
    }
    assert xhs_creator_list_note_id(raw) == "abc123"
    m = creator_list_item_to_note_item(raw, default_xsec_source="pc_feed", profile_xsec_token="fallback")
    assert m is not None
    assert m["note_id"] == "abc123"
    assert m["title"] == "hello"
    assert m["type"] == "video"
    assert m["xsec_token"] == "tok1"

    no_id = {"title": "x"}
    assert creator_list_item_to_note_item(no_id) is None
