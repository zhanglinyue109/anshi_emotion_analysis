import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================
# 🔧 配置区：只需修改这一行！
# ==============================
xlsx_file = "/home/kongcunliang/zhanglinyue/tang_jscd/appreciation_poem/random200_2annotator.xlsx"  # ←←← 替换为你的 Excel 文件路径！

# 列索引（第11列 = index 10，第12列 = index 11）
col_A_idx = 10
col_B_idx = 11

# ==============================
# 1. 读取数据
# ==============================
print("Reading Excel file...")
df = pd.read_excel(xlsx_file, header=0)

if len(df) != 200:
    print(f"⚠️ Warning: Found {len(df)} rows, expected 200.")

ann_col_A = df.iloc[:, col_A_idx]
ann_col_B = df.iloc[:, col_B_idx]

# ==============================
# 2. 数据转换：空 → 1（正确），0 → 0（错误）
# ==============================
def to_binary(series):
    s = pd.to_numeric(series, errors='coerce')  # 非数字转 NaN
    return s.fillna(1).astype(int)  # NaN（即空）→ 1

ann_A = to_binary(ann_col_A)
ann_B = to_binary(ann_col_B)

# ==============================
# 3. 统计计算
# ==============================
N_A_correct = (ann_A == 1).sum()
N_B_correct = (ann_B == 1).sum()

both_correct = ((ann_A == 1) & (ann_B == 1)).sum()
both_incorrect = ((ann_A == 0) & (ann_B == 0)).sum()
A_correct_B_incorrect = ((ann_A == 1) & (ann_B == 0)).sum()
A_incorrect_B_correct = ((ann_A == 0) & (ann_B == 1)).sum()

agree_total = both_correct + both_incorrect
disagree_total = A_correct_B_incorrect + A_incorrect_B_correct

observed_agreement = agree_total / len(df)
kappa = cohen_kappa_score(ann_A, ann_B)

strict_accuracy = both_correct / len(df)
lenient_accuracy = (both_correct + A_correct_B_incorrect + A_incorrect_B_correct) / len(df)

# ==============================
# 4. 打印文本报告
# ==============================
print("\n=== Inter-Annotator Agreement Report ===")
print(f"Total samples: {len(df)}")
print(f"Annotator A correct: {N_A_correct}")
print(f"Annotator B correct: {N_B_correct}")
print(f"\nAgreements: {agree_total} ({agree_total/len(df):.1%})")
print(f"  - Both correct: {both_correct}")
print(f"  - Both incorrect: {both_incorrect}")
print(f"Disagreements: {disagree_total} ({disagree_total/len(df):.1%})")
print(f"\nObserved Agreement: {observed_agreement:.4f}")
print(f"Cohen's Kappa: {kappa:.4f}")
print(f"\nEstimated Model Accuracy:")
print(f"  - Strict (both agree correct): {strict_accuracy:.2%}")
print(f"  - Lenient (at least one correct): {lenient_accuracy:.2%}")

# ==============================
# 5. 可视化（全英文）
# ==============================
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# --- 图1: Confusion Matrix ---
conf_matrix = pd.crosstab(
    ann_A.replace({1: 'Correct', 0: 'Incorrect'}),
    ann_B.replace({1: 'Correct', 0: 'Incorrect'}),
    rownames=['Annotator A'],
    colnames=['Annotator B']
)

plt.figure(figsize=(6, 5))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', cbar=True)
plt.title('Inter-Annotator Agreement Confusion Matrix')
plt.tight_layout()
plt.savefig('agreement_confusion_matrix.png', dpi=300, bbox_inches='tight')
plt.show()

# --- 图2: Judgment Distribution ---
labels = ['Correct', 'Incorrect']
counts_A = [N_A_correct, len(df) - N_A_correct]
counts_B = [N_B_correct, len(df) - N_B_correct]

x = np.arange(len(labels))
width = 0.35

plt.figure(figsize=(6, 5))
plt.bar(x - width/2, counts_A, width, label='Annotator A', alpha=0.8)
plt.bar(x + width/2, counts_B, width, label='Annotator B', alpha=0.8)
plt.xlabel('Judgment Result')
plt.ylabel('Number of Samples')
plt.title('Distribution of Judgments by Annotators')
plt.xticks(x, labels)
plt.legend()
plt.tight_layout()
plt.savefig('annotation_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

# --- 图3: Summary Text Plot ---
fig, ax = plt.subplots(figsize=(8, 4))
ax.axis('off')

textstr = f'''\
Total Samples: {len(df)}

Observed Agreement (P₀): {observed_agreement:.2%}
Cohen's Kappa (κ): {kappa:.3f}

Agreements: {agree_total} ({agree_total/len(df):.1%})
- Both Correct: {both_correct}
- Both Incorrect: {both_incorrect}

Disagreements: {disagree_total} ({disagree_total/len(df):.1%})

Estimated Model Accuracy:
- Strict Strategy: {strict_accuracy:.2%}
- Lenient Strategy: {lenient_accuracy:.2%}
'''

props = dict(boxstyle='round', facecolor='lightblue', alpha=0.5)
ax.text(0.1, 0.95, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props, family='monospace')

plt.title('Summary of Agreement and Model Performance', fontsize=14, pad=20)
plt.tight_layout()
plt.savefig('summary_metrics.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n✅ Analysis complete!")