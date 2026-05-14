# 少儿太极项目

## 项目目标

采集少儿太极拳相关的小红书内容，用于内容运营和市场分析。

## 采集账号（13 个）

1. **青少儿太极阿杜**（656df977000000001901004a）- 头部账号，教学内容为主
2. **北京逍遥少儿太极**（62233d5b00000000100068cf）- 地域性账号
3. **武术小娃**（642fede9000000000f0125cb）- 武术综合内容
4. **太极静心**（5df2e6c2000000000100717a）- 太极文化传播
5. **偲屹siri**（62f07fd6000000001f0147a4）- 少儿太极学习记录
6. **蕊宝学太极**（5de32d6d0000000001002d4b）- 儿童太极学习分享
7. **太极严光皓**（67b93ad2000000000e01375d）- 青少年太极教学
8. **太极萱萱**（599a866c6a6a691b72914f22）- 少儿太极推广
9. **一力一家太极**（64509ed70000000012036b0c）- 家庭太极教育
10. **仁武堂武术**（67f369860000000007003332）- 武术培训机构
11. **崇武堂武术训练基地**（68492002000000001b018d7d）- 武术训练基地
12. **博武堂卢教练**（691d6d310000000037002e66）- 武术教练个人账号
13. **杭州教武术王教练**（5b26542c11be10280d65ff6c）- 地域性武术教练

## 飞书表格

- **表格名称**：少儿太极内容库
- **App Token**：QdU4bb872aYZPSst5ckcBkAsnnc
- **Table ID**：tblJw6skYS51FWiu
- **View ID**：vewl0XfIvD
- **表格链接**：https://ccnxtccvgg22.feishu.cn/base/QdU4bb872aYZPSst5ckcBkAsnnc?table=tblJw6skYS51FWiu&view=vewl0XfIvD

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
bash projects/kids_taichi/scripts/run.sh

# 或者在项目根目录
bash projects/kids_taichi/scripts/run.sh
```

### 方式 2：手动指定参数

```bash
python main.py --platform xhs --type creator --project kids_taichi
```

### 方式 3：与其他项目一起执行

```bash
python main.py --platform xhs --type creator --projects kids_taichi,modern_taichi
```

## 数据位置

- **本地数据**：`projects/kids_taichi/data/xhs/`
  - `notes_YYYYMMDD_HHMMSS.jsonl` - 笔记数据
  - `creator_YYYYMMDD_HHMMSS.jsonl` - 创作者数据
- **飞书表格**：[点击查看](https://ccnxtccvgg22.feishu.cn/base/QdU4bb872aYZPSst5ckcBkAsnnc?table=tblJw6skYS51FWiu&view=vewl0XfIvD)

## 项目配置

项目配置位于 `projects/kids_taichi/project_config.py`。

如需修改采集规则，可在配置文件的 `RULES` 字典中覆盖全局默认值。

## 注意事项

1. **Token 过期**：创作者 URL 中的 `xsec_token` 会过期，如果采集失败，需要重新从浏览器复制 URL 并更新配置
2. **采集频率**：建议每天采集一次，避免频繁请求
3. **数据备份**：定期备份 `data/` 目录和飞书表格数据
