import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os

# === 指定你下载的字体文件路径 ===
FONT_PATH = os.path.expanduser("～/.fonts/wqy-microhei.ttc")

# 检查字体文件是否存在
if not os.path.exists(FONT_PATH):
    raise FileNotFoundError(f"❌ 字体文件未找到: {FONT_PATH}\n"
                            "请先运行以下命令下载字体:\n"
                            "mkdir -p ～/.fonts && wget -P ～/.fonts https://github.com/lilu314/awesome-fonts/raw/master/fonts/wqy-microhei.ttc")

# 创建 FontProperties 对象（关键！）
chinese_font = font_manager.FontProperties(fname=FONT_PATH)

# === 读取数据 ===
INPUT_FILE = "va_sample100.xlsx"
df = pd.read_excel(INPUT_FILE)
df = df.dropna(subset=['Valence', 'Arousal'])

# === 绘图 ===
plt.figure(figsize=(10, 8))
plt.scatter(df['Valence'], df['Arousal'], alpha=0.7, s=50, color='#1f77b4')

# 四象限线（假设 [0,1] 范围）
plt.axhline(0.5, color='black', linestyle='--', linewidth=1)
plt.axvline(0.5, color='black', linestyle='--', linewidth=1)
plt.xlim(0, 1)
plt.ylim(0, 1)

# 使用字体文件绘制中文（必须用 fontproperties=...）
def add_text(x, y, text):
    plt.text(x, y, text, ha='center', fontsize=10, fontproperties=chinese_font)

add_text(0.75, 0.9, '高愉悦 / 高唤醒\n(兴奋、喜悦)')
add_text(0.25, 0.9, '低愉悦 / 高唤醒\n(愤怒、焦虑)')
add_text(0.25, 0.1, '低愉悦 / 低唤醒\n(悲伤、疲倦)')
add_text(0.75, 0.1, '高愉悦 / 低唤醒\n(平静、满足)')

# 标题和坐标轴标签也用该字体
plt.title('情感四象限分布图（Valence-Arousal 模型）', fontsize=14, fontproperties=chinese_font)
plt.xlabel('愉悦度 Valence (0=负面 → 1=正面)', fontsize=12, fontproperties=chinese_font)
plt.ylabel('唤醒度 Arousal (0=平静 → 1=激动)', fontsize=12, fontproperties=chinese_font)

plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig("va_scatter_quadrant_zh.png", dpi=300, bbox_inches='tight')
print("✅ 中文四象限图已保存为: va_scatter_quadrant_zh.png")

plt.close()