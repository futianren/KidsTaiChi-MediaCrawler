# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/futianren/KidsTaiChi-MediaCrawler/blob/main/config/xhs_config.py
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


# Xiaohongshu platform configuration

# Sorting method, the specific enumeration value is in media_platform/xhs/field.py
SORT_TYPE = "popularity_descending"

# Specify the note URL list, which must carry the xsec_token parameter
XHS_SPECIFIED_NOTE_URL_LIST = [
    "https://www.xiaohongshu.com/explore/64b95d01000000000c034587?xsec_token=AB0EFqJvINCkj6xOCKCQgfNNh8GdnBC_6XecG4QOddo3Q=&xsec_source=pc_cfeed"
    # ........................
]

# Specify the creator URL list, which needs to carry xsec_token and xsec_source parameters.
# 注意：创作者列表已迁移到 config/projects_config.py 中的项目配置。
# 如果使用 --project 参数，会自动加载项目配置中的创作者列表。
# 如果使用 --creator_id 参数，会覆盖项目配置，使用命令行指定的创作者列表。

# 默认创作者列表（仅在不使用项目配置时生效）
XHS_CREATOR_ID_LIST = [
    # 示例：
    # "https://www.xiaohongshu.com/user/profile/{user_id}?xsec_token={token}&xsec_source=pc_note",
]

# 已迁移到 config/projects_config.py 的创作者列表（kids_taichi 项目）：
# - 青少儿太极阿杜（656df977000000001901004a）
# - 北京逍遥少儿太极（62233d5b00000000100068cf）
# - 武术小娃（642fede9000000000f0125cb）
# - 太极静心（5df2e6c2000000000100717a）
# - 偲屹siri（62f07fd6000000001f0147a4）
# - 蕊宝学太极（5de32d6d0000000001002d4b）
# - 太极严光皓（67b93ad2000000000e01375d）
# - 太极萱萱（599a866c6a6a691b72914f22）
# - 一力一家太极（64509ed70000000012036b0c）
# - 仁武堂武术（67f369860000000007003332）
# - 崇武堂武术训练基地（68492002000000001b018d7d）
# - 博武堂卢教练（691d6d310000000037002e66）
# - 杭州教武术王教练（5b26542c11be10280d65ff6c）

# 创作者主页列表最多拉取页数：1=仅第一页（约 30 条）后不再翻页；0=不限制，直至 has_more 为假或达到 CRAWLER_MAX_NOTES_COUNT
XHS_CREATOR_MAX_LIST_PAGES = 1

# 仅影响「创作者模式」下从主页拉笔记列表后的处理；搜索 / 指定笔记(detail) 模式仍始终走笔记详情接口，未删除详情能力。
# True：创作者主页 user_posted 列表字段直接落库/飞书，跳过 /feed 与 HTML 详情（省请求、适合台账只要标题链接）。
# False：创作者模式下列表每条仍并发拉详情（get_note_detail_async_task，字段全）。
XHS_CREATOR_LIST_PAYLOAD_ONLY = True

# 创作者模式下仅处理视频笔记：True（默认）时跳过列表里已标明非 video 的图文等；要首页「含图文」请改为 False。
XHS_CREATOR_ONLY_VIDEO_NOTES = True

# 创作者模式是否在列表/详情处理完后仍批量拉一级评论；False=不请求评论接口（与搜索/详情模式的 ENABLE_GET_COMMENTS 独立）
XHS_CREATOR_FETCH_COMMENTS = False

# 是否拉取创作者主页资料（粉丝/简介/HTML）；False 可省一次主页请求，仅依赖 URL 中的 user_id 拉笔记列表
XHS_FETCH_CREATOR_PROFILE = True

# 笔记落盘字段：full=与历史一致；feishu_plus=仅保留飞书链路 + 常用辅助字段（详情模式下仍走同一详情 HTTP；仅列表模式时无详情 HTTP）
XHS_NOTE_PERSIST_MODE = "full"  # full | feishu_plus

# 采集预设：none=不处理；feishu_minimal=在 CLI 解析前作为基线（随后仍可由 --get_comment 等单项覆盖）
XHS_CRAWL_PRESET = "none"  # none | feishu_minimal
