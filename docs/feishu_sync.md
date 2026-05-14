# 飞书多维表同步（小红书）

## 配置位置

- 已提交示例：`config/feishu_secrets_local.example.py`（复制为 `config/feishu_secrets_local.py` 并填写）
- 本机凭证（不提交）：`config/feishu_secrets_local.py`（已在 `.gitignore` 中忽略）
- 统一加载：`config/feishu_config.py`（由 `config/base_config.py` 引入，可通过 `import config` 读取）
- 环境变量备选：见仓库根目录 `.env.example` 中以 `FEISHU_` 开头的项

## 开关与模式

- `FEISHU_SYNC_ENABLED`：总开关。
- `FEISHU_SYNC_CRAWLER_TYPES`：逗号分隔，默认 `creator`；若需搜索/指定笔记也写飞书，可设为 `creator,search,detail`。

## 与 TikTok 参考项目的关系

- `FEISHU_APP_ID` / `FEISHU_APP_SECRET` 与 `Jesus_Cartoon/TikTok_Crawler` 中 `config.yaml` 的 `lark.app_id` / `lark.app_secret` 对齐。
- `FEISHU_APP_TOKEN` / `FEISHU_TABLE_ID` 使用你提供的小红书多维表 URL 中的 `base/` 与 `table=` 参数，与 TikTok 项目中的表不同。

## 实现说明

- 创作者模式下若开启 `XHS_CREATOR_ONLY_VIDEO_NOTES`（默认 `True`），仅 **视频笔记** 会落库、拉评论、写飞书；列表已标为图文的不会请求详情。
- 抓取每条笔记落盘后，`store/xhs/__init__.py` 会 `enqueue`；`media_platform/xhs/core.py` 在任务结束前 `flush`，对飞书做 **笔记ID** 判重后 `batch_create`。
- 代码：`tools/feishu/lark_bitable_client.py`、`tools/feishu/xhs_feishu_sink.py`、`tools/feishu/xhs_note_url.py`。
- 采集成本与开关总表：见 [xhs_crawl_cost.md](xhs_crawl_cost.md)。
