import pandas as pd
import numpy as np

# === 配置文件路径 (保持您提供的原始路径) ===
file_path_A = "/home/kongcunliang/zhanglinyue/tang_jscd/appreciation_poem/va_r1.xlsx"
file_path_B = "/home/kongcunliang/zhanglinyue/tang_jscd/appreciation_poem/va_r2.xlsx"

# === 0. 定义 Gwet's AC1 计算函数 ===
def gwet_ac1(y_true, y_pred):
    """
    计算二分类数据的 Gwet's AC1 系数 (解决 Kappa 悖论问题)
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    n = len(y_true)
    
    # 计算混淆矩阵 (Confusion Matrix) 0/1 二分类
    cm = np.zeros((2, 2))
    for a, b in zip(y_true, y_pred):
        cm[int(a), int(b)] += 1
        
    # 观察到的一致率 (Observed Agreement)
    pa = (cm[0, 0] + cm[1, 1]) / n
    
    # 计算随机一致率 (Chance Agreement) - Gwet's 公式
    # Pi = (该类别被A选中的概率 + 该类别被B选中的概率) / 2
    pi_0 = ((cm[0, 0] + cm[0, 1]) / n + (cm[0, 0] + cm[1, 0]) / n) / 2
    pi_1 = ((cm[1, 1] + cm[1, 0]) / n + (cm[1, 1] + cm[0, 1]) / n) / 2
    
    # 随机一致率 Pe
    pe = pi_0 * (1 - pi_0) + pi_1 * (1 - pi_1)
    
    # 避免完全一致导致分母为0的情况
    if pe == 1:
        return 1.0
        
    # AC1 公式
    ac1 = (pa - pe) / (1 - pe)
    return ac1

# === 1. 读取数据 ===
print("正在读取数据...")
try:
    dfA = pd.read_excel(file_path_A)
    dfB = pd.read_excel(file_path_B)
except FileNotFoundError:
    print(f"❌ 错误：找不到文件，请检查路径是否正确：\n{file_path_A}")
    exit()

# === 2. 数据校验 (Data Validation) ===
print("正在检查数据格式...")
cols_check = ['Valence是否合理', 'Arousal是否合理']

for col in cols_check:
    # 强制转换为整型
    dfA[col] = dfA[col].astype(int)
    dfB[col] = dfB[col].astype(int)
    
    # 检查是否包含非法数值
    unique_A = dfA[col].unique()
    unique_B = dfB[col].unique()
    if not set(unique_A).issubset({0, 1}) or not set(unique_B).issubset({0, 1}):
        print(f"⚠️ 警告: 列 '{col}' 中发现了除 0 和 1 以外的数值！请检查数据。")

# === 3. 计算一致性 (改为 Gwet's AC1) ===
ac1_valence = gwet_ac1(dfA['Valence是否合理'], dfB['Valence是否合理'])
ac1_arousal = gwet_ac1(dfA['Arousal是否合理'], dfB['Arousal是否合理'])

# === 4. 计算人工认可准确率 (Human Acceptance Rate) ===
# 计算 Valence 的认可率
acc_valence_A = dfA['Valence是否合理'].mean()
acc_valence_B = dfB['Valence是否合理'].mean()
final_acc_valence = (acc_valence_A + acc_valence_B) / 2

# 计算 Arousal 的认可率
acc_arousal_A = dfA['Arousal是否合理'].mean()
acc_arousal_B = dfB['Arousal是否合理'].mean()
final_acc_arousal = (acc_arousal_A + acc_arousal_B) / 2

# === 5. 读取模型预测分数的均值 (用于填表) ===
try:
    mean_val = dfA['Valence'].mean()
    std_val = dfA['Valence'].std()
    mean_aro = dfA['Arousal'].mean()
    std_aro = dfA['Arousal'].std()
except KeyError:
    mean_val, std_val, mean_aro, std_aro = 0, 0, 0, 0
    print("⚠️ 注意：未在表中找到 'Valence' 或 'Arousal' 数值列，统计值暂设为0。")

# === 6. 生成报告表格 ===
print("\n" + "="*60)
print("📊 实验二数据分析结果 (Using Gwet's AC1)")
print("="*60)

# 打印详细指标
print(f"1. 评分一致性 (Gwet's AC1):")
print(f"   - Valence: {ac1_valence:.3f}")
print(f"   - Arousal: {ac1_arousal:.3f}")

print(f"\n2. 模型预测准确率 (即人工认为'合理'的比例):")
print(f"   - Valence: {final_acc_valence:.1%}")
print(f"   - Arousal: {final_acc_arousal:.1%}")

# 生成 Markdown 表格
print("\n" + "-"*60)
print("表 3: XLM-RoBERTa 情感预测准确性人工校验 [可直接复制]")
print("-"*60)

table_data = {
    "维度": ["**效价 (Valence)**", "**唤醒度 (Arousal)**"],
    "平均预测分数 (Mean)": [f"{mean_val:.2f}", f"{mean_aro:.2f}"],
    "标准差 (Std)": [f"{std_val:.2f}", f"{std_aro:.2f}"],
    "人工一致性 (Gwet's AC1)": [f"{ac1_valence:.2f}", f"{ac1_arousal:.2f}"],
    "人工认可准确率 (Accuracy)": [f"**{final_acc_valence:.1%}%**", f"**{final_acc_arousal:.1%}%**"]
}

df_table = pd.DataFrame(table_data)
try:
    print(df_table.to_markdown(index=False))
except ImportError:
    print(df_table)
    print("\n(提示: 安装 tabulate 库可获得更漂亮的 Markdown 表格输出)")