# 小红书采集项目总览

本文档记录当前启用的小红书多项目采集方案（截至 2026-05）。

## 项目一览

| 项目 ID | 显示名 | 账号数 | 飞书表 | 发布状态列 |
|---------|--------|--------|--------|------------|
| `kids_taichi` | 少儿太极 | 13 | [少儿太极表](https://ccnxtccvgg22.feishu.cn/base/QZ4xb28cKa7UJqsKBD1c9FKXnsc?table=tblj5w5GWd4jZG9c) | 单列 `是否发布` |
| `modern_taichi` | 现代太极 | 10 | [现代太极表](https://ccnxtccvgg22.feishu.cn/base/CVp9bX541aOGrcsAAfecp1NDnhc?table=tblaS713yNB70l9m) | 单列 `是否发布` |
| `xiaoyao_taichi` | 逍遥太极 | 1 | [逍遥太极表](https://ccnxtccvgg22.feishu.cn/base/VvrYbHM2YaUJousmxeZcGgnZn9c?table=tblXLmvUy2RidkhC) | 分平台四列（见下） |
| `beida_qingniao` | 北大青鸟培训 | 5 | [北大青鸟培训表](https://ccnxtccvgg22.feishu.cn/base/W3WPbvjOLaF0zssAn87cfiignsm?table=tblQ5Rf1d3mR0nje) | 单列 `是否发布` |

**合计**：29 个创作者 URL（含 1 个与少儿太极重复的账号）。

## 逍遥太极（xiaoyao_taichi）

- **目标账号**：[北京逍遥少儿太极](https://www.xiaohongshu.com/user/profile/62233d5b00000000100068cf)
- **与少儿太极关系**：同一 `user_id` 保留在 `kids_taichi` 与 `xiaoyao_taichi` 中（方案 B）。每日 CI 会抓取两次，分别写入两张飞书表。
- **飞书新建行默认**：
  - `快手是否发布` = 否
  - `视频号是否发布` = 否
  - `百家号是否发布` = 否
  - `抖音是否发布` = 否

配置见 `projects/xiaoyao_taichi/project_config.py`。

## 统一采集规则

所有项目通过 GitHub Actions 或本地命令时，默认行为一致：

| 项 | 值 |
|----|-----|
| 平台 | 小红书 `xhs` |
| 模式 | `creator`（创作者主页） |
| 登录 | cookie（Playwright `session.json`） |
| 预设 | `feishu_minimal` |
| 仅视频 | 是 |
| 评论 | 否 |
| 主页翻页 | 最多 1 页 |
| 落盘 | JSONL（`projects/{id}/data/xhs/`） |
| 飞书同步 | 按 `笔记ID` 判重后 batch_create |

## GitHub Actions

| 工作流 | 文件 | 说明 |
|--------|------|------|
| 每日采集 + 飞书 | `.github/workflows/xhs-daily-kids-modern-feishu.yml` | 北京时间 02:00；顺序执行 `AVAILABLE_PROJECTS` 全部项目 |
| 单账号手动 | `.github/workflows/xhs-profile-crawl.yml` | 手动输入创作者 URL |
| 文档部署 | `.github/workflows/deploy.yml` | VitePress → GitHub Pages |

每日任务命令等价于：

```bash
python main.py --platform xhs --type creator --lt cookie \
  --projects "$(python -c "from config.projects_config import AVAILABLE_PROJECTS; print(','.join(AVAILABLE_PROJECTS))")" \
  --xhs_crawl_preset feishu_minimal --headless true \
  --get_comment false --save_data_option jsonl
```

所需 Secrets：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_WEBHOOK`、`XHS_PLAYWRIGHT_STORAGE_STATE`（与此前相同；逍遥表需同一飞书应用具备写入权限）。

## 飞书字段映射模式

1. **单列发布**（少儿 / 现代）：`fields.publish` → `是否发布`，新建为 `否`。
2. **多列发布**（逍遥）：`publish_fields_on_create` 字典，一次写入多个平台列。

实现：`tools/feishu/lark_bitable_client.py` 的 `batch_create_xhs_notes`。

## 本地单项目

```bash
bash projects/kids_taichi/scripts/run.sh
bash projects/modern_taichi/scripts/run.sh
bash projects/xiaoyao_taichi/scripts/run.sh
bash projects/beida_qingniao/scripts/run.sh
```

## 相关文档

- [项目管理指南](./projects_guide.md)
- [GitHub Actions 飞书通知](./github_action_feishu_notification.md)
- [GitHub Actions 配置指南](./github_actions_setup_guide.md)
