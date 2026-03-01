# ACL 2026 投稿要求与补全方案（2026-03-01）

> 说明：当前环境无法直接访问微信域名 `mp.weixin.qq.com`，本方案基于 ACL 2026 与 ARR 官方页面整理。

## 1. 官方投稿要求（ACL 2026 主会）

## 1.1 投稿入口与机制

1. ACL 2026 采用 ARR（ACL Rolling Review）机制投稿，不是传统“一次性截止”。
2. 论文通过 ARR 提交与评审，然后在 ACL 2026 commitment 阶段选择投向 ACL 2026（Main / Findings）。

## 1.2 关键格式要求（与你当前目标直接相关）

1. Short paper 正文上限 4 页（不含 references 与 limitations）。
2. 双盲匿名评审（作者信息、致谢、可识别身份内容需移除）。
3. 论文需选择 ARR area chairs 的 area 与 contribution types。
4. 需要在 OpenReview 平台完成提交与后续 commitment。

## 1.3 关键日期（AoE）

来自 ACL 2026 官方 CFP：

1. ARR submission deadline（用于 ACL 2026）：2026-01-05
2. ARR reviews + meta-reviews released：2026-03-10
3. Commitment deadline（ACL 2026）：2026-03-14

来自 ARR Dates & Venues（通用周期）：

1. 2026 January cycle submission：2026-01-12
2. 2026 January cycle notification：2026-04-02
3. 2026 May cycle submission：2026-05-11
4. EMNLP 2026 commitment deadline：2026-07-21

结论：若你没有在可用于 ACL 2026 的 ARR 窗口提交并获得可 commitment 的评审结果，则无法走 ACL 2026 主会这轮 commitment。

## 2. 你当前仓库与论文状态（现状评估）

## 2.1 已完成

1. 仓库结构已整理（`scripts/`、`src/`、`papers/`、`archive/`）。
2. 已有 ACL short LaTeX 草稿：
   - `papers/acl_short_paper/main.tex`
3. 已有基础统计数据：
   - `papers/english_paper_v1/materials/results/paper_v1_stats.json`

## 2.2 未完成（必须补全）

1. 论文正文仍有占位项：
   - `main.tex` 中 `TODO` 数字未填。
2. 引用仍为占位：
   - `refs.bib` 是 `PLACEHOLDER_*`，当前不可投稿。
3. 图表仍是占位框：
   - `main.tex` Figure 位置还没有真实图。
4. 代码复现还不达标：
   - 多个脚本含绝对路径（`/home/...`）。
   - 多个脚本含明文 API Key（高风险，且不适合开源投稿仓库）。
   - `kcluster.py` 存在交互式 `input()`，不利于一键复现。
5. 论文与代码之间的“可复现映射”不完整：
   - 缺固定命令、固定输入输出、固定环境版本说明。
6. 研究规范补充不充分：
   - 需完整的 Limitations/ethics 与数据许可说明（当前仅有简版叙述）。

## 3. 结合你现有工作的补全方案（按优先级）

## P0（本周内，必须完成）

1. 填完 `main.tex` 的核心数字（先用 `paper_v1_stats.json` 可核验数据）。
2. 替换全部 `PLACEHOLDER` 引用为真实文献（逐条核验）。
3. 生成 1 张主结果图 + 1 张补充图，放入 `papers/acl_short_paper/figures/` 并在文中引用。
4. 清理仓库中明文密钥，改为 `.env` + `os.getenv()`。
5. 把主链路脚本改为非交互式（参数化输入输出）。

## P1（1-2 周）

1. 增加可复现入口：`run_pipeline.sh` 或 `Makefile`。
2. 固化实验环境：锁定 `requirements.txt` 版本。
3. 补全误差分析与案例分析段落（至少 1 张表 + 3 个案例）。
4. 加入数据与许可证说明（能公开什么、不能公开什么、替代获取方式）。

## P2（投稿前）

1. 双盲排查（作者名、机构名、路径名、致谢、内部链接）。
2. PDF 终检（页数、模板、引用、图表清晰度、匿名）。
3. OpenReview 提交流程彩排（信息完整性 + 上传检查）。

## 4. 立刻执行的分支决策

## 分支 A：你已有 ARR 可 commitment 的评审结果

1. 目标：赶 `2026-03-14` ACL 2026 commitment。
2. 优先：P0 全部完成，然后直接做 commitment。

## 分支 B：你没有可 commitment 的 ARR 结果（更常见）

1. 结论：ACL 2026 这一轮主会无法赶上。
2. 建议：立刻按 P0/P1 提升论文质量，转投下一 ARR 周期并瞄准 EMNLP 2026。

## 5. 你现在最应该做的 3 件事

1. 确认你是否已有 ARR 评审结果可在 2026-03-14 前 commitment。
2. 用 `paper_v1_stats.json` 先把 `main.tex` 的 TODO 数字填完。
3. 先做“密钥清理 + 路径参数化”，把复现链路变成可审稿可开源状态。

## 6. 官方来源（请以官方为准）

1. ACL 2026 CFP: https://2026.aclweb.org/calls/main_conference_papers/
2. ACL 2026 submission policy: https://2026.aclweb.org/calls/submission_policy/
3. ARR CFP: https://aclrollingreview.org/cfp
4. ARR Dates & Venues: https://aclrollingreview.org/dates
