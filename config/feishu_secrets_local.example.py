# -*- coding: utf-8 -*-
"""
飞书多维表凭证（本机配置，勿提交仓库）。

用法：
1. 复制本文件为同目录下的 `feishu_secrets_local.py`
2. 填入 app_id / app_secret / app_token / table_id 等

`feishu_secrets_local.py` 已在 .gitignore 中忽略。
"""

# 与参考项目 TikTok_Crawler/config/config.yaml 中 lark.app_id / lark.app_secret 一致
FEISHU_APP_ID = ""
FEISHU_APP_SECRET = ""

# 目标多维表：从飞书 URL 中 base/ 与 table= 后取值
# 例：https://xxx.feishu.cn/base/<app_token>?table=<table_id>
FEISHU_APP_TOKEN = ""
FEISHU_TABLE_ID = ""

# 可选；判重若走全表 search 可不依赖 view
FEISHU_VIEW_ID = ""

# 飞书写入代码接入后，改为 True 才会同步
FEISHU_SYNC_ENABLED = False
