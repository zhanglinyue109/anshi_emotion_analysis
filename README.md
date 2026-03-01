# appreciation_poem

本仓库用于研究“安史之乱语境下唐诗情感变迁”，核心工作是把古诗从原始文本处理到可分析数据，再完成情感标注、统计和聚类分析。

## 1. 项目核心思想

项目主线是一个“文本到证据”的流水线：

1. 从原始诗歌表格中拆分出可分析单句。
2. 用统一情感标签体系对单句做自动标注（含失败重试机制）。
3. 按编年、作者、地点做情感分布统计。
4. 对“情感表达句”做向量化与聚类，观察主题和情绪簇结构。
5. 在翻译与 VA（Valence/Arousal）方向做补充实验，支撑论文分析。

优先复现目录：`anshi_emosion_paper_release/`（主流程更完整、文件更集中）。

## 2. 主流程（建议顺序）

```bash
python anshi.py
python annotate.py
python anshi_count.py

python emopoem_get.py
python embedding_get.py
python kcluster.py
```

主输入输出对应关系：

- `Anshi.xlsx` -> `anshi.py` -> `anshi_poems.csv`
- `anshi_poems.csv` -> `annotate.py` -> `anshi_annotated.xlsx`
- `anshi_annotated.xlsx` -> `anshi_count.py` -> `anshi_analysis.xlsx`
- `appreciation.jsonl` -> `emopoem_get.py` -> `emo_poems.txt/jsonl`
- `emo_poems.txt` -> `embedding_get.py` -> `appreciation_embeddings.npy`
- `appreciation_embeddings.npy` + `emo_poems.txt` -> `kcluster.py` -> 聚类结果与图

## 3. 如何修改（大纲）

建议按以下顺序改，避免牵一发动全身：

1. 配置层改造
- 把 `API_KEY` / `BASE_URL` / `MODEL` 改成环境变量读取。
- 把脚本中的绝对路径（如 `/home/...`）统一改为相对路径或命令行参数。

2. 数据与标签层改造
- `anshi.py`：调整拆句规则、字段映射（列索引）和清洗规则。
- `annotate.py`：维护标签集合、提示词和重试策略。
- `anshi_count.py`：维护二级->一级标签映射和统计口径。

3. 表征与聚类层改造
- `embedding_get.py`：替换编码模型、批大小、最大长度。
- `kcluster.py`：调整聚类范围、降维参数、可视化样式。

4. 评估层改造（可选）
- `test_annotator.py` / `annotator_count.py` / `va_annotator.py`：调整一致性指标与报表字段。

## 4. 仓库整理意见

当前仓库包含“主流程文件 + 历史实验 + 大体量产物”，建议分层管理：

1. 目录分层
- `src/`：仅放可复用脚本
- `data/raw`、`data/interim`、`data/processed`
- `outputs/figures`、`outputs/tables`
- `papers/`：论文与投稿材料

2. 配置与依赖
- 新增 `requirements.txt` 或 `pyproject.toml`
- 新增 `.env.example`（只保留变量名，不含真实密钥）

3. 安全与可复现
- 删除代码中的明文密钥并立即轮换现有 Key
- 保留一个“单一真相流程”（建议以 `anshi_emosion_paper_release/` 为基线）
- 对实验脚本标记 `archive/` 或 `legacy/`，避免主流程混淆

## 5. 开发规范（本仓库建议）

1. 禁止提交任何密钥、Token、私有地址。
2. 禁止硬编码本机绝对路径。
3. 所有脚本必须支持失败重试与中间结果保存。
4. 输出文件名应可配置，不覆盖原始数据。
5. 每次修改主流程时必须同步更新本 README 的“主流程”和“输入输出对应关系”。
