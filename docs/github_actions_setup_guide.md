# GitHub Actions 配置指南

## 🎯 快速开始

本指南帮助你完成 GitHub Actions 的最后配置步骤。

## ✅ 已完成的工作

代码实现已全部完成：

1. ✅ 统计数据收集（`tools/feishu/xhs_feishu_sink.py`）
2. ✅ 创作者状态跟踪（`media_platform/xhs/core.py`）
3. ✅ 运行摘要输出（`main.py`）
4. ✅ 飞书通知脚本（`scripts/ci_xhs_feishu_notify.py`）
5. ✅ GitHub Actions 工作流（`.github/workflows/xhs-daily-kids-modern-feishu.yml`）
6. ✅ 允许 session.json 提交（`.gitignore`）

## 📋 接下来需要做的事

### 1. 配置 GitHub Secrets

#### 步骤 1: 获取飞书凭证

打开本地文件 `config/feishu_secrets_local.py`，复制以下值：

```python
FEISHU_APP_ID = "cli_xxxxx"  # 复制这个值
FEISHU_APP_SECRET = "xxxxx"  # 复制这个值
```

#### 步骤 2: 在 GitHub 配置 Secrets

1. 打开浏览器，访问你的 GitHub 仓库：
   ```
   https://github.com/futianren/KidsTaiChi-MediaCrawler
   ```

2. 点击 `Settings`（设置）标签

3. 在左侧菜单中，点击 `Secrets and variables` → `Actions`

4. 点击 `New repository secret` 按钮

5. 添加以下 3 个 secrets：

   **Secret 1: FEISHU_WEBHOOK**
   - Name: `FEISHU_WEBHOOK`
   - Value: `https://open.feishu.cn/open-apis/bot/v2/hook/53784278-b0dd-4073-828d-c919b173dfee`
   - 点击 `Add secret`

   **Secret 2: FEISHU_APP_ID**
   - Name: `FEISHU_APP_ID`
   - Value: 从 `feishu_secrets_local.py` 复制的 `FEISHU_APP_ID` 值
   - 点击 `Add secret`

   **Secret 3: FEISHU_APP_SECRET**
   - Name: `FEISHU_APP_SECRET`
   - Value: 从 `feishu_secrets_local.py` 复制的 `FEISHU_APP_SECRET` 值
   - 点击 `Add secret`

### 2. 提交代码到 GitHub

```bash
# 1. 查看修改的文件
git status

# 2. 添加所有修改（包括 session.json）
git add .

# 3. 提交
git commit -m "feat: add GitHub Actions with Feishu notification

- Add statistics tracking in xhs_feishu_sink.py
- Add creator status tracking in core.py
- Add run summary output in main.py
- Add Feishu notification script
- Update GitHub Actions workflow
- Allow session.json to be committed
- Add documentation"

# 4. 推送到 GitHub
git push origin main
```

### 3. 验证 session.json 已提交

```bash
# 检查 session.json 是否在 Git 中
git ls-files | grep session.json

# 应该看到输出：
# cookiesFile/xhs/session.json
```

如果没有输出，说明文件未被跟踪，需要强制添加：

```bash
git add -f cookiesFile/xhs/session.json
git commit -m "chore: add session.json for CI"
git push origin main
```

### 4. 手动触发测试

1. 访问 GitHub Actions 页面：
   ```
   https://github.com/futianren/KidsTaiChi-MediaCrawler/actions
   ```

2. 在左侧选择 `XHS daily — kids & modern → Feishu`

3. 点击右上角的 `Run workflow` 按钮

4. 选择 `Branch: main`

5. 点击绿色的 `Run workflow` 按钮

6. 等待执行完成（约 5-10 分钟）

7. 检查飞书群是否收到通知

### 5. 查看执行日志

如果执行失败，点击失败的运行记录，查看详细日志：

1. 点击运行记录（如 `XHS daily — kids & modern → Feishu #1`）
2. 点击 `crawl-and-notify` 作业
3. 展开各个步骤查看日志
4. 重点检查：
   - `Verify secrets` - 确认 secrets 配置正确
   - `Verify session.json exists` - 确认 session.json 存在
   - `Run XHS creator` - 查看爬虫执行日志
   - `Feishu webhook summary` - 查看通知发送日志

### 6. 下载运行结果

执行完成后，可以下载运行结果：

1. 在运行记录页面，滚动到底部
2. 找到 `Artifacts` 部分
3. 点击 `xhs-daily-ci` 下载
4. 解压后可以看到：
   - `data/ci_all_projects_summary.json` - 所有项目汇总
   - `projects/kids_taichi/data/` - 少儿太极数据
   - `projects/modern_taichi/data/` - 现代太极数据

## 🔍 故障排查

### 问题 1: Secrets 未配置

**错误信息**:
```
Error: Missing repository secret: FEISHU_WEBHOOK
```

**解决方法**:
- 检查 GitHub Secrets 是否正确配置
- 确认 Secret 名称拼写正确（区分大小写）

### 问题 2: session.json 不存在

**错误信息**:
```
Error: Missing cookiesFile/xhs/session.json
```

**解决方法**:
```bash
# 检查文件是否存在
ls -la cookiesFile/xhs/session.json

# 强制添加到 Git
git add -f cookiesFile/xhs/session.json
git commit -m "chore: add session.json"
git push
```

### 问题 3: 飞书通知发送失败

**错误信息**:
```
[飞书通知] 请求失败 (尝试 1/3): ...
```

**解决方法**:
- 检查 FEISHU_WEBHOOK 地址是否正确
- 测试 webhook 是否有效：
  ```bash
  curl -X POST "https://open.feishu.cn/open-apis/bot/v2/hook/..." \
    -H "Content-Type: application/json" \
    -d '{"msg_type":"text","content":{"text":"测试消息"}}'
  ```

### 问题 4: 飞书写入失败

**错误信息**:
```
[xhs_feishu_sink] 飞书写入失败条数: 3
```

**解决方法**:
- 检查 FEISHU_APP_ID 和 FEISHU_APP_SECRET 是否正确
- 确认飞书应用有表格写入权限
- 检查项目配置中的 app_token 和 table_id 是否正确

## 📅 定时执行

工作流已配置为每天北京时间上午 2:00 自动执行。

如需修改执行时间，编辑 `.github/workflows/xhs-daily-kids-modern-feishu.yml`：

```yaml
schedule:
  # 北京时间每日 02:00（UTC 前一日 18:00）
  - cron: "0 18 * * *"
```

Cron 表达式说明：
- `0 18 * * *` = 每天 UTC 18:00（北京时间次日 02:00）
- `0 10 * * *` = 每天 UTC 10:00（北京时间 18:00）
- `0 2 * * *` = 每天 UTC 02:00（北京时间 10:00）

## ✅ 验证清单

在提交代码前，请确认：

- [ ] 本地 `config/feishu_secrets_local.py` 已配置完整
- [ ] `cookiesFile/xhs/session.json` 文件存在
- [ ] GitHub Secrets 已配置（3 个）
- [ ] 代码已提交并推送到 GitHub
- [ ] session.json 已被 Git 跟踪
- [ ] 手动触发测试成功
- [ ] 飞书群收到通知消息

## 📞 需要帮助？

如果遇到问题：

1. 查看 GitHub Actions 日志
2. 查看 `docs/github_action_feishu_notification.md` 详细文档
3. 检查本地是否能正常运行：
   ```bash
   python main.py --platform xhs --type creator --lt cookie \
     --projects kids_taichi,modern_taichi \
     --xhs_crawl_preset feishu_minimal \
     --headless true --get_comment false \
     --save_data_option jsonl
   ```

---

**配置完成后，你将拥有：**
- ✅ 每天自动采集小红书内容
- ✅ 自动写入飞书多维表格
- ✅ 自动发送飞书通知
- ✅ 完整的运行日志和数据备份
