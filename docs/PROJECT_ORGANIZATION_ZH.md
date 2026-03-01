# 项目内容整理说明（2026-03-01）

本文档用于把当前目录下已有内容“分层理解”，方便后续投稿 ACL。

## 1. 核心论文复现目录（优先使用）

目录：`anshi_emosion_paper_release/`

该目录已包含你论文主流程所需的核心文件：

- 数据入口：`Anshi.xlsx`
- 句子拆分：`anshi.py` -> `anshi_poems.csv`
- 情感标注：`annotate.py` -> `anshi_annotated.xlsx`
- 统计分析：`anshi_count.py` -> `anshi_analysis.xlsx`
- 聚类链路：`emopoem_get.py` -> `embedding_get.py` -> `kcluster.py`
- 方法输出：
  - `appreciation_clustering_results_20.csv`
  - `all_kclusters_20_results.txt`
  - `elbow_method_plot.png`
  - `poem_kclusters_20_visualization.png`
- 中文论文稿：`安史之乱与诗人情感变迁.docx`
- 复现说明：`README_论文复现说明.md`

## 2. 根目录历史文件（保留，不强制删除）

根目录包含大量历史实验文件：

- 多轮标注文件：`rater_A.xlsx`、`rater_B.xlsx`、`va_r1.xlsx`、`va_r2.xlsx` 等
- 对比脚本：`translate.py`、`xlm_test.py`、`test_annotator.py` 等
- 中间结果：`aligned_output.jsonl`、`retry_aligned_output.jsonl` 等
- 视觉化：`summary_metrics.png`、`agreement_confusion_matrix.png`、`va_scatter_quadrant.png`
- 超大模型目录：`models/`、`xlm_roberta_large/`

这些文件不影响你投稿 ACL 的主链路，可以继续保留在仓库本地。

## 3. 本次新增投稿目录

目录：`Papers/acl_short_paper/`

包含：

- 新手版投稿执行方案（中文）：`PLAN_ZH.md`
- ACL LaTeX 草稿（英文）：`main.tex`
- 参考文献占位文件：`refs.bib`
- 使用说明：`README.md`

## 4. GitHub 化策略

为保证“可推送 + 可维护”，采用以下策略：

1. 不删除原始文件，防止破坏已有实验。
2. 使用 `.gitignore` 屏蔽超大与中间文件，避免 GitHub 推送失败。
3. 将“论文写作与投稿”集中到 `Papers/`，后续可独立迭代。

## 5. 后续建议

1. 对 `Papers/acl_short_paper/main.tex` 补充真实实验数值与图表。
2. 把 `refs.bib` 中占位引用替换成已核实文献。
3. 按 ACL 当年 CFP 更新页数、匿名、伦理说明要求后再提交。
