#!/bin/bash
# 北大青鸟培训项目采集启动脚本

cd "$(dirname "$0")/../../.."

echo "=========================================="
echo "北大青鸟培训项目 - 小红书内容采集"
echo "=========================================="
echo ""

python main.py \
  --platform xhs \
  --type creator \
  --project beida_qingniao \
  --xhs_crawl_preset feishu_minimal \
  --headless true

echo ""
echo "=========================================="
echo "北大青鸟培训项目采集完成"
echo "=========================================="
