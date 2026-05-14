# 多项目管理功能实现总结

## 实现时间
2026-05-13

## 实现内容

### 1. 新建文件

#### 配置文件
- **`config/projects_config.py`**：项目配置集中管理
  - 包含 `kids_taichi` 和 `modern_taichi` 两个项目配置
  - 定义了创作者列表、飞书表格、字段映射、规则覆盖等

#### 工具文件
- **`tools/project_loader.py`**：项目配置加载器
  - `get_available_projects()`：获取所有可用项目
  - `load_project_config()`：加载项目配置
  - `apply_project_config()`：应用项目配置到全局 config
  - `get_project_name()`：获取项目显示名称
  - `validate_project_config()`：验证项目配置完整性

#### 项目文档
- **`projects/kids_taichi/README.md`**：少儿太极项目说明
- **`projects/modern_taichi/README.md`**：现代太极项目说明
- **`docs/projects_guide.md`**：项目管理指南

#### 启动脚本
- **`projects/kids_taichi/scripts/run.sh`**：少儿太极项目启动脚本
- **`projects/modern_taichi/scripts/run.sh`**：现代太极项目启动脚本

### 2. 修改文件

#### 命令行参数
- **`cmd_arg/arg.py`**：
  - 新增 `--project` 参数：指定单个项目
  - 新增 `--projects` 参数：顺序执行多个项目（逗号分隔）
  - 返回值中添加 `project` 和 `projects` 字段

#### 主入口
- **`main.py`**：
  - 添加多项目执行逻辑
  - 在 creator 模式下自动加载项目配置
  - 支持顺序执行多个项目
  - 每个项目执行前重置飞书写入状态

#### 配置文件
- **`config/xhs_config.py`**：
  - 注释掉原有的 `XHS_CREATOR_ID_LIST`（已迁移到 projects_config.py）
  - 添加说明：创作者列表已迁移到项目配置

### 3. 数据迁移

- **迁移路径**：`data/xhs/` → `projects/kids_taichi/data/xhs/`
- **迁移内容**：
  - `jsonl/creator_comments_2026-05-13.jsonl`
  - `jsonl/creator_contents_2026-05-12.jsonl`
  - `jsonl/creator_contents_2026-05-13.jsonl`
  - `jsonl/search_comments_2026-04-22.jsonl`
  - `jsonl/search_contents_2026-04-22.jsonl`
  - `jsonl/search_contents_2026-05-13.jsonl`

### 4. 目录结构

```
Media_Crawler/
├── config/
│   ├── projects_config.py          # 新增：项目配置
│   └── xhs_config.py               # 修改：注释掉创作者列表
├── tools/
│   └── project_loader.py           # 新增：项目加载器
├── cmd_arg/
│   └── arg.py                      # 修改：添加项目参数
├── main.py                         # 修改：多项目执行逻辑
├── projects/                       # 新增：项目工作区
│   ├── kids_taichi/
│   │   ├── README.md
│   │   ├── data/xhs/               # 迁移的数据
│   │   └── scripts/run.sh
│   └── modern_taichi/
│       ├── README.md
│       ├── data/xhs/
│       └── scripts/run.sh
└── docs/
    └── projects_guide.md           # 新增：项目管理指南
```

## 使用方式

### 单项目采集

**方式 1：使用启动脚本**
```bash
bash projects/kids_taichi/scripts/run.sh
```

**方式 2：命令行指定**
```bash
python main.py --platform xhs --type creator --project kids_taichi
```

### 多项目顺序采集

```bash
python main.py --platform xhs --type creator --projects kids_taichi,modern_taichi
```

### 使用默认项目

```bash
# 不指定 --project，自动使用 DEFAULT_PROJECT (kids_taichi)
python main.py --platform xhs --type creator
```

## 测试结果

### 集成测试
- ✓ 配置加载测试通过
- ✓ 项目加载器测试通过
- ✓ 配置应用测试通过
- ✓ 命令行参数测试通过
- ✓ 项目验证测试通过

### 项目验证
- ✓ `kids_taichi`：配置完整，13 个创作者账号
- ⚠ `modern_taichi`：创作者列表为空（待补充）

### 数据迁移
- ✓ 6 个数据文件已迁移到 `projects/kids_taichi/data/xhs/jsonl/`

## 核心功能

### 1. 配置隔离
- 每个项目独立的创作者列表
- 每个项目独立的飞书表格配置
- 每个项目独立的字段映射
- 每个项目可选的规则覆盖

### 2. 数据隔离
- 每个项目独立的数据目录：`projects/{project_id}/data/`
- 每个项目写入独立的飞书表格
- 多项目执行时自动重置飞书写入状态，避免数据混淆

### 3. 灵活执行
- 支持单项目执行
- 支持多项目顺序执行
- 支持默认项目
- 兼容原有的 `--creator_id` 参数（不使用项目配置）

## 后续工作

### modern_taichi 项目配置
需要在 `config/projects_config.py` 中补充：
1. 创作者账号列表（从小红书网页版复制 URL）
2. 飞书表格信息（`app_token`、`table_id`）
3. 字段映射（根据实际表格列名）

### 可选优化
1. 添加项目执行日志（每个项目单独的日志文件）
2. 添加项目执行统计（采集数量、耗时等）
3. 添加项目配置校验命令（`python main.py --validate-projects`）

## 兼容性

### 向后兼容
- 原有的 `--creator_id` 参数仍然可用
- 原有的搜索模式、详情模式不受影响
- 原有的配置文件保持不变（仅注释说明）

### 不影响现有功能
- 其他平台（抖音、快手等）不受影响
- 飞书同步逻辑保持不变
- 数据存储格式保持不变

## 文档

- **项目管理指南**：`docs/projects_guide.md`
- **少儿太极项目说明**：`projects/kids_taichi/README.md`
- **现代太极项目说明**：`projects/modern_taichi/README.md`
- **飞书同步说明**：`docs/feishu_sync.md`（已有）
- **采集成本说明**：`docs/xhs_crawl_cost.md`（已有）

## 实现完成

所有功能已实现并通过测试，可以开始使用。
