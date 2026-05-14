# 小红书创作者（单账号）+ 飞书同步 — 运行记录

> 本文记录一次「仅第一个创作者主页 + 飞书」任务的实际执行过程与问题。**不含任何飞书密钥。**

## 目标

- 平台：`xhs`
- 模式：`--type creator`，仅 **配置列表第一个** 账号（通过 `--creator_id` 传入一条主页 URL）
- 飞书：`FEISHU_SYNC_ENABLED=True` 且凭证完整时，在 `get_creators_and_notes` **正常结束后** 由 `xhs_feishu_sink.flush()` 判重并 `batch_create`
- 本次命令使用：`--xhs_crawl_preset feishu_minimal`（省流：关评论等）

## 命令（项目根目录）

```powershell
cd c:\Users\futianren\Project\Kids_TaiChi\Media_Crawler
$url = 'https://www.xiaohongshu.com/user/profile/656df977000000001901004a?xsec_token=...&xsec_source=pc_note'
python main.py --platform xhs --lt cookie --headless true --type creator `
  --xhs_crawl_preset feishu_minimal --creator_id $url
```

完整日志（含 PowerShell 对 stderr 的包装）：`data/xhs_creator_feishu_last_run.log`  
（该文件可能为 UTF-16，用编辑器打开若见字符间距变大属正常现象。）

---

## 流程（代码顺序）

1. `parse_cmd` → `CRAWLER_TYPE=creator`，`XHS_CREATOR_ID_LIST` 被 CLI 覆盖为单条 URL  
2. `launch_browser` → 若 `SAVE_LOGIN_STATE` 且存在文件，则 `new_context(storage_state=cookiesFile/xhs/session.json)`  
3. 若已有 `session.json`：**不再**叠加注入 `data/xhs_browser_cookies.json`（与参考项目单文件策略一致）  
4. `pong` 通过 → 写回一次 `session.json` → `get_creators_and_notes`  
5. 拉创作者笔记列表 → 并发拉详情 → `store/xhs` 落盘时 `enqueue` 飞书队列  
6. `start` 末尾：`await xhs_feishu_sink.flush()`（**仅当第 5 步整体未抛错走完**）

---

## 本次执行结果

### 第一次启动（已修复）

- **现象**：`UnboundLocalError: session_path_for_platform`  
- **原因**：`start()` 内层 `try` 里写了 `from tools.playwright_session import ... session_path_for_platform`，Python 把该名视为**整函数局部变量**，在更早的 `_session_json = session_path_for_platform(...)` 处尚未绑定即报错。  
- **修复**：内层仅 `import save_storage_state_atomic`，顶层已导入的 `session_path_for_platform` 继续使用（见 `media_platform/xhs/core.py`）。

### 第二次启动（主运行）

| 阶段 | 结果 |
|------|------|
| 登录 / `pong` | 成功（`session.json` 有效） |
| 创作者解析 | `user_id=656df977000000001901004a`，`feishu_minimal` 下 `XHS_FETCH_CREATOR_PROFILE=False` |
| 列表 | 首页约 30 条视频笔记；翻页后第二批约 29 条 |
| 详情拉取 | 首批约 30 条并发详情基本完成 |
| 第二批 | 出现 **`CAPTCHA appeared` / HTTP 461 / Verifytype 216**（风控） |
| 异常 | `get_note_detail_async_task` 中 `raise Exception(...)`，`asyncio.gather` 失败，向上冒泡 |
| **飞书 `flush`** | **未执行**（任务在 `get_creators_and_notes` 内崩溃，`start` 未走到 flush） |
| 会话落盘 | `finally` 中 `finalize_standard_playwright` 仍写出 **`cookiesFile/xhs/session.json`**（日志可见 `Saved storage_state`） |

### 结论

- **本地 JSONL 等**：若笔记在崩溃前已 `update_xhs_note`，可能有部分文件写入（需按需查看 `data/`）。  
- **飞书多维表**：本轮因中途 **461 验证码**，**没有执行 flush**，表上**不保证**有新行。  
- **后续建议**：降低触发风控概率——例如减小 `MAX_CONCURRENCY_NUM`、拉长详情间隔、或使用 **`--headless false`** 在浏览器里过验证后再跑；必要时临时调低 `CRAWLER_MAX_NOTES_COUNT` 做联调。

---

## 自检清单（下次跑前）

- [ ] `cookiesFile/xhs/session.json` 有效（`pong` True）  
- [ ] 创作者 URL 中 `xsec_token` 未过期  
- [ ] `config/feishu_secrets_local.py` 存在且 `FEISHU_SYNC_ENABLED=True`  
- [ ] 多维表字段名与 `FEISHU_FIELD_*` 一致（默认：笔记ID / 笔记标题 / 笔记链接 / 是否发布）  
- [ ] 若需稳定写飞书：先小规模验证（少笔记、低并发），再放大 `CRAWLER_MAX_NOTES_COUNT`

---

## 时间线（本地日志）

- 约 `04:25:47` 进程启动  
- 约 `04:25:58` 进入 `get_creators_and_notes`，开始拉详情  
- 约 `04:34:11` 起连续 **CAPTCHA / 461**  
- 约 `04:34:22` `storage_state` 保存至 `cookiesFile/xhs/session.json`  
- 随后 **`Exception: Failed to get note detail`**，进程以非 0 退出  

---

*文档更新：2026-05-13*
