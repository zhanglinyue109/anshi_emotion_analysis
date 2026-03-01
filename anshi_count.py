import pandas as pd
import os

# ==============================
# 配置
# ==============================
input_file = 'anshi_annotated.xlsx'
output_file = 'anshi_analysis.xlsx'

standard_columns = [
    '单句', '全诗', '标题', '作者', '编年', '地点',
    '情感标签1', '情感标签2', '情感标签3'
]

# 一级分类映射（二级标签 → 一级类别）
secondary_to_primary = {
    # 哀
    '羁旅': '哀',
    '伤逝': '哀',
    '偃蹇': '哀',
    '悲愁': '哀',
    '忧伤': '哀',
    '思念': '哀',
    '孤寂': '哀',
    # 恶
    '讥讽': '恶',
    # 乐
    '喜悦': '乐',
    '爱恋': '乐',
    '壮思': '乐',
    '淡泊': '乐',
    '宴息': '乐',
    # 怒
    '慷慨': '怒',
    '愤恨': '怒',
    # 惧
    '惊恐': '惧',
    # 好
    '赞美': '好',
    # 惊
    '迷茫': '惊'
}

# 所有有效的一级类别（用于对齐列顺序）
primary_categories = ['哀', '恶', '乐', '怒', '惧', '好', '惊']

def map_to_primary(secondary_labels):
    """将二级标签列表转为一级标签列表"""
    primaries = []
    for label in secondary_labels:
        if label in secondary_to_primary:
            primaries.append(secondary_to_primary[label])
        else:
            # 可选：警告未知标签
            print(f"⚠️ 警告：未定义的一级映射标签 '{label}'，已跳过")
    return primaries

def main():
    if not os.path.exists(input_file):
        print(f"❌ 找不到文件: {input_file}")
        return

    df = pd.read_excel(input_file)
    print(f"✅ 读取成功：{len(df)} 行，{len(df.columns)} 列")

    if len(df.columns) < 9:
        print("❌ 列数不足9列")
        return

    df = df.iloc[:, :9]
    df.columns = standard_columns
    print("✅ 已截取前9列并重命名")

    # 提取二级情感标签
    def extract_emotions(row):
        labels = []
        for i in range(1, 4):
            val = row[f'情感标签{i}']
            if pd.notna(val) and str(val).strip() != '':
                labels.append(str(val).strip())
        return labels

    df['情感标签'] = df.apply(extract_emotions, axis=1)

    # 转换为一级标签
    df['一级情感'] = df['情感标签'].apply(map_to_primary)

    # 展开一级标签用于统计
    df_primary = df.explode('一级情感').reset_index(drop=True)
    df_primary = df_primary.dropna(subset=['一级情感'])

    # ==============================
    # 一级分类统计
    # ==============================

    # 1. 每年的一级情感比例
    year_primary = df_primary.groupby('编年')['一级情感'].value_counts().unstack(fill_value=0)
    # 确保所有7个类别都存在（即使为0）
    for cat in primary_categories:
        if cat not in year_primary.columns:
            year_primary[cat] = 0
    year_primary = year_primary[primary_categories]  # 按固定顺序排列
    year_primary_ratio = year_primary.div(year_primary.sum(axis=1), axis=0).round(4)

    # 2. 每位诗人的一级情感比例 + 诗句数量
    poet_poem_count = df['作者'].value_counts().sort_index()
    poet_primary = df_primary.groupby('作者')['一级情感'].value_counts().unstack(fill_value=0)
    for cat in primary_categories:
        if cat not in poet_primary.columns:
            poet_primary[cat] = 0
    poet_primary = poet_primary[primary_categories]
    poet_primary_ratio = poet_primary.div(poet_primary.sum(axis=1), axis=0).round(4)
    poet_primary_summary = poet_primary_ratio.copy()
    poet_primary_summary.insert(0, '诗句数量', poet_poem_count)

    # 3. 各地点的一级情感比例
    location_primary = df_primary.groupby('地点')['一级情感'].value_counts().unstack(fill_value=0)
    for cat in primary_categories:
        if cat not in location_primary.columns:
            location_primary[cat] = 0
    location_primary = location_primary[primary_categories]
    location_primary_ratio = location_primary.div(location_primary.sum(axis=1), axis=0).round(4)

    # ==============================
    # 保存结果（原有 + 新增）
    # ==============================
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 原有：二级标签
        df_exploded = df.explode('情感标签').dropna(subset=['情感标签'])
        year_sec = df_exploded.groupby('编年')['情感标签'].value_counts().unstack(fill_value=0)
        poet_sec = df_exploded.groupby('作者')['情感标签'].value_counts().unstack(fill_value=0)
        loc_sec = df_exploded.groupby('地点')['情感标签'].value_counts().unstack(fill_value=0)

        year_sec.div(year_sec.sum(axis=1), axis=0).round(4).to_excel(writer, sheet_name='每年_二级比例')
        poet_sec.div(poet_sec.sum(axis=1), axis=0).round(4).to_excel(writer, sheet_name='诗人_二级比例')
        loc_sec.div(loc_sec.sum(axis=1), axis=0).round(4).to_excel(writer, sheet_name='地点_二级比例')

        # 新增：一级分类
        year_primary_ratio.to_excel(writer, sheet_name='每年_一级比例')
        poet_primary_summary.to_excel(writer, sheet_name='诗人_一级比例_含诗句数')
        location_primary_ratio.to_excel(writer, sheet_name='地点_一级比例')

        # 频次表（可选）
        year_primary.to_excel(writer, sheet_name='每年_一级频次')
        poet_primary.to_excel(writer, sheet_name='诗人_一级频次')
        location_primary.to_excel(writer, sheet_name='地点_一级频次')

    print(f"\n🎉 分析完成！结果已保存到：{output_file}")
    print("包含二级标签和一级分类的完整统计。")

if __name__ == '__main__':
    main()