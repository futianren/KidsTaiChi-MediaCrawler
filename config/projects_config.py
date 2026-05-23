# -*- coding: utf-8 -*-
"""
项目索引

列出所有可用的项目 ID。
每个项目的详细配置在各自的项目目录下的 project_config.py 文件中。

项目配置文件位置：projects/{project_id}/project_config.py
"""

# 所有可用的项目 ID 列表
AVAILABLE_PROJECTS = [
    "kids_taichi",      # 少儿太极
    "modern_taichi",    # 现代太极
    "xiaoyao_taichi",   # 逍遥太极（北京逍遥少儿太极独立台账）
]

# 默认项目（如果命令行不指定 --project，使用这个）
DEFAULT_PROJECT = "kids_taichi"

# 项目工作区根目录
PROJECTS_ROOT = "projects"
