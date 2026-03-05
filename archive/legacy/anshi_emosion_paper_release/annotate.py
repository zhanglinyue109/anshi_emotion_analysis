import openai
import pandas as pd
import json
import re
from tqdm import tqdm
import time
import os

# ======================
# 配置区（按需修改）
# ======================
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "http://43.163.86.62:3000/v1")
MODEL = os.getenv("MODEL", "deepseek-v3")

INPUT_FILE = "anshi_poems.csv"   # 支持 .xlsx 或 .csv
OUTPUT_FILE = "anshi_annotated.xlsx"

MAX_SECONDARY = 3  # 最多标注3个情感标签
MAX_RETRIES = 3    # 调用失败最多重试次数

# ======================
# 初始化 OpenAI 客户端
# ======================
client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ======================
# 安全解析 JSON（增强容错）
# ======================
def safe_json_loads(text):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return {"情感标签": []}

# ======================
# 构建模型提示词（略微放宽规则）
# ======================
def build_model_friendly_prompt():
    return r"""
你是一位精通中国古典诗词的情感分析专家，请为诗句标注**最多3个**最贴切的**情感标签**。

# 可选的情感标签（共18个，必须严格使用以下名称）：
羁旅、伤逝、偃蹇、悲愁、忧伤、思念、孤寂、
讥讽、
喜悦、爱恋、壮思、淡泊、宴息、
慷慨、愤恨、
惊恐、
赞美、
迷茫

# 标签定义（请严格遵守）：
- 羁旅：羁旅漂泊之苦（远行、风霜、路途艰辛）。例：“归雁来时数附书”。
- 伤逝：年华老去的悲伤，涉及黑发、白发等。例：“不堪玄鬓影”。
- 偃蹇：怀才不遇，壮志难酬。例：“无因见明主”。
- 悲愁：深重人生苦难，如亲友去世、战乱、贫穷、疾病。例：“弟兄无一人”。
- 忧伤：内心郁结，忧思难解。例：“暮天摇落伤怀抱”。
- 思念：思念恋人、故人（须在世）或故乡，且归期无望。例：“别后相思复何益”。
- 孤寂：寂寞孤单，天地独对。例：“已忍伶俜十年事”。
- 讥讽：对人或现象的讽刺、鄙夷、厌恶。例：“轻薄为文哂未休”。
- 喜悦：内心欢喜，轻松明朗。例：“却喜晒谷天晴”。
- 爱恋：夫妻或恋人之间的美好感情。例：“或恐是同乡”。
- 壮思：豪迈洒脱，人生得意。例：“冲天香阵透长安”。
- 淡泊：超然物外，不慕名利（属积极心境）。例：“悠然见南山”。
- 宴息：聚会饮酒、朋友欢聚之乐。例：“莫使金樽空对月”。
- 慷慨：悲壮激昂，忧国忧民。例：“慨然抚长剑”。
- 愤恨：强烈愤怒，痛斥不公。例：“朱门酒肉臭”。
- 惊恐：对危险、变故的害怕与焦虑。例：“恐惊平昔颜”。
- 赞美：对亲情、友情、爱情等真挚情谊的歌颂。例：“天涯若比邻”。
- 迷茫：前路不明，人生困惑（重点在“不知所措”）。例：“更欲东奔何处所”。

# ⚠️ 重要规则
1. **只输出属于上述18个标签的内容**，不得自创。
2. 若诗句为纯写景、纯记事、语义不清 → 返回空列表 `[]`。
3. **但若诗句隐含可合理推断的情绪（如“独坐”“寒雨”“孤舟”），请优先选择最贴近的1个标签，而非返回空列表。**
4. 最多标注3个标签，按相关性排序。
5. “泪”“愁”等字出现 ≠ 自动打标签，需看整体语境。
6. “独坐”“独钓”：超然 → 淡泊；孤独无助 → 孤寂。

# 输出要求
- 仅输出合法 JSON，格式：`{"情感标签": [...]}`
- 不要任何解释、注释、markdown 或额外字段。

## 示例（Few-shot）：
诗句："白日依山尽"
{"情感标签": []}

诗句："乡音无改鬓毛衰"
{"情感标签": ["思念", "伤逝"]}

诗句："莫使金樽空对月"
{"情感标签": ["宴息"]}

诗句："朱门酒肉臭，路有冻死骨"
{"情感标签": ["愤恨", "悲愁"]}

诗句："独坐幽篁里，弹琴复长啸"
{"情感标签": ["淡泊"]}
"""

# ======================
# 调用模型标注单句
# ======================
def annotate_poem_line(poem_line):
    user_prompt = f"""{build_model_friendly_prompt()}

## 请标注以下诗句：
诗句："{poem_line}"

## 输出（仅JSON）：
"""

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.0,
                max_tokens=150,
            )
            content = response.choices[0].message.content.strip()

            if content.startswith("```"):
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1].strip()
                    if content.lower().startswith("json"):
                        content = content[4:].strip()

            result = safe_json_loads(content)
            tags = result.get("情感标签", [])

            valid_tags = {
                "羁旅", "伤逝", "偃蹇", "悲愁", "忧伤", "思念", "孤寂",
                "讥讽", "喜悦", "爱恋", "壮思", "淡泊", "宴息",
                "慷慨", "愤恨", "惊恐", "赞美", "迷茫"
            }

            cleaned = []
            seen = set()
            for tag in tags:
                t = str(tag).strip()
                if t in valid_tags and t not in seen:
                    cleaned.append(t)
                    seen.add(t)
                if len(cleaned) >= MAX_SECONDARY:
                    break

            time.sleep(1.0)  # 关键限流

            if not cleaned:
                with open("debug_empty_responses.txt", "a", encoding="utf-8") as f:
                    f.write(f"诗句: {poem_line}\n模型输出: {content}\n---\n")

            return cleaned, True

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                with open("debug_failed_calls.txt", "a", encoding="utf-8") as f:
                    f.write(f"诗句: {poem_line} | 错误: {str(e)}\n")
                time.sleep(2.0)
                return [], False
            time.sleep(2.0)

    return [], False

# ======================
# 主处理函数（保留所有原始列）
# ======================
def process_excel_file(input_path, output_path, max_secondary=3):
    # 读取原始文件（自动识别格式）
    if input_path.endswith('.csv'):
        df = pd.read_csv(input_path, header=0, dtype=str)
    else:
        df = pd.read_excel(input_path, header=0, dtype=str)

    df = df.fillna("")  # 空值转为空字符串
    n = len(df)

    if n == 0:
        raise ValueError("输入文件为空")

    print(f"📄 检测到 {len(df.columns)} 列，列名: {list(df.columns)}")
    expected_cols = ["单句", "全诗", "标题", "作者", "编年", "地点"]
    if not all(col in df.columns for col in expected_cols):
        print("⚠️ 警告：列名不完全匹配预期，但仍将继续处理。")

    # 确保“单句”列存在
    if "单句" not in df.columns:
        raise KeyError("输入文件必须包含 '单句' 列作为标注依据")

    # 添加新列（初始化为空）
    for i in range(1, max_secondary + 1):
        df[f"情感标签{i}"] = ""
    df["调用成功"] = ""

    # 确保所有新增列为 object 类型（避免 pandas 警告）
    new_cols = [f"情感标签{i}" for i in range(1, max_secondary + 1)] + ["调用成功"]
    for col in new_cols:
        df[col] = df[col].astype(object)

    # 断点续传：检查已有输出
    start_idx = 0
    if os.path.exists(output_path):
        try:
            existing_df = pd.read_excel(output_path) if output_path.endswith('.xlsx') else pd.read_csv(output_path, dtype=str)
            if len(existing_df) == n and set(df.columns).issubset(set(existing_df.columns)):
                success_series = existing_df.get("调用成功", pd.Series(["否"] * n))
                if (success_series == "是").all():
                    print("✅ 所有行已处理完毕。")
                    return
                else:
                    start_idx = (success_series != "是").idxmax()
                    print(f"🔁 从第 {start_idx + 1} 行继续处理...")
                    # 合并已有结果
                    for col in new_cols:
                        if col in existing_df.columns:
                            df[col] = existing_df[col].fillna("").astype(object)
        except Exception as e:
            print(f"⚠️ 无法加载已有结果，重新开始: {e}")

    print(f"🚀 开始处理 {n - start_idx} / {n} 行...")

    for idx in tqdm(range(start_idx, n), desc="🔄 处理进度", initial=start_idx, total=n):
        poem = str(df.iloc[idx]["单句"]).strip()
        if not poem or poem.lower() in ("nan", "none", "", "null"):
            df.at[idx, "调用成功"] = "是"
        else:
            tags, success = annotate_poem_line(poem)
            df.at[idx, "调用成功"] = "是" if success else "否"
            for i in range(max_secondary):
                df.at[idx, f"情感标签{i+1}"] = tags[i] if i < len(tags) else ""

        # 每50行保存一次，防止崩溃丢失
        if (idx + 1) % 50 == 0 or idx == n - 1:
            if output_path.endswith('.csv'):
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
            else:
                df.to_excel(output_path, index=False, engine='openpyxl')

    # 最终保存
    if output_path.endswith('.csv'):
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
    else:
        df.to_excel(output_path, index=False, engine='openpyxl')

    print(f"\n✅ 处理完成！结果已保存至: {os.path.abspath(output_path)}")

    # 统计
    all_tags = []
    for i in range(1, max_secondary + 1):
        all_tags.extend(df[f"情感标签{i}"].dropna().tolist())
    all_tags = [t for t in all_tags if str(t).strip()]

    from collections import Counter
    print("\n📊 情感标签分布:")
    if all_tags:
        for tag, count in Counter(all_tags).most_common():
            print(f"  {tag}: {count}")
    else:
        print("  无有效标签")

    print("\n🔍 调用成功统计:")
    print(df["调用成功"].value_counts(dropna=False))


if __name__ == "__main__":
    process_excel_file(INPUT_FILE, OUTPUT_FILE, max_secondary=MAX_SECONDARY)
