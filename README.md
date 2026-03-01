# anshi_emotion_analysis

本仓库研究“安史之乱语境下唐诗情感变迁”，并已整理为更清晰的工程结构，方便复现与论文投稿。

## 目录结构

```text
anshi_emotion_analysis/
├─ README.md
├─ .gitignore
├─ requirements.txt
├─ src/                       # 可复用模型/模块
├─ scripts/                   # 主要实验脚本
├─ tests/                     # 测试与一致性检查
├─ data/
│  ├─ raw/                    # 原始数据（默认忽略）
│  ├─ interim/                # 中间数据（默认忽略）
│  └─ processed/              # 处理后数据（默认忽略）
├─ outputs/
│  ├─ figures/                # 图表输出
│  └─ tables/                 # 文本与表格输出
├─ papers/
│  └─ acl_short_paper/        # ACL 短文方案与 LaTeX 稿
├─ archive/
│  └─ legacy/                 # 历史版本（保留）
└─ docs/
```

## 主流程（当前脚本入口）

```bash
python scripts/anshi.py
python scripts/annotate.py
python scripts/anshi_count.py
python scripts/emopoem_get.py
python scripts/embedding_get.py
python scripts/kcluster.py
```

输入输出主链路：

1. `Anshi.xlsx` -> `scripts/anshi.py` -> `anshi_poems.csv`
2. `anshi_poems.csv` -> `scripts/annotate.py` -> `anshi_annotated.xlsx`
3. `anshi_annotated.xlsx` -> `scripts/anshi_count.py` -> `anshi_analysis.xlsx`
4. `appreciation.jsonl` -> `scripts/emopoem_get.py` -> `emo_poems.*`
5. `emo_poems.txt` -> `scripts/embedding_get.py` -> `appreciation_embeddings.npy`
6. `appreciation_embeddings.npy` + `emo_poems.txt` -> `scripts/kcluster.py` -> 聚类结果

## 论文目录

ACL 短文材料在：

- `papers/acl_short_paper/PLAN_ZH.md`
- `papers/acl_short_paper/main.tex`
- `papers/acl_short_paper/refs.bib`

## 历史版本

旧版集中在：

- `archive/legacy/anshi_emosion_paper_release/`

用于追溯历史结果，不建议在该目录继续开发新逻辑。

## 注意事项

1. 当前部分脚本仍含硬编码路径和明文 API 配置，建议后续改为 `.env`。
2. 大型数据和敏感文件已通过 `.gitignore` 忽略。
3. 修改主流程后，请同步更新 `README.md` 与 `docs/PROJECT_ORGANIZATION_ZH.md`。
