# -*- coding: utf-8 -*-
"""
项目配置加载与应用

负责从各项目目录下的 project_config.py 加载配置，并应用到全局 config 对象。
采用分散式配置：每个项目有独立的配置文件。
"""

import os
import sys
import importlib.util
from typing import Dict, Any, Optional

import config
from config.projects_config import AVAILABLE_PROJECTS, DEFAULT_PROJECT, PROJECTS_ROOT
from tools import utils


def get_available_projects() -> list[str]:
    """获取所有可用的项目 ID 列表"""
    return list(AVAILABLE_PROJECTS)


def _load_project_config_module(project_id: str):
    """
    动态加载项目配置模块

    Args:
        project_id: 项目标识符

    Returns:
        项目配置模块对象

    Raises:
        FileNotFoundError: 配置文件不存在
        ImportError: 配置文件导入失败
    """
    config_path = os.path.join(PROJECTS_ROOT, project_id, "project_config.py")

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"项目 '{project_id}' 的配置文件不存在：{config_path}"
        )

    # 动态导入模块
    spec = importlib.util.spec_from_file_location(
        f"projects.{project_id}.project_config",
        config_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载项目配置：{config_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


def load_project_config(project_id: str) -> Dict[str, Any]:
    """
    加载指定项目的配置

    Args:
        project_id: 项目标识符

    Returns:
        项目配置字典

    Raises:
        ValueError: 项目不存在
        FileNotFoundError: 配置文件不存在
    """
    if project_id not in AVAILABLE_PROJECTS:
        available = ", ".join(get_available_projects())
        raise ValueError(
            f"项目 '{project_id}' 不存在。可用项目：{available}"
        )

    # 加载项目配置模块
    module = _load_project_config_module(project_id)

    # 构建配置字典
    project_config = {
        "name": getattr(module, "PROJECT_NAME", project_id),
        "description": getattr(module, "PROJECT_DESCRIPTION", ""),
        "workspace": os.path.join(PROJECTS_ROOT, project_id),
        "creators": getattr(module, "CREATORS", []),
        "feishu": getattr(module, "FEISHU", {}),
        "rules": getattr(module, "RULES", {}),
    }

    return project_config


def apply_project_config(project_id: str) -> Dict[str, Any]:
    """
    将项目配置应用到全局 config

    Args:
        project_id: 项目标识符

    Returns:
        项目配置字典
    """
    project = load_project_config(project_id)

    utils.logger.info(
        f"[项目配置] 加载项目：{project['name']} ({project_id})"
    )

    # 1. 创作者列表
    config.XHS_CREATOR_ID_LIST = project["creators"]
    utils.logger.info(
        f"[项目配置] 创作者数量：{len(project['creators'])}"
    )

    # 2. 飞书表格配置
    feishu = project["feishu"]
    config.FEISHU_APP_TOKEN = feishu.get("app_token", "")
    config.FEISHU_TABLE_ID = feishu.get("table_id", "")
    config.FEISHU_VIEW_ID = feishu.get("view_id", "")

    # 3. 飞书字段映射
    fields = feishu.get("fields", {})
    config.FEISHU_FIELD_NOTE_ID = fields.get("note_id", "笔记ID")
    config.FEISHU_FIELD_TITLE = fields.get("title", "笔记标题")
    config.FEISHU_FIELD_LINK = fields.get("link", "笔记链接")
    config.FEISHU_FIELD_PUBLISH = fields.get("publish", "是否发布")
    config.FEISHU_PUBLISH_VALUE_ON_CREATE = feishu.get("publish_value_on_create", "否")
    config.FEISHU_LINK_FIELD_FORMAT = feishu.get("link_field_format", "object")

    utils.logger.info(
        f"[项目配置] 飞书表格：{config.FEISHU_APP_TOKEN[:10]}... / {config.FEISHU_TABLE_ID}"
    )

    # 4. 数据存储路径
    workspace = project["workspace"]
    config.SAVE_DATA_PATH = os.path.join(workspace, "data")

    # 创建数据目录（如果不存在）
    os.makedirs(config.SAVE_DATA_PATH, exist_ok=True)
    utils.logger.info(
        f"[项目配置] 数据路径：{config.SAVE_DATA_PATH}"
    )

    # 5. 规则覆盖（如果有）
    rules = project.get("rules", {})
    if rules:
        for key, value in rules.items():
            config_key = f"XHS_{key.upper()}"
            if hasattr(config, config_key):
                old_value = getattr(config, config_key)
                setattr(config, config_key, value)
                utils.logger.info(
                    f"[项目配置] 规则覆盖：{config_key} = {value} (原值: {old_value})"
                )
            else:
                utils.logger.warning(
                    f"[项目配置] 未知规则配置项：{config_key}"
                )

    return project


def get_project_name(project_id: str) -> str:
    """
    获取项目显示名称

    Args:
        project_id: 项目标识符

    Returns:
        项目名称
    """
    try:
        project = load_project_config(project_id)
        return project["name"]
    except Exception:
        return project_id


def get_default_project() -> str:
    """获取默认项目 ID"""
    return DEFAULT_PROJECT


def validate_project_config(project_id: str) -> tuple[bool, Optional[str]]:
    """
    验证项目配置是否完整

    Args:
        project_id: 项目标识符

    Returns:
        (是否有效, 错误信息)
    """
    try:
        project = load_project_config(project_id)
    except ValueError as e:
        return False, str(e)
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"加载配置失败：{str(e)}"

    # 检查创作者列表
    if not project.get("creators"):
        return False, f"项目 '{project_id}' 的创作者列表为空"

    # 检查飞书配置
    feishu = project.get("feishu", {})
    if not feishu.get("app_token"):
        return False, f"项目 '{project_id}' 缺少飞书 app_token"
    if not feishu.get("table_id"):
        return False, f"项目 '{project_id}' 缺少飞书 table_id"

    # 检查字段映射
    fields = feishu.get("fields", {})
    required_fields = ["note_id", "title", "link", "publish"]
    for field in required_fields:
        if not fields.get(field):
            return False, f"项目 '{project_id}' 缺少飞书字段映射：{field}"

    return True, None

