# -*- coding: utf-8 -*-
"""
北大青鸟培训项目配置
"""

# 项目基本信息
PROJECT_NAME = "北大青鸟培训"
PROJECT_DESCRIPTION = "北大青鸟及相关职业教育机构小红书内容采集"

# 创作者列表（从浏览器地址栏复制，包含 xsec_token）
CREATORS = [
    # 北大青鸟职业教育网
    "https://www.xiaohongshu.com/user/profile/667e622b000000000d02432f?xsec_token=YB6n65w_Z95TGfejsy95SSxfrPGGiODA9XYVBwgB3xKXw=&xsec_source=app_share",
    # 北大青鸟职业教育咨询
    "https://www.xiaohongshu.com/user/profile/5db16b6800000000010021e9?xsec_token=YBN2eRLCTVNVmFWkInr_58qONrBDTyTSLjGEJpUyjesoY=&xsec_source=app_share",
    # 北京青鸟华腾职业培训中心
    "https://www.xiaohongshu.com/user/profile/66a9f818000000000b03113f?xsec_token=YBykZzm153EYNLwaDKolUDQ1Xa5cI8tOTL04oRfJ4akZU=&xsec_source=app_share",
    # 北大青鸟
    "https://www.xiaohongshu.com/user/profile/666a42c8000000000303181d?xsec_token=YBeXcasuau1aVpdk9aW9hg5TU-UyApyLS59wODBq_KqUo=&xsec_source=app_share",
    # 金来盛青鸟职业教育
    "https://www.xiaohongshu.com/user/profile/64803cd10000000012036171?xsec_token=YBybegxmH-U1F5elQy-3L4ugdwwEaj68ABR7Ogrsdgdf0=&xsec_source=app_share",
]

# 飞书表格配置
# 表格链接：https://ccnxtccvgg22.feishu.cn/base/W3WPbvjOLaF0zssAn87cfiignsm?table=tblQ5Rf1d3mR0nje&view=vewl0XfIvD
FEISHU = {
    "app_token": "W3WPbvjOLaF0zssAn87cfiignsm",
    "table_id": "tblQ5Rf1d3mR0nje",
    "view_id": "vewl0XfIvD",

    "fields": {
        "note_id": "笔记ID",
        "title": "笔记标题",
        "link": "笔记链接",
        "publish": "是否发布",
    },

    # 新建行默认值（与表中「待发布记录」视图字段一致）
    "publish_fields_on_create": {
        "是否发布": "否",
        "笔记平台": "小红书",
    },

    "link_field_format": "plain",
}

# 采集规则（图文 + 视频均采集；不拉评论）
RULES = {
    "creator_only_video_notes": False,
    "creator_fetch_comments": False,
}
