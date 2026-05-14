# 项目管理指南

本文档说明如何使用多项目管理功能。

## 项目结构

```
Media_Crawler/
├── config/
│   └── projects_config.py          # 项目索引（列出所有项目 ID）
├── projects/                        # 项目工作区
│   ├── kids_taichi/                 # 少儿太极项目
│   │   ├── project_config.py        # 项目配置
│   │   ├── README.md                # 项目说明
│   │   ├── data/xhs/                # 采集数据
│   │   └── scripts/run.sh           # 启动脚本
│   └── modern_taichi/               # 现代太极项目
│       ├── project_config.py        # 项目配置
│       ├── README.md
│       ├── data/xhs/
│       └── scripts/run.sh
└── tools/
    └── project_loader.py            # 项目配置加载器
```

## 使用方式

### 1. 单项目采集

**使用启动脚本（推荐）**：
```bash
bash projects/kids_taichi/scripts/run.sh
```

**手动指定参数**：
```bash
python main.py --platform xhs --type creator --project kids_taichi
```

### 2. 多项目顺序采集

```bash
python main.py --platform xhs --type creator --projects kids_taichi,modern_taichi
```

执行顺序：
1. 加载 kids_taichi 配置 → 采集 → 写入飞书
2. 加载 modern_taichi 配置 → 采集 → 写入飞书

### 3. 定时任务

**每天凌晨 2 点采集所有项目**：
```bash
# crontab -e
0 2 * * * cd /path/to/Media_Crawler && python main.py --platform xhs --type creator --projects kids_taichi,modern_taichi >> logs/cron.log 2>&1
```

## 新增项目

### 步骤 1：创建项目目录

```bash
mkdir -p projects/new_project/data/xhs
mkdir -p projects/new_project/scripts
```

### 步骤 2：创建项目配置文件

创建 `projects/new_project/project_config.py`：

```python
# -*- coding: utf-8 -*-
"""
新项目配置
"""

# 项目基本信息
PROJECT_NAME = "新项目名称"
PROJECT_DESCRIPTION = "项目描述"

# 创作者列表
CREATORS = [
    # 从小红书网页版复制创作者主页 URL（包含 xsec_token）
    "https://www.xiaohongshu.com/user/profile/{user_id}?xsec_token={token}&xsec_source=pc_note",
]

# 飞书表格配置
FEISHU = {
    "app_token": "飞书表格的 app_token",
    "table_id": "飞书表格的 table_id",
    "view_id": "",  # 可选
    
    "fields": {
        "note_id": "笔记ID",      # 根据实际表格列名调整
        "title": "笔记标题",
        "link": "笔记链接",
        "publish": "是否发布",
    },
    
    "publish_value_on_create": "否",
    "link_field_format": "object",
}

# 采集规则覆盖（可选）
RULES = {
    # 如果需要覆盖全局规则，在这里添加
}
```

### 步骤 3：注册项目到索引

编辑 `config/projects_config.py`，添加项目 ID：

```python
AVAILABLE_PROJECTS = [
    "kids_taichi",
    "modern_taichi",
    "new_project",  # 新增
]
```

创建 `projects/new_project/README.md`，参考现有项目的 README 格式。

### 步骤 4：创建启动脚本

创建 `projects/new_project/scripts/run.sh`：

```bash
#!/bin/bash
cd "$(dirname "$0")/../../.."

echo "=========================================="
echo "新项目 - 小红书内容采集"
echo "=========================================="

python main.py \
  --platform xhs \
  --type creator \
  --project new_project \
  --xhs_crawl_preset feishu_minimal \
  --headless true

echo "=========================================="
echo "新项目采集完成"
echo "=========================================="
```

### 步骤 6：测试

```bash
bash projects/new_project/scripts/run.sh
```

## 获取创作者 URL

1. 打开小红书网页版：https://www.xiaohongshu.com
2. 登录账号
3. 搜索并进入创作者主页
4. 从浏览器地址栏复制完整 URL（必须包含 `xsec_token` 和 `xsec_source` 参数）
5. 添加到项目配置的 `creators` 列表

**注意**：`xsec_token` 会过期，如果采集失败，需要重新复制 URL。

## 获取飞书表格信息

1. 打开飞书多维表
2. 从浏览器地址栏复制 URL，格式如下：
   ```
   https://{domain}.feishu.cn/base/{app_token}?table={table_id}&view={view_id}
   ```
3. 提取参数：
   - `app_token`：`base/` 后面的字符串
   - `table_id`：`table=` 后面的字符串
   - `view_id`：`view=` 后面的字符串（可选）

## 项目配置说明

### 配置文件位置
每个项目的配置文件位于：`projects/{project_id}/project_config.py`

### 基本信息
- `PROJECT_NAME`：项目显示名称
- `PROJECT_DESCRIPTION`：项目描述

### 创作者列表
- `CREATORS`：创作者主页 URL 列表（必须包含 `xsec_token`）

### 飞书配置
- `FEISHU`：飞书表格配置字典
  - `app_token`：飞书多维表的 App Token
  - `table_id`：表格 ID
  - `view_id`：视图 ID（可选）
  - `fields`：字段映射（根据实际表格列名配置）
  - `publish_value_on_create`：创建记录时"是否发布"字段的默认值
  - `link_field_format`：链接字段格式（`object` 或 `plain`）

### 规则覆盖
- `RULES`：规则覆盖字典（可选）
  - `only_video_notes`：是否仅采集视频笔记（默认 `True`）
  - `fetch_comments`：是否采集评论（默认 `False`）
  - `max_list_pages`：每个账号主页最多拉取页数（默认 `1`）
  - `fetch_creator_profile`：是否拉取创作者资料（默认 `True`）
  - `list_payload_only`：是否仅使用列表数据（默认 `True`）

## 数据隔离

每个项目的数据完全隔离：
- **本地数据**：`projects/{project_id}/data/xhs/`
- **飞书表格**：每个项目使用独立的表格

## 常见问题

### Q: 如何查看可用的项目列表？
A: 查看 `config/projects_config.py` 中的 `AVAILABLE_PROJECTS` 列表。

### Q: 如何修改项目的采集规则？
A: 编辑 `projects/{project_id}/project_config.py` 中的 `RULES` 字典。

### Q: 如何禁用某个项目？
A: 从 `config/projects_config.py` 的 `AVAILABLE_PROJECTS` 列表中删除该项目 ID。

### Q: 采集失败提示 token 过期怎么办？
A: 重新从浏览器复制创作者主页 URL，更新 `projects/{project_id}/project_config.py` 中的对应 URL。

### Q: 如何查看项目的采集数据？
A: 查看 `projects/{project_id}/data/xhs/` 目录下的 jsonl 文件。

### Q: 如何备份项目数据？
A: 备份整个 `projects/{project_id}/` 目录，包含配置、数据和脚本。

### Q: 如何复制一个项目作为模板？
A: 复制整个项目目录，修改 `project_config.py` 中的配置，然后在 `config/projects_config.py` 中注册新项目 ID。

## 技术细节

### 配置加载流程
1. 解析命令行参数（`--project` 或 `--projects`）
2. 从 `config/projects_config.py` 获取项目 ID 列表
3. 动态加载 `projects/{project_id}/project_config.py` 模块
4. 应用配置到全局 `config` 对象
5. 设置数据路径为项目专属目录
6. 执行采集

### 分散式配置优势
- **项目自包含**：每个项目的配置、数据、脚本都在一起
- **独立管理**：修改一个项目不影响其他项目
- **便于迁移**：整个项目目录可以独立迁移
- **清晰隔离**：项目边界清晰，逻辑独立

### 多项目执行流程
1. 解析项目列表
2. 遍历每个项目：
   - 加载项目配置
   - 重置飞书写入状态（避免数据混淆）
   - 执行采集
   - 写入项目专属的飞书表格
3. 输出总结

### 飞书数据隔离
每个项目执行前会调用 `xhs_feishu_sink.reset_for_tests()` 重置状态，确保：
- 不同项目的数据不会混淆
- 每个项目写入各自的飞书表格
- 判重逻辑独立

## 相关文件

- `config/projects_config.py`：项目索引
- `projects/{project_id}/project_config.py`：项目配置
- `tools/project_loader.py`：配置加载器
- `cmd_arg/arg.py`：命令行参数解析
- `main.py`：主入口（多项目执行逻辑）
- `docs/feishu_sync.md`：飞书同步说明
- `docs/xhs_crawl_cost.md`：采集成本说明
