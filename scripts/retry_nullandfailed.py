# retry_null_and_failed.py

import openai
import pandas as pd
import json
from tqdm import tqdm
import time
try:
    from api_config import get_api_config, normalize_openai_base_url
except ModuleNotFoundError:
    from scripts.api_config import get_api_config, normalize_openai_base_url

# ======================
# 配置 API（请确认密钥和模型正确）
# ======================
API_KEY, BASE_URL, MODEL = get_api_config()

client = openai.OpenAI(api_key=API_KEY, base_url=normalize_openai_base_url(BASE_URL))

MAX_SECONDARY = 3


def build_model_friendly_prompt():
    return r"""
你是一位精通中国古典诗词的情感分析专家，必须严格按照以下分类标准对诗句进行标注。

# 情感分类标准（请逐条遵守）

## 一、一级类 “哀” —— 表达悲伤、消极的情绪
包含以下二级类：
- 羁旅：羁旅漂泊之苦（远行、风霜、路途艰辛）。典型例句：“归雁来时数附书”。
- 衰老：年华老去的悲伤，涉及对年龄的描写，如黑发、白发等。典型例句：“不堪玄鬓影”。
- 偃蹇：怀才不遇，壮志难酬。典型例句：“无因见明主”。
- 悲愁：深重的人生苦难，特指亲友去世、战乱、贫穷、疾病。典型例句：“弟兄无一人”。
- 忧伤：内心郁结，忧思难解。典型例句：“暮天摇落伤怀抱”。
- 思念：思念恋人、故人（须在世）或故乡，且归期无望。典型例句：“别后相思复何益”“谁言千里自今夕”。
- 孤寂：寂寞孤单，天地独对。典型例句：“已忍伶俜十年事”。

## 二、一级类 “恶” —— 轻蔑、讽刺、厌恶
- 讥讽：对人或现象的讽刺、鄙夷、厌恶。典型例句：“轻薄为文哂未休”。
⚠️ 注意：“恶”不是泛指“不好”，必须有明确的贬斥对象和讽刺语气。

## 三、一级类 “乐” —— 积极、愉悦的情绪
- 喜悦：内心欢喜，轻松明朗。典型例句：“却喜晒谷天晴”。
- 爱恋：夫妻或恋人、暧昧对象之间的美好感情。典型例句：“或恐是同乡”。
- 快意：豪迈洒脱，人生得意。典型例句：“冲天香阵透长安”。
- 淡泊：超然物外，不慕名利（属积极心境）。典型例句：“悠然见南山”。
- 宴息：聚会饮酒、朋友欢聚之乐。典型例句：“莫使金樽空对月”。
✅ 区分：“淡泊”虽平静，但属“乐”；若强调孤独无助，则属“哀-孤寂”。

## 四、一级类 “怒” —— 激昂、愤慨的情绪
- 慷慨：悲壮激昂，忧国忧民。典型例句：“慨然抚长剑”。
- 愤恨：强烈愤怒，痛斥不公。典型例句：“朱门酒肉臭”。
✅ 区分：“慷慨”常带悲悯，“愤恨”更具攻击性。

## 五、一级类 “惧” —— 恐惧、不安
- 惊恐：对危险、变故的害怕与焦虑。典型例句：“恐惊平昔颜”。

## 六、一级类 “好” —— 正向人际情感
- 赞美：对亲情、友情、爱情等真挚情谊的赞美、歌颂。典型例句：“天涯若比邻”。

## 七、一级类 “惊” —— 震惊、迷茫
- 迷茫：前路不明，人生困惑（重点在“不知所措”，非单纯惊讶）。典型例句：“更欲东奔何处所”。

## 八、特殊类：NULL
满足以下任一条件即判为 NULL：
1. 纯写景、纯记事、纯哲理陈述，无明显主观情绪投射。  
   → 例：“白日依山尽”“两个黄鹂鸣翠柳”。
2. 情感属于两种以上类别交叉，无法明确归类。
3. 诗句语义不完整，无法判断情绪。  
   → 例：“东风不与周郎便”（单句看不出情感）。

# ⚠️ 重要易错点判断规则（必须遵守！）
- “独坐”“独钓”类：若体现超然自得 → 乐-淡泊；若强调孤独无助 → 哀-孤寂。
- “泪”“愁”字出现 ≠ 一定是“哀”——需看整体语境（如“喜极而泣”属“乐”）。
- 豪放诗句：自信得意 → 乐-快意；忧国悲愤 → 怒-慷慨。
- 思念对象为故乡 → 仍属“哀-思念”。

# 输出要求
1. 一级情感只能是以下之一：哀、恶、乐、怒、惧、好、惊、NULL。
2. 若一级情感为 NULL，二级情感必须为空列表 []。
3. 否则，二级情感必须是对应一级类下的标签（最多3个）。
4. 仅输出合法 JSON，不要任何解释、注释或 markdown。
"""


def annotate_poem_line(poem_line):
    user_prompt = f"""{build_model_friendly_prompt()}

## 请标注以下诗句：
诗句："{poem_line}"

## 输出（仅JSON）：
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.0,
                max_tokens=200,
            )
            content = response.choices[0].message.content.strip()

            if content.startswith("```"):
                content = content.split("```")[1].strip().lstrip("json").strip()

            result = json.loads(content)

            allowed_primary = {"哀", "恶", "乐", "怒", "惧", "好", "惊", "NULL"}
            primary = result.get("一级情感", "NULL")
            if primary not in allowed_primary:
                primary = "NULL"

            secondary = []
            if primary != "NULL":
                sec_raw = result.get("二级情感", [])
                if isinstance(sec_raw, list):
                    secondary = [str(x).strip() for x in sec_raw if x][:MAX_SECONDARY]

            return {"一级情感": primary, "二级情感": secondary}, True

        except Exception as e:
            if attempt == max_retries - 1:
                return {"一级情感": "NULL", "二级情感": []}, False
            time.sleep(1.5)

    return {"一级情感": "NULL", "二级情感": []}, False


def main():
    input_file = "annotated_output.xlsx"
    output_file = "annotated_output_fixed.xlsx"

    print(f"📂 正在读取已有标注文件: {input_file}")
    df = pd.read_excel(input_file, dtype=str)  # 保持字符串，避免 NaN 变成 float

    # 确保必要列存在
    required_cols = ["诗句", "全文", "调用成功", "一级情感"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"缺少必要列: {col}")

    # 补全可能缺失的二级情感列（兼容旧格式）
    for i in range(MAX_SECONDARY):
        col_name = f"二级情感{i+1}"
        if col_name not in df.columns:
            df[col_name] = ""

    # 找出需要重试的行：调用失败 或 一级情感为 NULL
    need_retry = (df["调用成功"] == "否") | (df["一级情感"] == "NULL")
    retry_indices = df[need_retry].index.tolist()
    total = len(df)
    to_retry = len(retry_indices)

    print(f"📊 总行数: {total} | 需重试行数: {to_retry}")

    if to_retry == 0:
        print("✅ 无需重试，直接保存原文件。")
        df.to_excel(output_file, index=False)
        return

    # 开始重试
    poems = df["诗句"].fillna("").astype(str)

    for idx in tqdm(retry_indices, desc="重试中"):
        poem = poems.iloc[idx].strip()
        if not poem or poem.lower() in ("nan", "none", ""):
            df.at[idx, "调用成功"] = "是"
            df.at[idx, "一级情感"] = "NULL"
            for i in range(MAX_SECONDARY):
                df.at[idx, f"二级情感{i+1}"] = ""
        else:
            result, success = annotate_poem_line(poem)
            df.at[idx, "调用成功"] = "是" if success else "否"
            df.at[idx, "一级情感"] = result["一级情感"]
            sec_list = result["二级情感"]
            for i in range(MAX_SECONDARY):
                df.at[idx, f"二级情感{i+1}"] = sec_list[i] if i < len(sec_list) else ""

    # 保存完整结果
    df.to_excel(output_file, index=False)
    print(f"\n✅ 重试完成！完整修正版已保存至: {output_file}")

    print("\n📊 更新后的一级情感分布:")
    print(df["一级情感"].value_counts(dropna=False))
    print("\n🔍 调用成功统计:")
    print(df["调用成功"].value_counts(dropna=False))


if __name__ == "__main__":
    main()
