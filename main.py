# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/futianren/KidsTaiChi-MediaCrawler/blob/main/main.py
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

import sys
import io

# Force UTF-8 encoding for stdout/stderr to prevent encoding errors
# when outputting Chinese characters in non-UTF-8 terminals
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import asyncio
from typing import Optional, Type
import json
import time
from datetime import datetime
from pathlib import Path

import cmd_arg
import config
from database import db
from base.base_crawler import AbstractCrawler
from media_platform.bilibili import BilibiliCrawler
from media_platform.douyin import DouYinCrawler
from media_platform.kuaishou import KuaishouCrawler
from media_platform.tieba import TieBaCrawler
from media_platform.weibo import WeiboCrawler
from media_platform.xhs import XiaoHongShuCrawler
from media_platform.zhihu import ZhihuCrawler
from tools.async_file_writer import AsyncFileWriter
from tools import utils
from var import crawler_type_var


class CrawlerFactory:
    CRAWLERS: dict[str, Type[AbstractCrawler]] = {
        "xhs": XiaoHongShuCrawler,
        "dy": DouYinCrawler,
        "ks": KuaishouCrawler,
        "bili": BilibiliCrawler,
        "wb": WeiboCrawler,
        "tieba": TieBaCrawler,
        "zhihu": ZhihuCrawler,
    }

    @staticmethod
    def create_crawler(platform: str) -> AbstractCrawler:
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            supported = ", ".join(sorted(CrawlerFactory.CRAWLERS))
            raise ValueError(f"Invalid media platform: {platform!r}. Supported: {supported}")
        return crawler_class()


crawler: Optional[AbstractCrawler] = None


def _flush_excel_if_needed() -> None:
    if config.SAVE_DATA_OPTION != "excel":
        return

    try:
        from store.excel_store_base import ExcelStoreBase

        ExcelStoreBase.flush_all()
        print("[Main] Excel files saved successfully")
    except Exception as e:
        print(f"[Main] Error flushing Excel data: {e}")


async def _generate_wordcloud_if_needed() -> None:
    if config.SAVE_DATA_OPTION not in ("json", "jsonl") or not config.ENABLE_GET_WORDCLOUD:
        return

    try:
        file_writer = AsyncFileWriter(
            platform=config.PLATFORM,
            crawler_type=crawler_type_var.get(),
        )
        await file_writer.generate_wordcloud_from_comments()
    except Exception as e:
        print(f"[Main] Error generating wordcloud: {e}")


async def main() -> None:
    global crawler

    args = await cmd_arg.parse_cmd()
    if args.init_db:
        await db.init_db(args.init_db)
        print(f"Database {args.init_db} initialized successfully.")
        return

    # 项目配置处理（仅在 creator 模式下）
    project_ids = []
    if config.CRAWLER_TYPE == "creator" and config.PLATFORM == "xhs":
        # 如果命令行指定了 creator_id，不使用项目配置
        if not args.creator_id:
            from tools.project_loader import (
                apply_project_config,
                get_project_name,
                get_default_project,
                validate_project_config,
            )

            # 确定要执行的项目列表
            if args.projects:  # 多项目顺序执行
                project_ids = [p.strip() for p in args.projects.split(",") if p.strip()]
            elif args.project:  # 单项目
                project_ids = [args.project]
            else:  # 使用默认项目
                project_ids = [get_default_project()]

            # 验证项目配置
            for project_id in project_ids:
                is_valid, error_msg = validate_project_config(project_id)
                if not is_valid:
                    print(f"[错误] {error_msg}")
                    return

    # 执行爬虫
    if project_ids:
        # 多项目模式
        from tools.feishu import xhs_feishu_sink
        from tools.project_loader import get_project_name

        all_summaries = []

        for idx, project_id in enumerate(project_ids, 1):
            print(f"\n{'='*60}")
            print(f"[项目 {idx}/{len(project_ids)}] 开始执行：{get_project_name(project_id)} ({project_id})")
            print(f"{'='*60}\n")

            start_time = time.time()
            error_message = None
            project_name = get_project_name(project_id)
            crawler = None

            try:
                # 加载项目配置
                apply_project_config(project_id)

                # 重置飞书写入状态（避免项目间数据混淆）
                xhs_feishu_sink.reset_for_tests()

                # 执行爬虫
                crawler = CrawlerFactory.create_crawler(platform=config.PLATFORM)
                await crawler.start()

                _flush_excel_if_needed()
                await _generate_wordcloud_if_needed()

            except Exception as e:
                error_message = str(e)
                utils.logger.exception(f"[Main] 项目 {project_id} 执行失败: {e}")

            elapsed_seconds = time.time() - start_time

            # 收集统计数据
            feishu_stats = xhs_feishu_sink.get_stats()
            creator_stats = {}
            if crawler and hasattr(crawler, 'get_creator_stats'):
                creator_stats = crawler.get_creator_stats()

            # 判断状态
            if error_message:
                status = "failed"
            elif creator_stats.get("failed", 0) > 0:
                status = "partial"
            else:
                status = "success"

            # 构建摘要
            summary = {
                "project_id": project_id,
                "project_name": project_name,
                "status": status,
                "creators": creator_stats,
                "notes": feishu_stats,
                "elapsed_seconds": round(elapsed_seconds, 1),
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

            all_summaries.append(summary)

            # 保存单个项目的摘要
            project_summary_path = Path(config.SAVE_DATA_PATH) / "ci_run_summary.json"
            project_summary_path.parent.mkdir(parents=True, exist_ok=True)
            with open(project_summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            print(f"\n{'='*60}")
            print(f"[项目 {idx}/{len(project_ids)}] 完成：{project_name}")
            print(f"{'='*60}\n")

        # 保存所有项目的汇总
        overall_summary_path = Path("data") / "ci_all_projects_summary.json"
        overall_summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(overall_summary_path, "w", encoding="utf-8") as f:
            json.dump(all_summaries, f, ensure_ascii=False, indent=2)

        print(f"\n[总结] 所有项目执行完成，共 {len(project_ids)} 个项目")
    else:
        # 单次执行模式（非项目模式或指定了 creator_id）
        crawler = CrawlerFactory.create_crawler(platform=config.PLATFORM)
        await crawler.start()

        _flush_excel_if_needed()
        await _generate_wordcloud_if_needed()


async def async_cleanup() -> None:
    global crawler
    if crawler:
        if getattr(crawler, "cdp_manager", None):
            try:
                await crawler.cdp_manager.cleanup(force=True)
            except Exception as e:
                error_msg = str(e).lower()
                if "closed" not in error_msg and "disconnected" not in error_msg:
                    print(f"[Main] Error cleaning up CDP browser: {e}")

        elif getattr(crawler, "browser_context", None):
            try:
                await crawler.browser_context.close()
            except Exception as e:
                error_msg = str(e).lower()
                if "closed" not in error_msg and "disconnected" not in error_msg:
                    print(f"[Main] Error closing browser context: {e}")

    if config.SAVE_DATA_OPTION in ("db", "sqlite"):
        await db.close()

if __name__ == "__main__":
    from tools.app_runner import run

    def _force_stop() -> None:
        c = crawler
        if not c:
            return
        cdp_manager = getattr(c, "cdp_manager", None)
        launcher = getattr(cdp_manager, "launcher", None)
        if not launcher:
            return
        try:
            launcher.cleanup()
        except Exception:
            pass

    run(main, async_cleanup, cleanup_timeout_seconds=15.0, on_first_interrupt=_force_stop)
