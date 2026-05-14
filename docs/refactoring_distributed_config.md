# 分散式配置重构总结

## 重构时间
2026-05-13

## 重构原因

用户提出现代太极项目需要独立配置，并建议每个项目的配置应该放在项目文件夹中，使项目逻辑更清晰。

原有的集中式配置（所有项目配置在 `config/projects_config.py` 中）存在以下问题：
- 项目不是完全自包含的
- 修改一个项目需要编辑包含所有项目的配置文件
- 项目边界不够清晰

## 重构方案

采用**分散式配置 + 集中索引**的混合方案：
- 每个项目有独立的 `project_config.py` 配置文件
- `config/projects_config.py` 简化为项目索引（只列出项目 ID）

## 重构内容

### 1. 新建文件

#### 项目配置文件
- **`projects/kids_taichi/project_config.py`**：少儿太极项目配置
  - 13 个创作者账号
  - 飞书表格配置（QdU4bb872aYZPSst5ckcBkAsnnc / tblJw6skYS51FWiu）
  
- **`projects/modern_taichi/project_config.py`**：现代太极项目配置
  - 10 个创作者账号
  - 飞书表格配置（NVzCb6dngaFmEzsLZaJcL3zMnlc / tblKtt4XTowqt2Xn）

### 2. 修改文件

#### 配置索引
- **`config/projects_config.py`**：
  - 从 150+ 行简化为 20 行
  - 只保留 `AVAILABLE_PROJECTS` 列表和 `DEFAULT_PROJECT`
  - 移除所有项目详细配置

#### 项目加载器
- **`tools/project_loader.py`**：
  - 重写配置加载逻辑，支持动态导入项目配置模块
  - 新增 `_load_project_config_module()` 函数
  - 更新 `load_project_config()` 从项目目录加载配置
  - 保持 API 接口不变，向后兼容

#### 文档更新
- **`projects/kids_taichi/README.md`**：更新配置文件位置说明
- **`projects/modern_taichi/README.md`**：补充完整的项目信息
- **`docs/projects_guide.md`**：更新新增项目流程和配置说明

### 3. 重构总结文档
- **`docs/refactoring_distributed_config.md`**：本文档

## 新的目录结构

```
Media_Crawler/
├── config/
│   └── projects_config.py          # 简化为项目索引
├── projects/
│   ├── kids_taichi/
│   │   ├── project_config.py       # 新增：项目配置
│   │   ├── README.md
│   │   ├── data/xhs/
│   │   └── scripts/run.sh
│   └── modern_taichi/
│       ├── project_config.py       # 新增：项目配置
│       ├── README.md
│       ├── data/xhs/
│       └── scripts/run.sh
└── tools/
    └── project_loader.py           # 重写：支持分散式配置
```

## 配置文件格式

### 项目配置文件（`projects/{project_id}/project_config.py`）

```python
# 项目基本信息
PROJECT_NAME = "项目名称"
PROJECT_DESCRIPTION = "项目描述"

# 创作者列表
CREATORS = [
    "https://www.xiaohongshu.com/user/profile/...",
]

# 飞书表格配置
FEISHU = {
    "app_token": "...",
    "table_id": "...",
    "fields": {...},
}

# 采集规则覆盖（可选）
RULES = {
    "only_video_notes": True,
}
```

### 项目索引文件（`config/projects_config.py`）

```python
# 所有可用的项目 ID 列表
AVAILABLE_PROJECTS = [
    "kids_taichi",
    "modern_taichi",
]

# 默认项目
DEFAULT_PROJECT = "kids_taichi"
```

## 测试结果

### 配置加载测试
- ✅ kids_taichi：13 个创作者，配置有效
- ✅ modern_taichi：10 个创作者，配置有效

### 功能测试
- ✅ 项目索引加载
- ✅ 动态配置模块导入
- ✅ 配置应用到全局 config
- ✅ 配置验证
- ✅ 向后兼容性

## 优势对比

### 集中式配置（重构前）
- ❌ 项目不自包含
- ❌ 一个文件会很大（150+ 行）
- ❌ 修改一个项目影响整个配置文件
- ✅ 配置加载简单
- ✅ 便于对比不同项目

### 分散式配置（重构后）
- ✅ 项目完全自包含（配置、数据、脚本都在一起）
- ✅ 项目逻辑更清晰
- ✅ 修改一个项目不影响其他项目
- ✅ 便于项目独立管理和迁移
- ✅ 新增项目只需创建项目文件夹
- ⚠️ 配置加载稍复杂（需要动态导入）

## 向后兼容性

### API 接口保持不变
- `get_available_projects()`
- `load_project_config(project_id)`
- `apply_project_config(project_id)`
- `get_project_name(project_id)`
- `validate_project_config(project_id)`

### 使用方式不变
```bash
# 单项目
python main.py --platform xhs --type creator --project kids_taichi

# 多项目
python main.py --platform xhs --type creator --projects kids_taichi,modern_taichi

# 启动脚本
bash projects/kids_taichi/scripts/run.sh
```

## 新增项目流程

1. 创建项目目录：`projects/new_project/`
2. 创建配置文件：`projects/new_project/project_config.py`
3. 注册到索引：在 `config/projects_config.py` 的 `AVAILABLE_PROJECTS` 中添加项目 ID
4. 创建文档和脚本
5. 测试运行

## 现代太极项目配置

### 创作者账号（10 个）
1. 小宇咂（楚瑷旭）
2. 紫黑是梓禧
3. 🏅张宁语zy✨
4. 马小瑞
5. 阿泽
6. 太极王冰
7. 账号7
8. 若兰
9. 九月太极
10. 请叫我小张

### 飞书表格
- App Token：NVzCb6dngaFmEzsLZaJcL3zMnlc
- Table ID：tblKtt4XTowqt2Xn
- View ID：vewSv84TV8
- 表格链接：https://ccnxtccvgg22.feishu.cn/base/NVzCb6dngaFmEzsLZaJcL3zMnlc?table=tblKtt4XTowqt2Xn&view=vewSv84TV8

### 采集规则
- 仅采集视频笔记
- 不采集评论
- 根据笔记 ID 去重
- "是否发布"默认值为"否"

## 重构完成

所有功能已重构并通过测试，两个项目（kids_taichi 和 modern_taichi）均可正常使用。
