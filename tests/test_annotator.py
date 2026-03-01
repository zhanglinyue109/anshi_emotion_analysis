import pandas as pd
import krippendorff
import numpy as np

# === 配置 ===
raterA_file = "rater_A.xlsx"
raterB_file = "rater_B.xlsx"

# === 1. 读取数据 ===
print("正在读取数据...")
dfA = pd.read_excel(raterA_file)
dfB = pd.read_excel(raterB_file)

# 检查行数是否一致
assert len(dfA) == len(dfB) == 20, "两个评分表行数不一致！"
# 假设有一列 '单句' 用于对齐，如果不存在可以注释掉下面这行
if '单句' in dfA.columns:
    assert (dfA['单句'].values == dfB['单句'].values).all(), "诗句顺序不一致！"

# === 2. 计算 Krippendorff's Alpha (原有代码保持不变) ===
# 提取评分用于一致性检验
semantic_A = pd.concat([dfA['语义忠实度1'], dfA['语义忠实度2']], ignore_index=True)
semantic_B = pd.concat([dfB['语义忠实度1'], dfB['语义忠实度2']], ignore_index=True)
emotional_A = pd.concat([dfA['情感表现度1'], dfA['情感表现度2']], ignore_index=True)
emotional_B = pd.concat([dfB['情感表现度1'], dfB['情感表现度2']], ignore_index=True)

alpha_semantic = krippendorff.alpha(reliability_data=[semantic_A.values, semantic_B.values], level_of_measurement='ordinal')
alpha_emotional = krippendorff.alpha(reliability_data=[emotional_A.values, emotional_B.values], level_of_measurement='ordinal')

# === 3. 统计分析：计算平均分与胜出率 (新增部分) ===

# --- A. 准备数据 ---
# 1 代表 Group A (有语境), 2 代表 Group B (无语境)

# 合并两个评分者的数据以便计算平均值
# 语义 (IC)
groupA_ic_all = pd.concat([dfA['语义忠实度1'], dfB['语义忠实度1']])
groupB_ic_all = pd.concat([dfA['语义忠实度2'], dfB['语义忠实度2']])

# 情感 (EA)
groupA_ea_all = pd.concat([dfA['情感表现度1'], dfB['情感表现度1']])
groupB_ea_all = pd.concat([dfA['情感表现度2'], dfB['情感表现度2']])

# --- B. 计算平均分 ---
mean_ic_A = groupA_ic_all.mean()
mean_ea_A = groupA_ea_all.mean()

mean_ic_B = groupB_ic_all.mean()
mean_ea_B = groupB_ea_all.mean()

# --- C. 计算胜出率 (Head-to-Head Comparison) ---
# 逻辑：针对每一句诗，计算两位评分者的平均总分（语义+情感），分数高者胜
# 计算每句诗 Group A 的平均总分
score_A_per_poem = (dfA['语义忠实度1'] + dfA['情感表现度1'] + 
                    dfB['语义忠实度1'] + dfB['情感表现度1']) / 4

# 计算每句诗 Group B 的平均总分
score_B_per_poem = (dfA['语义忠实度2'] + dfA['情感表现度2'] + 
                    dfB['语义忠实度2'] + dfB['情感表现度2']) / 4

# 比较
wins_A = (score_A_per_poem > score_B_per_poem).sum()
wins_B = (score_B_per_poem > score_A_per_poem).sum()
ties = len(dfA) - wins_A - wins_B  # 平局数量

win_rate_A = (wins_A / len(dfA)) * 100
win_rate_B = (wins_B / len(dfA)) * 100

# === 4. 输出结果 ===

print("\n" + "=" * 50)
print("PART 1: 评分者一致性分析 (Krippendorff's Alpha)")
print("=" * 50)
def interpret_alpha(alpha):
    if alpha >= 0.80: return "良好"
    elif alpha >= 0.67: return "可接受"
    else: return "较低"

print(f"语义忠实度 (IC): {alpha_semantic:.3f} ({interpret_alpha(alpha_semantic)})")
print(f"情感准确度 (EA): {alpha_emotional:.3f} ({interpret_alpha(alpha_emotional)})")


print("\n" + "=" * 50)
print("PART 2: 翻译质量对比评估表 (用于填入实验报告)")
print("=" * 50)

# 创建并打印 DataFrame 表格
results_data = {
    "组别": ["Group A (有语境)", "Group B (无语境)"],
    "平均信息完整度 (IC)": [f"{mean_ic_A:.2f}", f"{mean_ic_B:.2f}"],
    "平均情感准确度 (EA)": [f"{mean_ea_A:.2f}", f"{mean_ea_B:.2f}"],
    "胜出率 (Win Rate)": [f"{win_rate_A:.1f}%", f"{win_rate_B:.1f}%"]
}

df_results = pd.DataFrame(results_data)
print(df_results.to_markdown(index=False)) # 需要 tabulate 库，如果没有安装，pandas 会默认输出简单文本表格

print("\n[注]: 胜出率基于单句诗的(IC+EA)综合总分进行两两比较 (N=20)。")
print(f"其中平局数量: {ties} (未计入胜出率)")