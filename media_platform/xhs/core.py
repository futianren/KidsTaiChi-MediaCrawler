# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/futianren/KidsTaiChi-MediaCrawler/blob/main/media_platform/xhs/core.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

import asyncio
import os
import random
from asyncio import Task
from typing import Dict, List, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    async_playwright,
)
from tenacity import RetryError

import config
from base.base_crawler import AbstractCrawler
from model.m_xiaohongshu import NoteUrlInfo, CreatorUrlInfo
from proxy.proxy_ip_pool import IpInfoModel, create_ip_pool
from store import xhs as xhs_store
from tools import utils
from tools.cdp_browser import CDPBrowserManager
from tools.playwright_session import (
    attach_chromium_browser,
    finalize_standard_playwright,
    session_path_for_platform,
)
from var import crawler_type_var, source_keyword_var

from .client import XiaoHongShuClient
from .exception import DataFetchError, NoteNotFoundError
from .field import SearchSortType
from .help import (
    parse_note_info_from_note_url,
    parse_creator_info_from_url,
    get_search_id,
    is_xhs_video_note,
    should_skip_xhs_note_detail_fetch,
    creator_list_item_to_note_item,
    xhs_creator_list_note_id,
)
from .login import XiaoHongShuLogin, try_load_saved_xhs_cookies


class XiaoHongShuCrawler(AbstractCrawler):
    context_page: Page
    xhs_client: XiaoHongShuClient
    browser_context: BrowserContext
    cdp_manager: Optional[CDPBrowserManager]
    playwright_browser: Optional[Browser]
    _session_persist_ok: bool
    _creator_stats: Dict[str, bool]  # 创作者URL -> 是否成功

    def __init__(self) -> None:
        self.index_url = "https://www.rednote.com" if config.XHS_INTERNATIONAL else "https://www.xiaohongshu.com"
        # 与 XiaoHongShuClient.cookie_urls 一致：导出 cookie 时同时覆盖站点页与 API 域，避免 httpx 请求 edith 时缺 cookie
        if config.XHS_INTERNATIONAL:
            self.cookie_urls = [self.index_url, "https://webapi.rednote.com"]
        else:
            self.cookie_urls = [self.index_url, "https://edith.xiaohongshu.com"]
        # self.user_agent = utils.get_user_agent()
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        self.cdp_manager = None
        self.playwright_browser = None
        self._session_persist_ok = False
        self.ip_proxy_pool = None  # Proxy IP pool for automatic proxy refresh
        # 创作者模式下仅视频笔记落库后，用于拉评论（note_id -> xsec_token）
        self._creator_video_notes_xsec: dict[str, str] = {}
        # 创作者采集统计
        self._creator_stats: Dict[str, bool] = {}

    async def start(self) -> None:
        playwright_proxy_format, httpx_proxy_format = None, None
        if config.ENABLE_IP_PROXY:
            self.ip_proxy_pool = await create_ip_pool(config.IP_PROXY_POOL_COUNT, enable_validate_ip=True)
            ip_proxy_info: IpInfoModel = await self.ip_proxy_pool.get_proxy()
            playwright_proxy_format, httpx_proxy_format = utils.format_proxy_info(ip_proxy_info)

        async with async_playwright() as playwright:
            self._session_persist_ok = False
            self.playwright_browser = None
            try:
                # Choose launch mode based on configuration
                if config.ENABLE_CDP_MODE:
                    utils.logger.info("[XiaoHongShuCrawler] Launching browser using CDP mode")
                    self.browser_context = await self.launch_browser_with_cdp(
                        playwright,
                        playwright_proxy_format,
                        self.user_agent,
                        headless=config.CDP_HEADLESS,
                    )
                else:
                    utils.logger.info("[XiaoHongShuCrawler] Launching browser using standard mode")
                    chromium = playwright.chromium
                    self.browser_context = await self.launch_browser(
                        chromium,
                        playwright_proxy_format,
                        self.user_agent,
                        headless=config.HEADLESS,
                    )
                    await self.browser_context.add_init_script(path="libs/stealth.min.js")

                self.context_page = await self.browser_context.new_page()
                _session_json = session_path_for_platform(config.PLATFORM)
                if config.SAVE_LOGIN_STATE and _session_json.is_file():
                    utils.logger.info(
                        "[XiaoHongShuCrawler.start] 使用 Playwright storage_state %s，不叠加注入 data/xhs_browser_cookies.json",
                        _session_json,
                    )
                else:
                    await try_load_saved_xhs_cookies(self.browser_context)
                await self.context_page.goto(self.index_url)

                self.xhs_client = await self.create_xhs_client(httpx_proxy_format)
                if not await self.xhs_client.pong():
                    login_obj = XiaoHongShuLogin(
                        login_type=config.LOGIN_TYPE,
                        login_phone="",  # input your phone number
                        browser_context=self.browser_context,
                        context_page=self.context_page,
                        cookie_str=config.COOKIES,
                    )
                    await login_obj.begin()
                    await self.xhs_client.update_cookies(
                        browser_context=self.browser_context,
                        urls=self.cookie_urls,
                    )
                if not await self.xhs_client.pong():
                    # 有头 + 非 CDP：Cookie 失效时参考 TikTok_Video 思路，改为扫码登录，成功后由 finally 写入 session.json
                    if (
                        config.LOGIN_TYPE == "cookie"
                        and not config.HEADLESS
                        and not config.ENABLE_CDP_MODE
                    ):
                        utils.logger.warning(
                            "[XiaoHongShuCrawler.start] Cookie 未通过 pong，有头模式将切换为扫码登录；"
                            "请在已打开的浏览器窗口内用小红书 App 扫码，完成后将自动保存会话并继续采集。"
                        )
                        qr_login = XiaoHongShuLogin(
                            login_type="qrcode",
                            login_phone="",
                            browser_context=self.browser_context,
                            context_page=self.context_page,
                            cookie_str="",
                        )
                        await qr_login.begin()
                        await self.xhs_client.update_cookies(
                            browser_context=self.browser_context,
                            urls=self.cookie_urls,
                        )
                if not await self.xhs_client.pong():
                    msg = (
                        "小红书登录态无效或会话已过期（pong 校验失败）。"
                        "有头模式可改用 --headless false 以在 Cookie 失效时自动弹出扫码；"
                        "或更新 cookiesFile/xhs/session.json / data/xhs_cookie_string.txt 后重试。"
                    )
                    utils.logger.error("[XiaoHongShuCrawler.start] %s", msg)
                    raise RuntimeError(msg)

                self._session_persist_ok = True
                if (
                    config.SAVE_LOGIN_STATE
                    and not config.ENABLE_CDP_MODE
                    and self.browser_context is not None
                ):
                    try:
                        from tools.playwright_session import save_storage_state_atomic

                        _dest = session_path_for_platform(config.PLATFORM)
                        await save_storage_state_atomic(self.browser_context, _dest)
                        utils.logger.info(
                            "[XiaoHongShuCrawler.start] 登录态已写入 %s（任务结束时将再次保存以刷新会话）",
                            _dest,
                        )
                    except Exception as exc:
                        utils.logger.warning(
                            "[XiaoHongShuCrawler.start] 登录后立即保存 storage_state 失败: %s", exc
                        )

                crawler_type_var.set(config.CRAWLER_TYPE)
                crawl_exc: Optional[BaseException] = None
                try:
                    if config.CRAWLER_TYPE == "search":
                        await self.search()
                    elif config.CRAWLER_TYPE == "detail":
                        await self.get_specified_notes()
                    elif config.CRAWLER_TYPE == "creator":
                        await self.get_creators_and_notes()
                    else:
                        pass
                except BaseException as exc:
                    crawl_exc = exc
                    utils.logger.exception(
                        "[XiaoHongShuCrawler.start] 采集中断，将继续执行飞书 flush（已入队的成功笔记仍会尝试同步）: %s",
                        exc,
                    )

                if config.PLATFORM == "xhs":
                    try:
                        from tools.feishu import xhs_feishu_sink

                        await xhs_feishu_sink.flush()
                    except Exception as exc:
                        utils.logger.exception("[XiaoHongShuCrawler.start] 飞书 flush 失败: %s", exc)

                if crawl_exc is not None:
                    raise crawl_exc

                utils.logger.info("[XiaoHongShuCrawler.start] Xhs Crawler finished ...")
            finally:
                await finalize_standard_playwright(
                    use_cdp=config.ENABLE_CDP_MODE,
                    save_login_state=config.SAVE_LOGIN_STATE,
                    persist_ok=getattr(self, "_session_persist_ok", False),
                    browser_context=getattr(self, "browser_context", None),
                    playwright_browser=getattr(self, "playwright_browser", None),
                    platform=config.PLATFORM,
                    log=utils.logger,
                )
                if not config.ENABLE_CDP_MODE:
                    self.browser_context = None  # type: ignore[assignment]
                    self.playwright_browser = None

    async def search(self) -> None:
        """Search for notes and retrieve their comment information."""
        utils.logger.info("[XiaoHongShuCrawler.search] Begin search Xiaohongshu keywords")
        xhs_limit_count = 20  # Xiaohongshu limit page fixed value
        if config.CRAWLER_MAX_NOTES_COUNT < xhs_limit_count:
            config.CRAWLER_MAX_NOTES_COUNT = xhs_limit_count
        start_page = config.START_PAGE
        for keyword in config.KEYWORDS.split(","):
            source_keyword_var.set(keyword)
            utils.logger.info(f"[XiaoHongShuCrawler.search] Current search keyword: {keyword}")
            page = 1
            search_id = get_search_id()
            while (page - start_page + 1) * xhs_limit_count <= config.CRAWLER_MAX_NOTES_COUNT:
                if page < start_page:
                    utils.logger.info(f"[XiaoHongShuCrawler.search] Skip page {page}")
                    page += 1
                    continue

                try:
                    utils.logger.info(f"[XiaoHongShuCrawler.search] search Xiaohongshu keyword: {keyword}, page: {page}")
                    note_ids: List[str] = []
                    xsec_tokens: List[str] = []
                    notes_res = await self.xhs_client.get_note_by_keyword(
                        keyword=keyword,
                        search_id=search_id,
                        page=page,
                        sort=(SearchSortType(config.SORT_TYPE) if config.SORT_TYPE != "" else SearchSortType.GENERAL),
                    )
                    utils.logger.info(f"[XiaoHongShuCrawler.search] Search notes response: {notes_res}")
                    if not notes_res or not notes_res.get("has_more", False):
                        utils.logger.info("[XiaoHongShuCrawler.search] No more content!")
                        break
                    semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
                    task_list = [
                        self.get_note_detail_async_task(
                            note_id=post_item.get("id"),
                            xsec_source=post_item.get("xsec_source"),
                            xsec_token=post_item.get("xsec_token"),
                            semaphore=semaphore,
                        ) for post_item in notes_res.get("items", {}) if post_item.get("model_type") not in ("rec_query", "hot_query")
                    ]
                    raw_details = await asyncio.gather(*task_list, return_exceptions=True)
                    for idx, note_detail in enumerate(raw_details):
                        if isinstance(note_detail, BaseException):
                            utils.logger.error(
                                "[XiaoHongShuCrawler.search] 单条笔记详情失败 index=%s: %s", idx, note_detail
                            )
                            continue
                        if note_detail and note_detail.get("note_id"):
                            try:
                                await xhs_store.update_xhs_note(note_detail)
                                await self.get_notice_media(note_detail)
                                note_ids.append(note_detail.get("note_id"))
                                xsec_tokens.append(note_detail.get("xsec_token"))
                            except Exception as exc:
                                utils.logger.exception(
                                    "[XiaoHongShuCrawler.search] 落库/媒体失败 note_id=%s: %s",
                                    note_detail.get("note_id"),
                                    exc,
                                )
                    page += 1
                    utils.logger.info("[XiaoHongShuCrawler.search] 本页详情任务数=%s", len(raw_details))
                    await self.batch_get_note_comments(note_ids, xsec_tokens)

                    # Sleep after each page navigation
                    await asyncio.sleep(config.CRAWLER_MAX_SLEEP_SEC)
                    utils.logger.info(f"[XiaoHongShuCrawler.search] Sleeping for {config.CRAWLER_MAX_SLEEP_SEC} seconds after page {page-1}")
                except DataFetchError:
                    utils.logger.error("[XiaoHongShuCrawler.search] Get note detail error")
                    break

    async def get_creators_and_notes(self) -> None:
        """Get creator's notes and retrieve their comment information."""
        utils.logger.info("[XiaoHongShuCrawler.get_creators_and_notes] Begin get Xiaohongshu creators")
        for creator_url in config.XHS_CREATOR_ID_LIST:
            self._creator_video_notes_xsec.clear()
            creator_success = False
            try:
                # Parse creator URL to get user_id and security tokens
                creator_info: CreatorUrlInfo = parse_creator_info_from_url(creator_url)
                utils.logger.info(f"[XiaoHongShuCrawler.get_creators_and_notes] Parse creator URL info: {creator_info}")
                user_id = creator_info.user_id

                # get creator detail info from web html content
                if getattr(config, "XHS_FETCH_CREATOR_PROFILE", True):
                    createor_info: Dict = await self.xhs_client.get_creator_info(
                        user_id=user_id,
                        xsec_token=creator_info.xsec_token,
                        xsec_source=creator_info.xsec_source
                    )
                    if createor_info:
                        await xhs_store.save_creator(user_id, creator=createor_info)
                else:
                    utils.logger.info(
                        "[XiaoHongShuCrawler.get_creators_and_notes] XHS_FETCH_CREATOR_PROFILE=False，跳过创作者资料拉取"
                    )
            except ValueError as e:
                utils.logger.error(f"[XiaoHongShuCrawler.get_creators_and_notes] Failed to parse creator URL: {e}")
                self._creator_stats[creator_url] = False
                continue

            self._creator_default_xsec_source = creator_info.xsec_source or "pc_note"
            self._creator_fallback_xsec_token = creator_info.xsec_token or ""

            # Use fixed crawling interval
            crawl_interval = config.CRAWLER_MAX_SLEEP_SEC
            try:
                all_notes_list = await self.xhs_client.get_all_notes_by_creator(
                    user_id=user_id,
                    crawl_interval=crawl_interval,
                    callback=self.fetch_creator_notes_detail,
                    xsec_token=creator_info.xsec_token,
                    xsec_source=creator_info.xsec_source,
                )
                creator_success = True
            except Exception as exc:
                utils.logger.exception(
                    "[XiaoHongShuCrawler.get_creators_and_notes] 获取创作者笔记列表失败（如 461/验证码），"
                    "跳过该账号本条 URL 的列表与评论，继续下一账号或收尾 flush: %s | url=%s",
                    exc,
                    creator_url[:120],
                )
                all_notes_list = []
                creator_success = False

            # 记录创作者状态
            self._creator_stats[creator_url] = creator_success

            note_ids = []
            xsec_tokens = []
            if getattr(config, "XHS_CREATOR_ONLY_VIDEO_NOTES", False):
                note_ids = list(self._creator_video_notes_xsec.keys())
                xsec_tokens = [self._creator_video_notes_xsec[nid] for nid in note_ids]
            else:
                for note_item in all_notes_list:
                    nid = xhs_creator_list_note_id(note_item)
                    if nid:
                        note_ids.append(nid)
                        xsec_tokens.append(str(note_item.get("xsec_token") or self._creator_fallback_xsec_token or ""))
            # 创作者台账默认不拉评论；仅当 XHS_CREATOR_FETCH_COMMENTS 且 ENABLE_GET_COMMENTS 时批量拉评论
            if getattr(config, "XHS_CREATOR_FETCH_COMMENTS", False) and config.ENABLE_GET_COMMENTS:
                await self.batch_get_note_comments(note_ids, xsec_tokens)
            elif note_ids:
                utils.logger.info(
                    "[XiaoHongShuCrawler.get_creators_and_notes] 已跳过评论拉取（创作者模式默认关闭，"
                    "需评论请设 XHS_CREATOR_FETCH_COMMENTS=True 且 ENABLE_GET_COMMENTS/--get_comment true）"
                )

    def get_creator_stats(self) -> Dict[str, any]:
        """
        获取创作者采集统计

        Returns:
            包含创作者统计的字典
        """
        total = len(self._creator_stats)
        success = sum(1 for v in self._creator_stats.values() if v)
        failed = total - success
        failed_urls = [url for url, ok in self._creator_stats.items() if not ok]

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "failed_urls": failed_urls,
        }

    async def fetch_creator_notes_detail(self, note_list: List[Dict]):
        """处理创作者主页列表回调：可仅用列表字段落库，或并发拉详情后再落库。"""
        only_video = bool(getattr(config, "XHS_CREATOR_ONLY_VIDEO_NOTES", False))
        list_only = bool(getattr(config, "XHS_CREATOR_LIST_PAYLOAD_ONLY", False))
        list_skipped = 0
        work_list = note_list
        if only_video:
            work_list = []
            for post_item in note_list:
                if should_skip_xhs_note_detail_fetch(post_item):
                    list_skipped += 1
                    continue
                work_list.append(post_item)
            if list_skipped:
                utils.logger.info(
                    "[XiaoHongShuCrawler.fetch_creator_notes_detail] 列表阶段跳过非视频笔记 %s 条",
                    list_skipped,
                )

        if list_only:
            default_src = str(getattr(self, "_creator_default_xsec_source", "") or "pc_note")
            profile_tok = str(getattr(self, "_creator_fallback_xsec_token", "") or "")
            utils.logger.info(
                "[XiaoHongShuCrawler.fetch_creator_notes_detail] XHS_CREATOR_LIST_PAYLOAD_ONLY=True，"
                "仅用 user_posted 列表数据落库/飞书，本批 %s 条（不调 /feed 笔记详情）",
                len(work_list),
            )
            detail_skipped = 0
            for post_item in work_list:
                mapped = creator_list_item_to_note_item(
                    post_item,
                    default_xsec_source=default_src,
                    profile_xsec_token=profile_tok,
                )
                if not mapped:
                    continue
                if only_video and not is_xhs_video_note(mapped):
                    detail_skipped += 1
                    continue
                try:
                    await xhs_store.update_xhs_note(mapped)
                    await self.get_notice_media(mapped)
                except Exception as exc:
                    utils.logger.exception(
                        "[XiaoHongShuCrawler.fetch_creator_notes_detail] 列表模式落库/媒体失败 note_id=%s: %s",
                        mapped.get("note_id"),
                        exc,
                    )
                    continue
                if only_video:
                    nid = str(mapped.get("note_id"))
                    self._creator_video_notes_xsec[nid] = str(mapped.get("xsec_token") or "")
            if only_video and detail_skipped:
                utils.logger.info(
                    "[XiaoHongShuCrawler.fetch_creator_notes_detail] 列表模式下跳过非视频笔记 %s 条",
                    detail_skipped,
                )
            return

        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        task_list = [
            self.get_note_detail_async_task(
                note_id=xhs_creator_list_note_id(post_item),
                xsec_source=post_item.get("xsec_source"),
                xsec_token=post_item.get("xsec_token"),
                semaphore=semaphore,
            )
            for post_item in work_list
        ]

        raw_details = await asyncio.gather(*task_list, return_exceptions=True)
        detail_skipped = 0
        for idx, note_detail in enumerate(raw_details):
            if isinstance(note_detail, BaseException):
                nid = xhs_creator_list_note_id(work_list[idx]) if idx < len(work_list) else None
                utils.logger.error(
                    "[XiaoHongShuCrawler.fetch_creator_notes_detail] 单条详情失败 note_id=%s: %s",
                    nid,
                    note_detail,
                )
                continue
            if not note_detail or not note_detail.get("note_id"):
                continue
            if only_video and not is_xhs_video_note(note_detail):
                detail_skipped += 1
                continue
            try:
                await xhs_store.update_xhs_note(note_detail)
                await self.get_notice_media(note_detail)
            except Exception as exc:
                utils.logger.exception(
                    "[XiaoHongShuCrawler.fetch_creator_notes_detail] 落库/媒体失败 note_id=%s: %s",
                    note_detail.get("note_id"),
                    exc,
                )
                continue
            if only_video:
                nid = str(note_detail.get("note_id"))
                self._creator_video_notes_xsec[nid] = str(note_detail.get("xsec_token") or "")
        if only_video and detail_skipped:
            utils.logger.info(
                "[XiaoHongShuCrawler.fetch_creator_notes_detail] 详情阶段跳过非视频笔记 %s 条",
                detail_skipped,
            )

    async def get_specified_notes(self):
        """Get the information and comments of the specified post

        Note: Must specify note_id, xsec_source, xsec_token
        """
        get_note_detail_task_list = []
        for full_note_url in config.XHS_SPECIFIED_NOTE_URL_LIST:
            note_url_info: NoteUrlInfo = parse_note_info_from_note_url(full_note_url)
            utils.logger.info(f"[XiaoHongShuCrawler.get_specified_notes] Parse note url info: {note_url_info}")
            crawler_task = self.get_note_detail_async_task(
                note_id=note_url_info.note_id,
                xsec_source=note_url_info.xsec_source,
                xsec_token=note_url_info.xsec_token,
                semaphore=asyncio.Semaphore(config.MAX_CONCURRENCY_NUM),
            )
            get_note_detail_task_list.append(crawler_task)

        need_get_comment_note_ids = []
        xsec_tokens = []
        raw_details = await asyncio.gather(*get_note_detail_task_list, return_exceptions=True)
        for idx, note_detail in enumerate(raw_details):
            if isinstance(note_detail, BaseException):
                utils.logger.error(
                    "[XiaoHongShuCrawler.get_specified_notes] 单条详情失败 index=%s: %s", idx, note_detail
                )
                continue
            if note_detail and note_detail.get("note_id"):
                try:
                    need_get_comment_note_ids.append(note_detail.get("note_id", ""))
                    xsec_tokens.append(note_detail.get("xsec_token", ""))
                    await xhs_store.update_xhs_note(note_detail)
                    await self.get_notice_media(note_detail)
                except Exception as exc:
                    utils.logger.exception(
                        "[XiaoHongShuCrawler.get_specified_notes] 落库/媒体失败 note_id=%s: %s",
                        note_detail.get("note_id"),
                        exc,
                    )
        await self.batch_get_note_comments(need_get_comment_note_ids, xsec_tokens)

    async def get_note_detail_async_task(
        self,
        note_id: str,
        xsec_source: str,
        xsec_token: str,
        semaphore: asyncio.Semaphore,
    ) -> Optional[Dict]:
        """Get note detail

        Args:
            note_id:
            xsec_source:
            xsec_token:
            semaphore:

        Returns:
            Dict: note detail
        """
        note_detail = None
        utils.logger.info(f"[get_note_detail_async_task] Begin get note detail, note_id: {note_id}")
        async with semaphore:
            try:
                try:
                    note_detail = await self.xhs_client.get_note_by_id(note_id, xsec_source, xsec_token)
                except RetryError:
                    pass

                if not note_detail:
                    note_detail = await self.xhs_client.get_note_by_id_from_html(note_id, xsec_source, xsec_token,
                                                                                 enable_cookie=True)
                    if not note_detail:
                        utils.logger.error(
                            "[get_note_detail_async_task] 无法获取笔记详情（可能风控/验证码），跳过 note_id=%s",
                            note_id,
                        )
                        return None

                note_detail.update({"xsec_token": xsec_token, "xsec_source": xsec_source})

                # Sleep after fetching note detail
                await asyncio.sleep(config.CRAWLER_MAX_SLEEP_SEC)
                utils.logger.info(f"[get_note_detail_async_task] Sleeping for {config.CRAWLER_MAX_SLEEP_SEC} seconds after fetching note {note_id}")

                return note_detail

            except NoteNotFoundError as ex:
                utils.logger.warning(f"[XiaoHongShuCrawler.get_note_detail_async_task] Note not found: {note_id}, {ex}")
                return None
            except DataFetchError as ex:
                utils.logger.error(f"[XiaoHongShuCrawler.get_note_detail_async_task] Get note detail error: {ex}")
                return None
            except KeyError as ex:
                utils.logger.error(f"[XiaoHongShuCrawler.get_note_detail_async_task] have not fund note detail note_id:{note_id}, err: {ex}")
                return None
            except Exception as ex:
                utils.logger.error(
                    "[XiaoHongShuCrawler.get_note_detail_async_task] 未预期异常 note_id=%s: %s", note_id, ex
                )
                return None

    async def batch_get_note_comments(self, note_list: List[str], xsec_tokens: List[str]):
        """Batch get note comments"""
        if not config.ENABLE_GET_COMMENTS:
            utils.logger.info(f"[XiaoHongShuCrawler.batch_get_note_comments] Crawling comment mode is not enabled")
            return

        utils.logger.info(f"[XiaoHongShuCrawler.batch_get_note_comments] Begin batch get note comments, note list: {note_list}")
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        task_list: List[Task] = []
        for index, note_id in enumerate(note_list):
            task = asyncio.create_task(
                self.get_comments(note_id=note_id, xsec_token=xsec_tokens[index], semaphore=semaphore),
                name=note_id,
            )
            task_list.append(task)
        raw_c = await asyncio.gather(*task_list, return_exceptions=True)
        for note_id, res in zip(note_list, raw_c):
            if isinstance(res, BaseException):
                utils.logger.error("[XiaoHongShuCrawler.batch_get_note_comments] 评论拉取失败 note_id=%s: %s", note_id, res)

    async def get_comments(self, note_id: str, xsec_token: str, semaphore: asyncio.Semaphore):
        """Get note comments with keyword filtering and quantity limitation"""
        async with semaphore:
            utils.logger.info(f"[XiaoHongShuCrawler.get_comments] Begin get note id comments {note_id}")
            # Use fixed crawling interval
            crawl_interval = config.CRAWLER_MAX_SLEEP_SEC
            await self.xhs_client.get_note_all_comments(
                note_id=note_id,
                xsec_token=xsec_token,
                crawl_interval=crawl_interval,
                callback=xhs_store.batch_update_xhs_note_comments,
                max_count=config.CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES,
            )

            # Sleep after fetching comments
            await asyncio.sleep(crawl_interval)
            utils.logger.info(f"[XiaoHongShuCrawler.get_comments] Sleeping for {crawl_interval} seconds after fetching comments for note {note_id}")

    async def create_xhs_client(self, httpx_proxy: Optional[str]) -> XiaoHongShuClient:
        """Create Xiaohongshu client"""
        utils.logger.info("[XiaoHongShuCrawler.create_xhs_client] Begin create Xiaohongshu API client ...")
        cookie_str, cookie_dict = await utils.convert_browser_context_cookies(
            self.browser_context,
            urls=self.cookie_urls,
        )
        xhs_client_obj = XiaoHongShuClient(
            proxy=httpx_proxy,
            headers={
                "accept": "application/json, text/plain, */*",
                "accept-language": "zh-CN,zh;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/json;charset=UTF-8",
                "origin": self.index_url,
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": f"{self.index_url}/",
                "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                "Cookie": cookie_str,
            },
            playwright_page=self.context_page,
            cookie_dict=cookie_dict,
            proxy_ip_pool=self.ip_proxy_pool,  # Pass proxy pool for automatic refresh
        )
        return xhs_client_obj

    async def launch_browser(
        self,
        chromium: BrowserType,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True,
    ) -> BrowserContext:
        """Launch browser and create browser context (storage_state when SAVE_LOGIN_STATE)."""
        utils.logger.info("[XiaoHongShuCrawler.launch_browser] Begin create browser context ...")
        self.playwright_browser = None
        state_path = session_path_for_platform(config.PLATFORM) if config.SAVE_LOGIN_STATE else None
        viewport = {"width": 1920, "height": 1080}
        browser, context = await attach_chromium_browser(
            chromium,
            headless=headless,
            playwright_proxy=playwright_proxy,
            user_agent=user_agent,
            viewport=viewport,
            storage_state_path=state_path,
        )
        self.playwright_browser = browser
        return context

    async def launch_browser_with_cdp(
        self,
        playwright: Playwright,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True,
    ) -> BrowserContext:
        """Launch browser using CDP mode"""
        try:
            self.cdp_manager = CDPBrowserManager()
            browser_context = await self.cdp_manager.launch_and_connect(
                playwright=playwright,
                playwright_proxy=playwright_proxy,
                user_agent=user_agent,
                headless=headless,
            )

            # Display browser information
            browser_info = await self.cdp_manager.get_browser_info()
            utils.logger.info(f"[XiaoHongShuCrawler] CDP browser info: {browser_info}")

            return browser_context

        except Exception as e:
            utils.logger.error(f"[XiaoHongShuCrawler] CDP mode launch failed, falling back to standard mode: {e}")
            # Fall back to standard mode
            chromium = playwright.chromium
            return await self.launch_browser(chromium, playwright_proxy, user_agent, headless)

    async def close(self):
        """Close browser context"""
        if self.cdp_manager:
            await self.cdp_manager.cleanup()
            self.cdp_manager = None
        else:
            await finalize_standard_playwright(
                use_cdp=False,
                save_login_state=config.SAVE_LOGIN_STATE,
                persist_ok=getattr(self, "_session_persist_ok", False),
                browser_context=getattr(self, "browser_context", None),
                playwright_browser=getattr(self, "playwright_browser", None),
                platform=config.PLATFORM,
                log=utils.logger,
            )
            self.browser_context = None  # type: ignore[assignment]
            self.playwright_browser = None
        utils.logger.info("[XiaoHongShuCrawler.close] Browser context closed ...")

    async def get_notice_media(self, note_detail: Dict):
        if not config.ENABLE_GET_MEIDAS:
            utils.logger.info(f"[XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled")
            return
        await self.get_note_images(note_detail)
        await self.get_notice_video(note_detail)

    async def get_note_images(self, note_item: Dict):
        """Get note images. Please use get_notice_media

        Args:
            note_item: Note item dictionary
        """
        if not config.ENABLE_GET_MEIDAS:
            return
        note_id = note_item.get("note_id")
        image_list: List[Dict] = note_item.get("image_list", [])

        for img in image_list:
            if img.get("url_default") != "":
                img.update({"url": img.get("url_default")})

        if not image_list:
            return
        picNum = 0
        for pic in image_list:
            url = pic.get("url")
            if not url:
                continue
            content = await self.xhs_client.get_note_media(url)
            await asyncio.sleep(random.random())
            if content is None:
                continue
            extension_file_name = f"{picNum}.jpg"
            picNum += 1
            await xhs_store.update_xhs_note_image(note_id, content, extension_file_name)

    async def get_notice_video(self, note_item: Dict):
        """Get note videos. Please use get_notice_media

        Args:
            note_item: Note item dictionary
        """
        if not config.ENABLE_GET_MEIDAS:
            return
        note_id = note_item.get("note_id")

        videos = xhs_store.get_video_url_arr(note_item)

        if not videos:
            return
        videoNum = 0
        for url in videos:
            content = await self.xhs_client.get_note_media(url)
            await asyncio.sleep(random.random())
            if content is None:
                continue
            extension_file_name = f"{videoNum}.mp4"
            videoNum += 1
            await xhs_store.update_xhs_note_video(note_id, content, extension_file_name)
