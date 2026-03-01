import pandas as pd

# 设置输入和输出文件路径
input_file = 'anshi_annotated.xlsx'      # 替换为你的输入文件路径
output_file = 'random200_rows.xlsx'  # 输出文件名

# 读取 Excel 文件
df = pd.read_excel(input_file)

# 检查总行数是否足够
if len(df) < 200:
    raise ValueError(f"输入文件只有 {len(df)} 行，无法抽取 200 行。")

# 随机抽取 200 行（不重复）
random_sample = df.sample(n=200, random_state=None)  # 可设置 random_state 为固定值以复现结果
# 保存到新的 Excel 文件
random_sample.to_excel(output_file, index=False)

print(f"已成功从 {input_file} 中随机抽取 200 行，并保存到 {output_file}")