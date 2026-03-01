# 项目内容整理说明（2026-03-01）

## 1. 当前分层结构

本仓库已按“代码、数据、输出、论文、历史”拆分：

1. `scripts/`：主流程与实验脚本入口。
2. `src/`：可复用模块（如模型定义）。
3. `data/`：原始/中间/处理后数据目录（默认忽略具体数据文件）。
4. `outputs/`：图和表等结果文件。
5. `papers/acl_short_paper/`：ACL 短文方案与 LaTeX 草稿。
6. `archive/legacy/anshi_emosion_paper_release/`：旧版发布目录，保留历史对照。

## 2. 主流程脚本位置

当前建议执行顺序：

```bash
python scripts/anshi.py
python scripts/annotate.py
python scripts/anshi_count.py
python scripts/emopoem_get.py
python scripts/embedding_get.py
python scripts/kcluster.py
```

## 3. 论文相关目录

论文材料位于：

- `papers/acl_short_paper/PLAN_ZH.md`
- `papers/acl_short_paper/main.tex`
- `papers/acl_short_paper/refs.bib`

## 4. 忽略策略

`.gitignore` 已设置为：

1. 忽略大型模型与大体量数据（如 `*.npy`, `*.xlsx`, `*.jsonl`, `*.csv`）。
2. 忽略敏感文件（如 `.env*`, `*.pem`, `secrets/`）。
3. 保留 `papers/` 论文图资源可跟踪。

## 5. 后续建议

1. 将脚本中的 API Key 和绝对路径迁移到环境变量 + 配置文件。
2. 在 `scripts/` 为主流程脚本补充 CLI 参数（输入/输出可配置）。
3. 在提交 ACL 前，用真实结果替换 `papers/acl_short_paper/main.tex` 占位内容。
