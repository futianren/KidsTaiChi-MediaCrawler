# 现代太极项目

## 项目目标

采集现代太极拳相关的小红书内容，用于内容运营和市场分析。

## 采集账号（10 个）

1. **小宇咂（楚瑷旭）**（5add33f44eacab3a6907a0a7）
2. **紫黑是梓禧**（59f056b34eacab5f8070eac9）
3. **🏅张宁语zy✨**（59e09cfdde5fb45a28c3fcc1）
4. **马小瑞**（5f465b160000000001008d90）
5. **阿泽**（60a3c53d0000000001009463）
6. **太极王冰**（67a457ad000000000e0105c8）
7. **账号7**（691fabba000000003700b13b）
8. **若兰**（5dd00a610000000001003e05）
9. **九月太极**（68a529e0000000001901044c）
10. **请叫我小张**（5f28d13e0000000001002176）

## 飞书表格

- **表格名称**：现代太极内容库
- **App Token**：NVzCb6dngaFmEzsLZaJcL3zMnlc
- **Table ID**：tblKtt4XTowqt2Xn
- **View ID**：vewSv84TV8
- **表格链接**：https://ccnxtccvgg22.feishu.cn/base/NVzCb6dngaFmEzsLZaJcL3zMnlc?table=tblKtt4XTowqt2Xn&view=vewSv84TV8

### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 笔记ID | 文本 | 小红书笔记唯一标识 |
| 笔记标题 | 文本 | 笔记标题 |
| 笔记链接 | URL | 笔记链接（对象格式） |
| 是否发布 | 单选 | 默认值：否 |

## 采集规则

- **仅采集视频笔记**：跳过图文笔记
- **不采集评论**：不请求一级和二级评论
- **不下载媒体文件**：不下载视频和图片到本地
- **每个账号主页最多 1 页**：约 30 条笔记
- **使用 feishu_minimal 预设**：省流量模式

## 快速启动

### 方式 1：使用启动脚本（推荐）

```bash
# Windows (Git Bash)
bash projects/modern_taichi/scripts/run.sh

# 或者在项目根目录
bash projects/modern_taichi/scripts/run.sh
```

### 方式 2：手动指定参数

```bash
python main.py --platform xhs --type creator --project modern_taichi
```

### 方式 3：与其他项目一起执行

```bash
python main.py --platform xhs --type creator --projects kids_taichi,modern_taichi
```

## 数据位置

- **本地数据**：`projects/modern_taichi/data/xhs/`
  - `notes_YYYYMMDD_HHMMSS.jsonl` - 笔记数据
  - `creator_YYYYMMDD_HHMMSS.jsonl` - 创作者数据
- **飞书表格**：[点击查看](https://ccnxtccvgg22.feishu.cn/base/NVzCb6dngaFmEzsLZaJcL3zMnlc?table=tblKtt4XTowqt2Xn&view=vewSv84TV8)

## 项目配置

项目配置位于 `projects/modern_taichi/project_config.py`。

如需修改采集规则，可在配置文件的 `RULES` 字典中覆盖全局默认值。

## 注意事项

1. **Token 过期**：创作者 URL 中的 `xsec_token` 会过期，如果采集失败，需要重新从浏览器复制 URL 并更新配置
2. **采集频率**：建议每天采集一次，避免频繁请求
3. **数据备份**：定期备份 `data/` 目录和飞书表格数据
