# GitHub Action 小红书采集飞书通知实现说明

## 📋 概述

本文档说明了 GitHub Actions 自动化小红书采集并发送飞书通知的完整实现方案。

## 🎯 功能特性

- ✅ 每天北京时间上午 2:00 自动执行
- ✅ 顺序执行两个项目（kids_taichi、modern_taichi）
- ✅ 采集创作者笔记并写入飞书多维表格
- ✅ 每个项目发送独立的飞书通知
- ✅ 失败时也发送通知并说明原因
- ✅ 飞书通知失败自动重试 3 次

## 📊 通知消息格式

### 成功示例
```
小红书采集 | 少儿太极 | 新增 15 条

创作者进度: 12/13 成功 (92%)
采集统计: 抓取 156 条，新增 15 条，重复 138 条
写入结果: 全部成功 (15 条)
执行时间: 3分25秒
```

### 失败示例
```
小红书采集 | 少儿太极 | 运行失败

错误信息: Playwright session timeout
创作者进度: 5/13 成功 (38%)
采集统计: 抓取 45 条，新增 8 条，重复 37 条
写入结果: 成功 42 条，失败 3 条
执行时间: 1分12秒
```

## 🔧 实现细节

### 1. 统计数据收集

**文件**: `tools/feishu/xhs_feishu_sink.py`

新增统计指标：
- `_stats_crawled`: 本次抓取总数
- `_stats_new`: 新增到飞书
- `_stats_duplicate`: 重复跳过
- `_stats_failed`: 写入失败

新增函数：
- `get_stats()`: 获取统计数据

### 2. 创作者状态跟踪

**文件**: `media_platform/xhs/core.py`

新增属性：
- `_creator_stats`: Dict[str, bool] - 记录每个创作者 URL 的成功/失败状态

新增方法：
- `get_creator_stats()`: 返回创作者统计信息

### 3. 运行摘要输出

**文件**: `main.py`

修改多项目执行逻辑：
- 每个项目执行后生成 `projects/{project_id}/data/ci_run_summary.json`
- 所有项目完成后生成 `data/ci_all_projects_summary.json`

摘要 JSON 格式：
```json
{
  "project_id": "kids_taichi",
  "project_name": "少儿太极",
  "status": "success",
  "creators": {
    "total": 13,
    "success": 12,
    "failed": 1,
    "failed_urls": ["https://..."]
  },
  "notes": {
    "crawled": 156,
    "new": 15,
    "duplicate": 138,
    "failed": 3
  },
  "elapsed_seconds": 205.3,
  "error_message": null,
  "timestamp": "2026-05-14T02:15:30Z"
}
```

### 4. 飞书通知脚本

**文件**: `scripts/ci_xhs_feishu_notify.py`

功能：
- 读取 `data/ci_all_projects_summary.json`
- 为每个项目格式化通知消息
- 发送到飞书 webhook（失败重试 3 次，指数退避）
- 输出发送结果统计

### 5. GitHub Actions 工作流

**文件**: `.github/workflows/xhs-daily-kids-modern-feishu.yml`

执行步骤：
1. 检出代码
2. 安装 Python 3.11 和依赖
3. 安装 Playwright Chromium
4. 禁用 CDP 模式（CI 环境）
5. 验证 secrets 和 session.json
6. 执行爬虫（两个项目）
7. 发送飞书通知
8. 上传运行日志

## 🔐 GitHub Secrets 配置

需要在 GitHub 仓库设置以下 Secrets：

### 必需的 Secrets

1. **FEISHU_WEBHOOK**
   ```
   https://open.feishu.cn/open-apis/bot/v2/hook/53784278-b0dd-4073-828d-c919b173dfee
   ```

2. **FEISHU_APP_ID**
   - 从本地 `config/feishu_secrets_local.py` 复制

3. **FEISHU_APP_SECRET**
   - 从本地 `config/feishu_secrets_local.py` 复制

### 配置步骤

1. 打开 GitHub 仓库页面
2. 进入 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. 分别添加上述 3 个 secrets

## 📁 文件变更清单

### 修改的文件
- `tools/feishu/xhs_feishu_sink.py` - 添加统计功能
- `media_platform/xhs/core.py` - 添加创作者状态跟踪
- `main.py` - 添加运行摘要输出
- `.github/workflows/xhs-daily-kids-modern-feishu.yml` - 更新工作流
- `.gitignore` - 允许 session.json 提交

### 新增的文件
- `scripts/ci_xhs_feishu_notify.py` - 飞书通知脚本
- `docs/github_action_feishu_notification.md` - 本文档

## 🚀 使用方法

### 本地测试

```bash
# 1. 确保本地配置完整
cat config/feishu_secrets_local.py

# 2. 执行多项目采集
python main.py --platform xhs --type creator --lt cookie \
  --projects kids_taichi,modern_taichi \
  --xhs_crawl_preset feishu_minimal \
  --headless true --get_comment false \
  --save_data_option jsonl

# 3. 测试通知脚本
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/..."
python scripts/ci_xhs_feishu_notify.py
```

### GitHub Actions 手动触发

1. 进入 GitHub 仓库页面
2. 点击 `Actions` 标签
3. 选择 `XHS daily — kids & modern → Feishu`
4. 点击 `Run workflow` → `Run workflow`

### 定时执行

工作流已配置为每天北京时间上午 2:00 自动执行：
```yaml
schedule:
  - cron: "0 18 * * *"  # UTC 18:00 = 北京时间次日 02:00
```

## 🔍 故障排查

### 1. 通知未发送

检查：
- GitHub Secrets 是否正确配置
- FEISHU_WEBHOOK 地址是否有效
- 查看 Actions 日志中的错误信息

### 2. 采集失败

检查：
- `cookiesFile/xhs/session.json` 是否存在且有效
- 创作者 URL 是否过期（xsec_token 有时效性）
- 查看 Actions 日志中的详细错误

### 3. 飞书写入失败

检查：
- FEISHU_APP_ID 和 FEISHU_APP_SECRET 是否正确
- 飞书应用是否有表格写入权限
- 表格 app_token 和 table_id 是否正确

## 📈 监控指标

每次运行会生成以下文件（可在 Actions Artifacts 下载）：

- `data/ci_all_projects_summary.json` - 所有项目汇总
- `projects/kids_taichi/data/ci_run_summary.json` - 少儿太极摘要
- `projects/modern_taichi/data/ci_run_summary.json` - 现代太极摘要
- `projects/*/data/*.jsonl` - 采集的笔记数据

## 🔄 后续优化建议

1. **通知增强**
   - 添加失败创作者列表（当前只统计数量）
   - 添加趋势对比（与昨天对比）

2. **错误处理**
   - 单个创作者失败不影响其他创作者
   - 添加更详细的错误分类

3. **性能优化**
   - 并发采集多个创作者
   - 缓存已采集的笔记

## 📞 联系方式

如有问题，请查看：
- GitHub Issues: https://github.com/futianren/KidsTaiChi-MediaCrawler/issues
- 项目文档: `docs/` 目录

---

**最后更新**: 2026-05-14
**版本**: 1.0.0
