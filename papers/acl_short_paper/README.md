# ACL Short Paper Package

本目录是你当前项目的 ACL 4 页短文投稿骨架。

## 文件说明

- `PLAN_ZH.md`：给新手的完整执行方案（中文）。
- `ACL2026_REQUIREMENTS_AND_GAP_PLAN_20260301.md`：ACL 2026 官方要求、缺口识别与补全计划。
- `main.tex`：英文 LaTeX 草稿（ACL 风格）。
- `refs.bib`：参考文献占位（必须人工核实后替换）。
- `figures/`：建议放论文用图（可选）。
- `.latexmkrc`：本地编译配置，统一把中间文件输出到 `build/`。
- `build_local.sh`：本地一键编译脚本（自动检查依赖和 ACL 样式文件）。
- `Makefile`：`make pdf` / `make clean` 快速命令。

## 使用方式

1. 用 `PLAN_ZH.md` 先确定“问题-方法-结果-贡献”。
2. 把真实实验结果填入 `main.tex`（表格、指标、误差分析）。
3. 替换 `refs.bib` 中所有 `PLACEHOLDER_*` 条目。
4. 使用 ACL 官方模板文件（`acl.sty`, `acl_natbib.bst`）编译。

## 对比实验数据（用于增强严谨性）

主任务对比实验基于 18 类多标签设置，结果文件：

- `outputs/tables/multilabel_baselines_18.json`

生成命令：

```bash
python scripts/run_multilabel_baselines.py
python scripts/run_api_word_stability.py
```

## 编译示例

```bash
cd papers/acl_short_paper
make pdf
```

编译成功后 PDF 在：

```bash
papers/acl_short_paper/build/main.pdf
```

如果本机还没安装 LaTeX，可先安装（macOS）：

```bash
brew install --cask mactex-no-gui
```

如果你本地缺少 ACL 样式文件，请从 ACL 官方模板下载后放到本目录（与 `main.tex` 同级）：

- `acl.sty`
- `acl_natbib.bst`
