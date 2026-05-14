# -*- coding: utf-8 -*-
"""
现代太极项目配置
"""

# 项目基本信息
PROJECT_NAME = "现代太极"
PROJECT_DESCRIPTION = "现代太极拳相关内容采集"

# 创作者列表（从浏览器地址栏复制，包含 xsec_token）
CREATORS = [
    # 小宇咂（楚瑷旭）
    "https://www.xiaohongshu.com/user/profile/5add33f44eacab3a6907a0a7?xsec_token=AB0jB9-OHp9-pPMi1NcBkhkySPU3OBB0N64kAJBQCNX20=&xsec_source=pc_note",
    # 紫黑是梓禧
    "https://www.xiaohongshu.com/user/profile/59f056b34eacab5f8070eac9?xsec_token=ABF7dbYrldHv2oEfs_sAkXp2GhhN6BXXEk9oGFbWojRWU=&xsec_source=pc_note",
    # 🏅张宁语zy✨
    "https://www.xiaohongshu.com/user/profile/59e09cfdde5fb45a28c3fcc1?xsec_token=ABC7Y56Rgd3VGptRzyUBuPA3iE7-Az70uVbm5dsJc0uss=&xsec_source=pc_note",
    # 马小瑞
    "https://www.xiaohongshu.com/user/profile/5f465b160000000001008d90?xsec_token=ABg-Kd1qSbw6KZG0iyKyLE-1kXJhP1y7PL_0T0GEnD7Ww=&xsec_source=pc_note",
    # 阿泽
    "https://www.xiaohongshu.com/user/profile/60a3c53d0000000001009463?xsec_token=ABBUdYtaxVD7fGL4U-NfgVx3s15EvEyWG3-yM5_rAyhgQ=&xsec_source=pc_note",
    # 太极王冰
    "https://www.xiaohongshu.com/user/profile/67a457ad000000000e0105c8?xsec_token=ABhQUAjSBpXWlkfw5YHNUX9GUzHbNr8gXxsg87nKaL3Gc=&xsec_source=pc_note",
    # 第7个账号
    "https://www.xiaohongshu.com/user/profile/691fabba000000003700b13b?xsec_token=ABeolh5QVr42LLCX6iECHWX4QWkLG1q4b3Q6zYIhs9f2A=&xsec_source=pc_note",
    # 若兰
    "https://www.xiaohongshu.com/user/profile/5dd00a610000000001003e05?xsec_token=AB52Tk94ePYKXdzAx2t7gNYWAbzSzP2AHMJh05JE-u-PI=&xsec_source=pc_note",
    # 九月太极
    "https://www.xiaohongshu.com/user/profile/68a529e0000000001901044c?xsec_token=ABHGM-knZOeDKj8mGrsBn9zUO9zB6ZcDbywjSl1nCcEwI=&xsec_source=pc_search",
    # 请叫我小张
    "https://www.xiaohongshu.com/user/profile/5f28d13e0000000001002176?xsec_token=ABg2a-Z_hPpB0ercaWbLcTt8d7POJmFRTSAYaZskoXGSk=&xsec_source=pc_note",
]

# 飞书表格配置
# 表格链接：https://ccnxtccvgg22.feishu.cn/base/CVp9bX541aOGrcsAAfecp1NDnhc?table=tblaS713yNB70l9m&view=vewSv84TV8
FEISHU = {
    # 表格标识
    "app_token": "CVp9bX541aOGrcsAAfecp1NDnhc",
    "table_id": "tblaS713yNB70l9m",
    "view_id": "vewSv84TV8",

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
    # 仅采集视频笔记（与少儿太极一致）
    "creator_only_video_notes": True,
    # 不采集评论（与少儿太极一致）
    "creator_fetch_comments": False,
}
