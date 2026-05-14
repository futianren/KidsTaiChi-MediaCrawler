# -*- coding: utf-8 -*-
"""
少儿太极项目配置
"""

# 项目基本信息
PROJECT_NAME = "少儿太极"
PROJECT_DESCRIPTION = "青少儿太极拳相关内容采集"

# 创作者列表（从浏览器地址栏复制，包含 xsec_token）
CREATORS = [
    # 青少儿太极阿杜
    "https://www.xiaohongshu.com/user/profile/656df977000000001901004a?xsec_token=AB27hwMFp0xMjNK5xdYOSvhwsH7DmDkBzvg1jTsbY5jOs=&xsec_source=pc_note",
    # 北京逍遥少儿太极
    "https://www.xiaohongshu.com/user/profile/62233d5b00000000100068cf?xsec_token=ABPQSNsmEnlKz8licn9Dhcc9_SWzJ2u0kbRTcuhpzbksA=&xsec_source=pc_note",
    # 武术小娃
    "https://www.xiaohongshu.com/user/profile/642fede9000000000f0125cb?xsec_token=ABd5RSPKeXt4t4BSNLuJ46uYdC5ipOk-FJFFcm_vOavH0=&xsec_source=pc_note",
    # 太极静心
    "https://www.xiaohongshu.com/user/profile/5df2e6c2000000000100717a?xsec_token=ABjzwx_03hfEecYI7jJYWFeN8oS-_ij5_-mb5QceHUXY0=&xsec_source=pc_search",
    # 偲屹siri
    "https://www.xiaohongshu.com/user/profile/62f07fd6000000001f0147a4?xsec_token=ABqE4iMOCesVNMS_BOXElT_QROqQOIBCUTbRK81QN6QYg=&xsec_source=pc_note",
    # 蕊宝学太极
    "https://www.xiaohongshu.com/user/profile/5de32d6d0000000001002d4b?xsec_token=ABuC3IzKSv4JjKPqtmrDthrARkpJs-dJ_wGHOM356ZlA0=&xsec_source=pc_note",
    # 太极严光皓
    "https://www.xiaohongshu.com/user/profile/67b93ad2000000000e01375d?xsec_token=ABVI_FwtKmiuhP5SEu9JCox7BLUqLo8V5NwDzlb6QSY5o=&xsec_source=pc_search",
    # 太极萱萱
    "https://www.xiaohongshu.com/user/profile/599a866c6a6a691b72914f22?xsec_token=ABeYw5l90ildQ_vRS6MNpIW9xsWPRXGJKEtf95IKmMaNQ=&xsec_source=pc_search",
    # 一力一家太极
    "https://www.xiaohongshu.com/user/profile/64509ed70000000012036b0c?xsec_token=ABSVUxr9PbFpVBRslJ6Zo-_-WJcUgplLRAVv80tRzlHd8=&xsec_source=pc_search",
    # 仁武堂武术
    "https://www.xiaohongshu.com/user/profile/67f369860000000007003332?xsec_token=ABZMBLlyL9s6FrkHqImsmAKo56sqcRX7zFnKn3E34fw90=&xsec_source=pc_search",
    # 崇武堂武术训练基地
    "https://www.xiaohongshu.com/user/profile/68492002000000001b018d7d?xsec_token=ABFpMCoPwm85Vuls4c8q6ZOU8rVd3v_lCN69OTktwaK7o=&xsec_source=pc_search",
    # 博武堂卢教练
    "https://www.xiaohongshu.com/user/profile/691d6d310000000037002e66?xsec_token=ABU_V1YViuBgSkskcFfeeFDIdvfJWFDz-0HYCZLQaApZk=&xsec_source=pc_search",
    # 杭州教武术王教练
    "https://www.xiaohongshu.com/user/profile/5b26542c11be10280d65ff6c?xsec_token=AB5wkUoS7bPVKp3eRIAjOMtODzjl6b1gqYtqNk_IJtHkA=&xsec_source=pc_search",
]

# 飞书表格配置
# 表格链接：https://ccnxtccvgg22.feishu.cn/base/QZ4xb28cKa7UJqsKBD1c9FKXnsc?table=tblj5w5GWd4jZG9c&view=vewl0XfIvD
FEISHU = {
    # 表格标识
    "app_token": "QZ4xb28cKa7UJqsKBD1c9FKXnsc",
    "table_id": "tblj5w5GWd4jZG9c",
    "view_id": "vewl0XfIvD",

    # 字段映射（根据飞书表格的实际列名配置）
    "fields": {
        "note_id": "笔记ID",
        "title": "笔记标题",
        "link": "笔记链接",
        "publish": "是否发布",
    },

    # 创建记录时"是否发布"字段的默认值
    "publish_value_on_create": "否",

    # 链接字段格式：object（飞书 URL 对象）| plain（纯文本）
    "link_field_format": "plain",
}

# 采集规则覆盖（可选，不填则使用全局默认值）
# 如果需要覆盖 config/xhs_config.py 中的全局规则，在这里添加
RULES = {
    # 示例：
    # "only_video_notes": True,        # 仅采集视频笔记
    # "fetch_comments": False,         # 不采集评论
    # "max_list_pages": 1,             # 每个账号主页最多 1 页
    # "fetch_creator_profile": True,   # 拉取创作者资料
    # "list_payload_only": True,       # 仅使用列表数据
}
