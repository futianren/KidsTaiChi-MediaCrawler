#!/bin/bash
# 现代太极项目采集启动脚本

# 回到项目根目录
cd "$(dirname "$0")/../../.."

echo "=========================================="
echo "现代太极项目 - 小红书内容采集"
echo "=========================================="
echo ""

# 启动采集
python main.py \
  --platform xhs \
  --type creator \
  --project modern_taichi \
  --xhs_crawl_preset feishu_minimal \
  --headless true

echo ""
echo "=========================================="
echo "现代太极项目采集完成"
echo "=========================================="
