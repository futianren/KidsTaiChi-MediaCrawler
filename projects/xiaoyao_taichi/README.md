# 逍遥太极项目

## 项目目标

单独维护 **北京逍遥少儿太极** 的小红书内容台账，并跟踪笔记在各分发平台的发布状态。

> 说明：该账号同时出现在「少儿太极」项目的创作者列表中（方案 B：双写）。每日 CI 会对同一账号抓取两次，分别写入少儿太极表与本表。

## 采集账号（1 个）

1. **北京逍遥少儿太极**（62233d5b00000000100068cf）

## 飞书表格

- **表格名称**：逍遥太极内容库
- **App Token**：VvrYbHM2YaUJousmxeZcGgnZn9c
- **Table ID**：tblXLmvUy2RidkhC
- **View ID**：vewSv84TV8
- **表格链接**：https://ccnxtccvgg22.feishu.cn/base/VvrYbHM2YaUJousmxeZcGgnZn9c?table=tblXLmvUy2RidkhC&view=vewSv84TV8

### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 笔记ID | 文本 | 小红书笔记唯一标识 |
| 笔记标题 | 文本 | 笔记标题 |
| 笔记链接 | 文本 | 笔记链接（plain） |
| 快手是否发布 | 单选 | 新建默认：否 |
| 视频号是否发布 | 单选 | 新建默认：否 |
| 百家号是否发布 | 单选 | 新建默认：否 |
| 抖音是否发布 | 单选 | 新建默认：否 |

## 采集规则

- **仅采集视频笔记**
- **不采集评论**
- **每个账号主页最多 1 页**（全局默认）
- **使用 feishu_minimal 预设**

## 快速启动

```bash
bash projects/xiaoyao_taichi/scripts/run.sh
```

或：

```bash
python main.py --platform xhs --type creator --project xiaoyao_taichi \
  --xhs_crawl_preset feishu_minimal --headless true
```

## 数据路径

- **本地数据**：`projects/xiaoyao_taichi/data/xhs/`
- **配置文件**：`projects/xiaoyao_taichi/project_config.py`
