# 论文复现说明（安史之乱与诗人情感变迁）

本目录用于论文提交，聚焦主流程文件，剔除中间尝试项目。

## 一、主流程总览

1. 原始数据整理（安史样本）
   - 输入：`Anshi.xlsx`
   - 脚本：`anshi.py`
   - 输出：`anshi_poems.csv`

2. 最终情感标签标注（论文最终使用）
   - 输入：`anshi_poems.csv`
   - 脚本：`annotate.py`
   - 输出：`anshi_annotated.xlsx`

3. 统计分析（年度/诗人/地点）
   - 输入：`anshi_annotated.xlsx`
   - 脚本：`anshi_count.py`
   - 输出：`anshi_analysis.xlsx`

4. 情感句提取与聚类方法链路（方法部分）
   - 输入：`appreciation.jsonl`
   - 脚本：`emopoem_get.py`
   - 输出：`emo_poems.txt`（或中间 JSONL 后转 TXT）
   - 脚本：`embedding_get.py`
   - 输出：`appreciation_embeddings.npy`
   - 脚本：`kcluster.py`
   - 输出：
     - `appreciation_clustering_results_20.csv`
     - `all_kclusters_20_results.txt`
     - `elbow_method_plot.png`
     - `poem_kclusters_20_visualization.png`

## 二、建议复现顺序

```bash
python anshi.py
python annotate.py
python anshi_count.py

python emopoem_get.py
python embedding_get.py
python kcluster.py
```

## 三、论文正文

- `安史之乱与诗人情感变迁.docx`

## 四、注意事项

- `annotate.py`、`emopoem_get.py` 依赖 API 调用，请先配置可用的 `API_KEY / BASE_URL / MODEL`。
- `embedding_get.py`、`kcluster.py` 中可能包含旧的绝对路径（历史环境路径），如需跨机器复现请改为当前相对路径。
- 论文最终使用的情感标签文件为：`anshi_annotated.xlsx`。
