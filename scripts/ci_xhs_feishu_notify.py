#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub Actions CI 小红书采集飞书通知脚本

读取各项目的运行摘要 JSON，格式化后发送到飞书 webhook。
每个项目发送独立的通知消息。
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests


def format_time(seconds: float) -> str:
    """格式化时间为 分钟+秒"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes > 0:
        return f"{minutes}分{secs}秒"
    return f"{secs}秒"


def format_message(summary: Dict[str, Any]) -> tuple[str, str]:
    """
    格式化飞书消息

    Args:
        summary: 项目运行摘要

    Returns:
        (title, content) 元组
    """
    project_name = summary.get("project_name", "未知项目")
    status = summary.get("status", "unknown")
    creators = summary.get("creators", {})
    notes = summary.get("notes", {})
    elapsed = summary.get("elapsed_seconds", 0)
    error_msg = summary.get("error_message")

    # 标题
    if status == "failed":
        title = f"小红书采集 | {project_name} | 运行失败"
    elif status == "partial":
        title = f"小红书采集 | {project_name} | 部分成功"
    elif notes.get("new", 0) > 0:
        title = f"小红书采集 | {project_name} | 新增 {notes['new']} 条"
    else:
        title = f"小红书采集 | {project_name} | 无新增"

    # 内容
    lines = []

    # 错误信息（如果有）
    if error_msg:
        lines.append(f"错误信息: {error_msg}")
        lines.append("")

    # 创作者进度
    creators_total = creators.get("total", 0)
    creators_success = creators.get("success", 0)
    creators_failed = creators.get("failed", 0)
    if creators_total > 0:
        success_rate = int(creators_success * 100 / creators_total) if creators_total else 0
        lines.append(f"创作者进度: {creators_success}/{creators_total} 成功 ({success_rate}%)")
        if creators_failed > 0:
            lines.append(f"  失败 {creators_failed} 个创作者")
    else:
        lines.append("创作者进度: 无数据")

    # 采集统计
    crawled = notes.get("crawled", 0)
    new = notes.get("new", 0)
    duplicate = notes.get("duplicate", 0)
    lines.append(f"采集统计: 抓取 {crawled} 条，新增 {new} 条，重复 {duplicate} 条")

    # 写入结果
    failed = notes.get("failed", 0)
    success_write = new - failed if new >= failed else new
    if failed > 0:
        lines.append(f"写入结果: 成功 {success_write} 条，失败 {failed} 条")
    else:
        lines.append(f"写入结果: 全部成功 ({new} 条)")

    # 执行时间
    lines.append(f"执行时间: {format_time(elapsed)}")

    content = "\n".join(lines)
    return title, content


def send_feishu_notification(
    webhook_url: str,
    title: str,
    content: str,
    retries: int = 3,
    retry_delay: float = 2.0,
) -> bool:
    """
    发送飞书通知

    Args:
        webhook_url: 飞书 webhook 地址
        title: 消息标题
        content: 消息内容
        retries: 重试次数
        retry_delay: 重试延迟（秒）

    Returns:
        是否发送成功
    """
    message = f"{title}\n\n{content}".strip()
    payload = {
        "msg_type": "text",
        "content": {"text": message},
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=10,
            )
            response.raise_for_status()
            response_json = response.json()

            if response_json.get("code") != 0:
                error_msg = response_json.get("msg", "未知错误")
                print(f"[飞书通知] 业务错误 (尝试 {attempt}/{retries}): code={response_json.get('code')}, msg={error_msg}")
                if attempt < retries:
                    time.sleep(retry_delay * (2 ** (attempt - 1)))
                    continue
                return False

            print(f"[飞书通知] 发送成功 (尝试 {attempt}/{retries})")
            return True

        except requests.RequestException as e:
            print(f"[飞书通知] 请求失败 (尝试 {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(retry_delay * (2 ** (attempt - 1)))
                continue
            return False
        except Exception as e:
            print(f"[飞书通知] 未预期错误 (尝试 {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(retry_delay * (2 ** (attempt - 1)))
                continue
            return False

    return False


def main():
    """主函数"""
    # 获取 webhook 地址
    webhook_url = os.environ.get("FEISHU_WEBHOOK", "").strip()
    if not webhook_url:
        print("[错误] 环境变量 FEISHU_WEBHOOK 未设置")
        sys.exit(1)

    # 读取所有项目的摘要
    all_summaries_path = Path("data/ci_all_projects_summary.json")
    if not all_summaries_path.exists():
        print(f"[错误] 找不到汇总文件: {all_summaries_path}")
        sys.exit(1)

    try:
        with open(all_summaries_path, "r", encoding="utf-8") as f:
            all_summaries = json.load(f)
    except Exception as e:
        print(f"[错误] 读取汇总文件失败: {e}")
        sys.exit(1)

    if not all_summaries:
        print("[警告] 汇总文件为空，没有项目数据")
        sys.exit(0)

    # 为每个项目发送独立通知
    success_count = 0
    failed_count = 0

    for summary in all_summaries:
        project_name = summary.get("project_name", "未知项目")
        print(f"\n{'='*60}")
        print(f"[通知] 发送项目通知: {project_name}")
        print(f"{'='*60}")

        title, content = format_message(summary)
        print(f"标题: {title}")
        print(f"内容:\n{content}")
        print()

        success = send_feishu_notification(webhook_url, title, content)
        if success:
            success_count += 1
            print(f"✅ {project_name} 通知发送成功")
        else:
            failed_count += 1
            print(f"❌ {project_name} 通知发送失败")

    # 总结
    print(f"\n{'='*60}")
    print(f"[总结] 通知发送完成")
    print(f"  成功: {success_count}/{len(all_summaries)}")
    print(f"  失败: {failed_count}/{len(all_summaries)}")
    print(f"{'='*60}")

    # 如果有失败，返回非零退出码（但不影响 CI 流程）
    if failed_count > 0:
        print("[警告] 部分通知发送失败，但不影响主流程")
        # 不退出失败，避免影响 CI
        # sys.exit(1)


if __name__ == "__main__":
    main()
