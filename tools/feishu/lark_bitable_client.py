# -*- coding: utf-8 -*-
"""Lark / Feishu Bitable client for Xiaohongshu note rows (search by note id + batch create)."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from tools.feishu.xhs_note_url import normalize_xhs_note_url

_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

_FEISHU_RETRYABLE_CODES = frozenset({99991429, 99991428, 99991463})


def _field_to_primitive(field: Any) -> str:
    if field is None:
        return ""
    if isinstance(field, str):
        return field.strip()
    if isinstance(field, (int, float)):
        return str(int(field)) if isinstance(field, float) and field.is_integer() else str(field)
    if isinstance(field, list) and field:
        first = field[0]
        if isinstance(first, dict):
            return str(first.get("text") or first.get("value") or "").strip()
        return str(first).strip()
    if isinstance(field, dict):
        return str(field.get("text") or field.get("value") or "").strip()
    return str(field).strip()


class LarkBitableClient:
    def __init__(self, settings: dict[str, Any]):
        self.app_id = str(settings.get("app_id", "")).strip()
        self.app_secret = str(settings.get("app_secret", "")).strip()
        self.app_token = str(settings.get("app_token", "")).strip()
        self.table_id = str(settings.get("table_id", "")).strip()
        self.field_note_id = str(settings.get("field_note_id", "笔记ID")).strip() or "笔记ID"
        self.field_title = str(settings.get("field_title", "笔记标题")).strip() or "笔记标题"
        self.field_link = str(settings.get("field_link", "笔记链接")).strip() or "笔记链接"
        self.field_publish = str(settings.get("field_publish", "是否发布")).strip() or "是否发布"
        self.publish_value = str(settings.get("publish_value", "否")).strip() or "否"
        raw_multi = settings.get("publish_fields_on_create") or {}
        self.publish_fields_on_create = {
            str(k).strip(): str(v).strip()
            for k, v in raw_multi.items()
            if str(k).strip()
        }
        self.link_field_format = str(settings.get("link_field_format", "object")).strip().lower()
        self.xhs_international = bool(settings.get("xhs_international", False))
        self.timeout_sec = int(settings.get("timeout_sec", 30))
        self.max_or_conditions = max(5, int(settings.get("max_or_conditions", 25)))
        self.retries = max(1, int(settings.get("retries", 3)))
        self.retry_backoff_sec = float(settings.get("retry_backoff_sec", 1.0))

        self._access_token: str | None = None
        self._token_expire_at: float = 0.0

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        h = dict(headers or {})
        last_err: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                resp = requests.request(
                    method,
                    url,
                    json=json_body,
                    headers=h,
                    timeout=self.timeout_sec,
                )
                if resp.status_code == 429 and attempt < self.retries:
                    wait = min(60, max(1, int(resp.headers.get("Retry-After", "3") or 3)))
                    logging.warning("飞书 HTTP 429，%s 秒后重试 (attempt=%s)", wait, attempt)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict):
                    c = data.get("code")
                    if (
                        c not in (0, None)
                        and c in _FEISHU_RETRYABLE_CODES
                        and attempt < self.retries
                    ):
                        wait = min(30, self.retry_backoff_sec * (2 ** (attempt - 1)))
                        logging.warning("飞书业务限流 code=%s，%s 秒后重试", c, wait)
                        time.sleep(wait)
                        continue
                return data
            except (requests.RequestException, ValueError) as exc:
                last_err = exc
                logging.warning("飞书 API 请求失败 attempt=%s/%s: %s", attempt, self.retries, exc)
                if attempt < self.retries:
                    time.sleep(self.retry_backoff_sec * (2 ** (attempt - 1)))
        raise last_err or RuntimeError("飞书 API 请求失败")

    def get_tenant_access_token(self) -> str:
        now = time.time()
        if self._access_token and self._token_expire_at > now + 120:
            return self._access_token

        data = self._request_json(
            "POST",
            _TOKEN_URL,
            json_body={"app_id": self.app_id, "app_secret": self.app_secret},
        )
        if data.get("code") != 0:
            raise RuntimeError(f"获取 tenant_access_token 失败: {data.get('msg')!r} body={data!r}")

        token = data.get("tenant_access_token")
        if not token:
            raise RuntimeError(f"tenant_access_token 为空: {data!r}")
        expire = int(data.get("expire", 7200))
        self._access_token = token
        self._token_expire_at = now + expire
        return token

    def _auth_headers(self) -> dict[str, str]:
        token = self.get_tenant_access_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def search_existing_note_ids(self, note_ids: list[str]) -> set[str]:
        """Return note ids that already exist in the table (full-table search, no view_id)."""
        ids = sorted({x.strip() for x in note_ids if x and str(x).strip()})
        if not ids:
            return set()

        base = (
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/"
            f"{self.app_token}/tables/{self.table_id}/records/search"
        )
        found: set[str] = set()

        for i in range(0, len(ids), self.max_or_conditions):
            chunk = ids[i : i + self.max_or_conditions]
            conditions = [
                {
                    "field_name": self.field_note_id,
                    "operator": "is",
                    "value": [nid],
                }
                for nid in chunk
            ]
            page_token: str | None = None
            while True:
                body: dict[str, Any] = {
                    "filter": {"conjunction": "or", "conditions": conditions},
                    "page_size": 500,
                }
                if page_token:
                    body["page_token"] = page_token

                data = self._request_json("POST", base, headers=self._auth_headers(), json_body=body)
                if data.get("code") != 0:
                    raise RuntimeError(f"飞书 search 失败: {data.get('msg')!r} body={data!r}")

                items = data.get("data", {}).get("items") or []
                for item in items:
                    fields = item.get("fields") or {}
                    raw = fields.get(self.field_note_id)
                    val = _field_to_primitive(raw)
                    if val:
                        found.add(val)

                if data.get("data", {}).get("has_more"):
                    page_token = data.get("data", {}).get("page_token")
                    if not page_token:
                        break
                else:
                    break

        return found

    def _link_value(self, url: str) -> str | dict[str, str]:
        normalized = normalize_xhs_note_url(url, international=self.xhs_international)
        if self.link_field_format == "plain":
            return normalized
        return {"link": normalized, "text": normalized}

    def batch_create_xhs_notes(
        self, items: list[tuple[str, str, str]]
    ) -> tuple[int, int]:
        """
        Create rows. items: (note_id, title, note_url)
        Returns (success_count, fail_count).
        """
        if not items:
            return 0, 0

        url = (
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/"
            f"{self.app_token}/tables/{self.table_id}/records/batch_create"
        )
        batch_size = 100
        ok_total = 0
        fail_total = 0

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            records = []
            for note_id, title, link in batch:
                fields: dict[str, Any] = {
                    self.field_note_id: str(note_id).strip(),
                    self.field_title: title or "",
                    self.field_link: self._link_value(link),
                }
                if self.publish_fields_on_create:
                    fields.update(self.publish_fields_on_create)
                else:
                    fields[self.field_publish] = self.publish_value
                records.append({"fields": fields})
            body = {"records": records}
            data = self._request_json("POST", url, headers=self._auth_headers(), json_body=body)
            if data.get("code") != 0:
                logging.error("飞书 batch_create 失败: %s 本批条数=%s", data, len(batch))
                fail_total += len(batch)
                continue

            created = data.get("data", {}).get("records") or []
            ok_total += len(created)
            fail_total += len(batch) - len(created)
            if len(created) != len(batch):
                logging.warning(
                    "飞书 batch_create 返回条数与提交不一致 submitted=%s returned=%s raw=%s",
                    len(batch),
                    len(created),
                    data,
                )

        return ok_total, fail_total
