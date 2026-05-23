#!/bin/bash
# 逍遥太极项目采集启动脚本

cd "$(dirname "$0")/../../.."

echo "=========================================="
echo "逍遥太极项目 - 小红书内容采集"
echo "=========================================="
echo ""

python main.py \
  --platform xhs \
  --type creator \
  --project xiaoyao_taichi \
  --xhs_crawl_preset feishu_minimal \
  --headless true

echo ""
echo "=========================================="
echo "逍遥太极项目采集完成"
echo "=========================================="
