# 北大青鸟培训项目

## 项目目标

采集北大青鸟及相关职业教育机构的小红书内容，用于内容运营和市场分析。

## 采集账号（5 个）

1. **北大青鸟职业教育网**（667e622b000000000d02432f）
2. **北大青鸟职业教育咨询**（5db16b6800000000010021e9）
3. **北京青鸟华腾职业培训中心**（66a9f818000000000b03113f）
4. **北大青鸟**（666a42c8000000000303181d）
5. **金来盛青鸟职业教育**（64803cd10000000012036171）

## 飞书表格

- **表格链接**：https://ccnxtccvgg22.feishu.cn/base/W3WPbvjOLaF0zssAn87cfiignsm?table=tblQ5Rf1d3mR0nje&view=vewl0XfIvD
- **App Token**：W3WPbvjOLaF0zssAn87cfiignsm
- **Table ID**：tblQ5Rf1d3mR0nje
- **View ID**：vewl0XfIvD（视图名：待发布记录）

### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 笔记ID | 文本 | 小红书笔记唯一标识 |
| 笔记标题 | 文本 | 笔记标题 |
| 笔记链接 | URL | 笔记链接 |
| 是否发布 | 单选 | 默认值：否 |

## 采集规则

- **图文 + 视频均采集**（项目内覆盖 `feishu_minimal` 预设的「仅视频」默认值）
- **不采集评论**：不请求一级和二级评论
- **每个账号主页最多 1 页**：约 30 条笔记（全局 `XHS_CREATOR_MAX_LIST_PAGES=1`）
- **使用 feishu_minimal 预设**：省流量模式（关评论、不下载媒体、不拉创作者资料）

## 快速启动

```bash
bash projects/beida_qingniao/scripts/run.sh
```

或：

```bash
python main.py --platform xhs --type creator --project beida_qingniao \
  --xhs_crawl_preset feishu_minimal --headless true
```

## 数据与配置

- **本地数据**：`projects/beida_qingniao/data/xhs/`
- **配置文件**：`projects/beida_qingniao/project_config.py`
