# ACL 投稿完整方案（新手可执行）

目标：把你现有中文论文工作，转成 ACL 风格约 4 页英文短文，并具备可复现性与可提交性。

## 0. 你当前的优势

你已经有完整主链路：

1. 数据清洗与句子切分：`anshi.py`
2. 情感标注：`annotate.py`
3. 分析统计：`anshi_count.py`
4. 聚类分析：`emopoem_get.py` + `embedding_get.py` + `kcluster.py`

这意味着你不是“从零开始”，而是“从中文稿升级为 ACL 稿”。

## 1. 先定论文类型与主张（一句话）

建议按 ACL Short Paper 思路写成：

- 任务：古典汉语诗歌情感演化分析（以安史之乱为时间窗口）
- 方法：规则/LLM 标注 + 嵌入 + 聚类 + 年代/作者/地点统计
- 贡献：
  - 提出一个可复现的古诗情感分析流程
  - 展示历史事件前后情感结构变化
  - 给出可解释的聚类与统计结果

一句话主张模板：

> We present a reproducible pipeline for tracking emotion shifts in Classical Chinese poetry around the An Lushan Rebellion, combining sentence-level annotation, embedding-based clustering, and temporal-authorial analysis.

## 2. 4 页结构分配（建议）

1. Abstract（0.2 页）
2. Introduction（0.8 页）
3. Task/Data/Method（1.2 页）
4. Experiments and Results（1.2 页）
5. Discussion + Limitations + Ethics（0.4 页）
6. Conclusion（0.2 页）

参考文献通常不计入正文页数（以当年 CFP 为准）。

## 3. 从中文稿到英文稿的映射

把你中文论文里的内容映射为下面四类：

1. 必保留
- 研究问题和历史背景
- 数据来源与清洗规则
- 标注流程和一致性分析
- 核心实验结果和图表

2. 要压缩
- 长段背景综述
- 细枝末节的实现描述

3. 要新增
- ACL 风格贡献点（bullet list）
- Limitations 小节
- Ethics Statement（简短）

4. 要删除
- 与主结论弱相关的支线实验
- 对投稿目标不关键的长附录内容

## 4. 实操步骤（按顺序）

1. 固化实验表格
- 至少准备 2 张表：
  - 主结果表（情感分布/变化）
  - 标注质量表（如一致性指标）

2. 固化图
- 选择 1-2 张最解释结论的图放正文，其他放附录或仓库。

3. 写英文初稿
- 直接在 `main.tex` 中替换占位结果、数字与图注。

4. 做语言与术语统一
- 统一 “appreciation text / emotional sentence / poet-year-location” 等术语。

5. 匿名与合规检查
- 删除可识别作者身份的信息（双盲时）。
- 检查数据许可与 API 使用说明。

6. 最后提交包检查
- PDF 可编译
- 引用可解析
- 页数、格式、匿名、伦理声明均满足 ACL 当年要求

## 5. 结果最小可交付标准（你可以先做到这个）

1. 一篇 4 页英文 PDF（结构完整）
2. 一个可运行的复现说明（脚本顺序 + 输入输出）
3. 一个公开仓库（本仓库）含：
- `README.md`
- `docs/PROJECT_ORGANIZATION_ZH.md`
- `papers/acl_short_paper/`

## 6. 常见错误（新手高频）

1. 只讲背景，不给可验证结果数字。
2. 引用不核实，BibTeX 条目错误。
3. 图很多但无法支撑主结论。
4. 没写限制与伦理，导致评审扣分。

## 7. 你下一步只要做三件事

1. 把真实结果数值填进 `main.tex` 的表格占位。
2. 把 `refs.bib` 占位引用替换为真实且核实过的文献。
3. 编译并进行一次全文英文润色。
