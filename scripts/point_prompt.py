import openai
import pandas as pd
import json
from tqdm import tqdm
import time

# 配置 API
API_KEY = "[REDACTED_API_KEY_1]"
BASE_URL = "http://43.163.86.62:3000/v1"
MODEL = "deepseek-v3"

client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)


EMOTION_CATEGORIES = """
一级类“哀”：
  二级类：行旅、衰老、不遇、悲苦、愁苦、思人、劳苦、思乡、孤寂
一级类“恶”：
  二级类：讥讽
一级类“乐”：
  二级类：喜悦、恩爱、快意、淡泊、宴乐
一级类“怒”：
  二级类：慷慨、愤恨
一级类“惧”：
  二级类：惊恐
一级类“好”：
  二级类：友情
一级类“惊”：
  二级类：迷茫
特殊类：NULL（无法归类）

情感极性评分标准（1-5）：
1: 情绪极弱或无情绪，仅陈述事实或轻微流露
2: 情绪初现，温和含蓄
3: 情绪明确，具感染力
4: 情绪饱满，令人动容
5: 情绪强烈，具心灵冲击力

请严格根据以下规则判断：
- 先判断属于哪个一级类，再选最匹配的二级类（若为NULL则二级类留空）
- 若不属于任何类，选“NULL”，此时无需二级类
- 情感极性打分必须为1~5之间的整数
"""

def annotate_poem_line(poem_line):
    """对单句诗句进行情感标注"""
    prompt = f"""
你是一个精通中国古典诗词情感分析的专家。请根据提供的《古诗情感标注规范》，对以下诗句进行精确分类和打分。

## 诗句：
"{poem_line}"

## 标注规范摘要：
{EMOTION_CATEGORIES}

## 任务要求：
1. 判断该诗句最符合的一级情感类别（只能选一个）。
2. 若非NULL，则选择最匹配的二级情感类别（只能选一个）。
3. 给出情感极性评分（1-5的整数）。
4. 若完全不符合任何类别，请将一级类设为"NULL"，二级类为空字符串。

## 输出格式（严格使用以下 JSON 格式，不要添加任何其他内容）：
{{
  "一级情感": "哀",
  "二级情感": "思乡",
  "情感层级（1-5）": 4
}}

或当无法归类时：
{{
  "一级情感": "NULL",
  "二级情感": "",
  "情感层级（1-5）": 1
}}

注意：
- 评分必须结合语言强度、意象密度、情感浓度综合判断
- 不要输出任何解释、说明或额外文本
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # 降低随机性
            )
            content = response.choices[0].message.content.strip()

            # 清理可能的 Markdown 代码块标记
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
            if content.endswith("```"):
                content = content.rsplit("\n", 1)[0]

            result = json.loads(content)

            # 验证字段
            if ("一级情感" not in result or
                "二级情感" not in result or
                "情感层级（1-5）" not in result):
                raise ValueError("缺失必要字段")

            # 类型检查
            if not isinstance(result["情感层级（1-5）"], int) or not (1 <= result["情感层级（1-5）"] <= 5):
                raise ValueError("情感层级必须是1-5的整数")

            return result

        except Exception as e:
            print(f"  [尝试 {attempt+1}/{max_retries}] 错误: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)  # 简单重试延迟
            else:
                print(f"  ✗ 处理失败: {poem_line}")
                return {"一级情感": "NULL", "二级情感": "", "情感层级（1-5）": 1}
    return {"一级情感": "NULL", "二级情感": "", "情感层级（1-5）": 1}


def process_excel_file(input_excel, output_excel):
    """
    读取 Excel 文件，对第一列诗句进行情感标注，并写回第7~9列
    """
    # 读取 Excel
    df = pd.read_excel(input_excel, header=0)

    # 确保有至少一列
    if df.shape[1] < 1:
        raise ValueError("输入文件至少需要一列诗句")

    # 扩展列数到至少9列
    for i in range(df.shape[1], 9):
        df[f"列{i+1}"] = ""

    # 设置表头（如果原表头不对）
    headers = list(df.columns)
    headers[6] = "一级情感"
    headers[7] = "二级情感"
    headers[8] = "情感层级（1-5）"
    df.columns = headers

    # tqdm 支持 pandas
    tqdm.pandas(desc="处理诗句")

    print("开始批量处理...")

    # 逐行处理第一列诗句
    def process_row(row):
        poem = str(row.iloc[0]).strip()
        if not poem or poem == "nan":
            row.iloc[6] = "NULL"
            row.iloc[7] = ""
            row.iloc[8] = 1
            return row

        result = annotate_poem_line(poem)
        row.iloc[6] = result["一级情感"]
        row.iloc[7] = result["二级情感"]
        row.iloc[8] = result["情感层级（1-5）"]
        return row

    # 应用处理（带进度条）
    df = df.progress_apply(process_row, axis=1)

    # 保存结果
    df.to_excel(output_excel, index=False)
    print(f"✅ 处理完成，结果已保存至: {output_excel}")


if __name__ == "__main__":
    INPUT_FILE = "shiju.xlsx"      # 输入：Excel，第一列为诗句
    OUTPUT_FILE = "shiju_annotated.xlsx"  # 输出：带标注的新 Excel

    process_excel_file(INPUT_FILE, OUTPUT_FILE)