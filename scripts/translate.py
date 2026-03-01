import pandas as pd
import httpx
import time
import re

# === 配置 ===
INPUT_FILE = "/home/kongcunliang/zhanglinyue/tang_jscd/appreciation_poem/anshi.xlsx"  # 输入文件
OUTPUT_FILE = "translate_all.xlsx"  # 输出文件

API_KEY = "[REDACTED_API_KEY_2]"
BASE_URL = "https://yeysai.com/v1"
MODEL = "deepseek-v3.2-thinking"

PROMPT_WITH_CONTEXT = '''“{full_poem}”是一首唐诗。请结合语境，将其中“{single_line}”这句诗翻译成白话文，要求翻译出诗句包含的情感，但若诗句本身无情感，则不必硬翻译出情感。请仅输出白话文翻译本身，不要包含任何解释、引号、序号或其他额外文字。'''


def clean_translation(text: str) :
    """清洗模型返回的翻译文本，仅保留核心白话内容"""
    if "[ERROR]" in text:
        return text

    text = text.strip().strip('"“”\'')
    text = text.split('\n')[0]  # 只取第一行

    # 移除前缀（如“翻译：”、“1. ”等），修复原正则中的笔误（\dd+ → \d+）
    text = re.sub(
        r'^(?:\d+\.\s*|翻译[：:]\s*|答[：:]\s*|白话文[：:]\s*|解释[：:]\s*|说明[：:]\s*)',
        '',
        text,
        flags=re.IGNORECASE
    )
    return text.strip()


def call_model(prompt: str, max_retries: int = 3) -> str:
    """调用大模型 API，最多重试 max_retries 次（指数退避）"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                raw_output = response.json()['choices'][0]['message']['content'].strip()
                return raw_output

        except Exception as e:
            print(f"  ⚠️ 尝试第 {attempt}/{max_retries} 次失败: {str(e)}")
            if attempt < max_retries:
                wait_time = 2 ** (attempt - 1)  # 1s, 2s, 4s...
                print(f"     等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                error_msg = f"[ERROR] 所有 {max_retries} 次调用均失败: {str(e)}"
                print(f"  ❌ 最终失败: {error_msg}")
                return error_msg


# === 主流程 ===
if __name__ == "__main__":
    # 读取数据
    df = pd.read_excel(INPUT_FILE)
    if df.shape[1] < 2:
        raise ValueError("Excel 至少需要两列：第1列为单句，第2列为全诗")

    # 数据清洗：移除空值或空白行
    original_len = len(df)
    df = df.dropna(subset=[df.columns[0], df.columns[1]])
    df = df[df.iloc[:, 0].astype(str).str.strip() != '']
    df = df[df.iloc[:, 1].astype(str).str.strip() != '']
    cleaned_len = len(df)
    print(f"原始数据 {original_len} 行 → 清洗后 {cleaned_len} 行")

    results = []

    for idx, row in df.iterrows():
        single_line = str(row.iloc[0]).strip()
        full_poem = str(row.iloc[1]).strip()

        print(f"\n[{idx + 1}/{cleaned_len}] 处理单句: {single_line}")

        # 仅使用带上下文的 prompt
        prompt = PROMPT_WITH_CONTEXT.format(full_poem=full_poem, single_line=single_line)
        raw_answer = call_model(prompt)
        answer = clean_translation(raw_answer)

        results.append({
            "单句": single_line,
            "全诗": full_poem,
            "翻译": answer
        })

        # 控制请求频率，避免触发限流
        time.sleep(0.5)

    # 保存结果
    result_df = pd.DataFrame(results)
    result_df.to_excel(OUTPUT_FILE, index=False)
    print(f"\n🎉 全部完成！共处理 {len(result_df)} 行，结果已保存至: {OUTPUT_FILE}")