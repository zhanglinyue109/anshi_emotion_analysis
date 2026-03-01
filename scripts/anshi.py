import pandas as pd
import re

# 读取Excel文件
input_file = 'Anshi.xlsx'
df = pd.read_excel(input_file)

# 创建结果列表（比反复 append DataFrame 更高效）
result_rows = []

# 遍历每一行
for idx, row in df.iterrows():
    # 提取所需列（pandas 默认列索引从0开始）
    title = row.iloc[3]      # 原第4列（1-based）→ iloc[3]
    raw_poem = str(row.iloc[5])   # 原第6列 → 全诗
    year_num = row.iloc[8]   # 原第9列 → 编年（数字）
    location = row.iloc[9]   # 原第10列 → 地点
    author = row.iloc[12]    # 原第13列 → 作者

    # 清洗：删除所有 ｛...｝ 内容（全角花括号）
    cleaned_poem = re.sub(r'｛[^｝]*｝', '', raw_poem)
    
    # 按中文句号分割，并清理每句
    sentences = [s.strip() for s in cleaned_poem.split('。') if s.strip()]
    
    
    # 为每个句子生成一行
    for sent in sentences:
        result_rows.append({
            '单句': sent,
            '全诗': cleaned_poem,
            '标题': title,
            '作者': author,
            '编年': year_num,
            '地点': location
        })

# 转为DataFrame并保存
result_df = pd.DataFrame(result_rows, columns=['单句', '全诗', '标题', '作者', '编年', '地点'])
output_file = 'anshi_poems.csv'
result_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"处理完成！共 {len(result_rows)} 行，已保存至 {output_file}")