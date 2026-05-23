# -*- coding: utf-8 -*-
"""
逍遥太极项目配置

北京逍遥少儿太极独立台账；与少儿太极项目中的同一账号并行维护（双写不同飞书表）。
"""

# 项目基本信息
PROJECT_NAME = "逍遥太极"
PROJECT_DESCRIPTION = "北京逍遥少儿太极 — 分平台发布状态台账"

# 创作者列表（从浏览器地址栏复制，包含 xsec_token）
CREATORS = [
    # 北京逍遥少儿太极
    "https://www.xiaohongshu.com/user/profile/62233d5b00000000100068cf?xsec_token=ABPQSNsmEnlKz8licn9DhcczeO1Xt_UojaAX0eojBSL3s=&xsec_source=pc_note",
]

# 飞书表格配置
# 表格链接：https://ccnxtccvgg22.feishu.cn/base/VvrYbHM2YaUJousmxeZcGgnZn9c?table=tblXLmvUy2RidkhC&view=vewSv84TV8
FEISHU = {
    "app_token": "VvrYbHM2YaUJousmxeZcGgnZn9c",
    "table_id": "tblXLmvUy2RidkhC",
    "view_id": "vewSv84TV8",

    "fields": {
        "note_id": "笔记ID",
        "title": "笔记标题",
        "link": "笔记链接",
    },

    # 新建行时，各分发平台默认「否」（列名与多维表一致）
    "publish_fields_on_create": {
        "快手是否发布": "否",
        "视频号是否发布": "否",
        "百家号是否发布": "否",
        "抖音是否发布": "否",
    },

    "link_field_format": "plain",
}

# 采集规则（与 modern_taichi 一致）
RULES = {
    "creator_only_video_notes": True,
    "creator_fetch_comments": False,
}
