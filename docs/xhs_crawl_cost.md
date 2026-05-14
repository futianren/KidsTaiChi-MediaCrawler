# 小红书采集：成本与可选项说明

## 飞书同步最小必要数据

写入飞书多维表依赖：

- **笔记ID**、**笔记标题**、**笔记链接**（及表内「是否发布」常量）
- 判重：**笔记ID**

以上均来自**单条笔记详情**接口（与是否落盘精简无关）。

---

## 高开销步骤（省请求 / 省下载）

| 业务含义 | 配置项 | CLI |
|---------|--------|-----|
| 一级评论 | `ENABLE_GET_COMMENTS` | `--get_comment` |
| 二级评论 | `ENABLE_GET_SUB_COMMENTS` | `--get_sub_comment` |
| 每条笔记评论条数上限 | `CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES` | `--max_comments_count_singlenotes` |
| 下载笔记图片/视频到本地 | `ENABLE_GET_MEIDAS` | `--get_medias` |
| 创作者主页资料（粉丝/简介等） | `XHS_FETCH_CREATOR_PROFILE` | 无（见 `config/xhs_config.py`） |
| 创作者模式仅视频笔记 | `XHS_CREATOR_ONLY_VIDEO_NOTES` | 无 |
| 飞书同步 | `FEISHU_SYNC_ENABLED` 等 | 见 `docs/feishu_sync.md` |

关闭评论、关闭媒体下载、关闭创作者资料，可明显降低请求量与磁盘占用。

---

## 落盘精简（不减少详情 HTTP）

| 配置项 | 取值 | 说明 |
|--------|------|------|
| `XHS_NOTE_PERSIST_MODE` | `full`（默认） | 与历史一致，写入完整 `local_db_item` |
| | `feishu_plus` | 在 `SAVE_DATA_OPTION` 为 `json` / `jsonl` / `csv` 时，仅写入 **`note_id/title/note_url/type`**；**数据库类**存储仍为完整字段 |

---

## 一键预设（仅小红书）

| 配置 / CLI | 取值 | 行为 |
|------------|------|------|
| `XHS_CRAWL_PRESET`（`config/xhs_config.py`） | `none`（默认） | 不额外改其他开关 |
| | `feishu_minimal` | 在解析 CLI 前作为**基线**：关评论、关子评论、关媒体下载、关创作者资料、`XHS_NOTE_PERSIST_MODE=feishu_plus` |
| `--xhs_crawl_preset` | `none` \| `feishu_minimal` | 与上类似；**空字符串**表示沿用配置文件中的 `XHS_CRAWL_PRESET` |

**覆盖顺序**：先应用预设基线，再应用 `--get_comment`、`--get_medias` 等单项。例如预设关评论后仍可用 `--get_comment true` 打开评论。

**注意**：预设仅在 `platform=xhs` 时生效。

---

## 业务字段清单

当前你已确认：除 **`note_id/title/note_url/type`** 外，其余字段都先不采集（可通过 `XHS_NOTE_PERSIST_MODE=full` 随时恢复完整落盘能力）。
