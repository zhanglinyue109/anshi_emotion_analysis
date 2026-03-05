import openai
import pandas as pd
import json
import re
import time
import os
from tqdm import tqdm
try:
    from api_config import get_api_config, normalize_openai_base_url
except ModuleNotFoundError:
    from scripts.api_config import get_api_config, normalize_openai_base_url

# ======================
# 配置（必须与主程序一致）
# ======================
API_KEY, BASE_URL, MODEL = get_api_config()

OUTPUT_FILE = "anshi_annotated.xlsx"  # 你的输出文件路径（支持 .xlsx / .csv）
MAX_SECONDARY = 3
MAX_RETRY_ATTEMPTS = 10  # 对每行最多重试 10 次（直到成功）

# 初始化 OpenAI 客户端
client = openai.OpenAI(api_key=API_KEY, base_url=normalize_openai_base_url(BASE_URL))

# ======================
# 安全解析 JSON
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
# 构建完整的提示词（含 few-shot，紧贴输入）
# ======================
def build_full_prompt(poem_line):
    instruction = r"""
你是一位精通中国古典诗词的情感分析专家，请为诗句标注**最多3个**最贴切的**情感标签**。

# 可选的情感标签（共18个，必须严格使用以下名称）：
羁旅、伤逝、偃蹇、悲愁、忧伤、思念、孤寂、
讥讽、
喜悦、爱恋、壮思、淡泊、宴息、
慷慨、愤恨、
惊恐、
赞美、
迷茫

# ⚠️ 规则摘要：
1. 只能使用上述18个标签。
2. 纯写景/记事 → 返回空列表。
3. 隐含情绪（如“独坐”“寒雨”）→ 优先选最贴近的1个标签。
4. 最多3个，按相关性排序。
5. 输出仅 JSON：{"情感标签": [...]}

# 示例：
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
    return f"""{instruction}

## 现在请标注以下诗句：
诗句："{poem_line}"

## 输出（仅JSON）：
"""

# ======================
# 调用模型（带重试逻辑）
# ======================
def call_model_until_success(poem_line, max_attempts=10):
    valid_tags = {
        "羁旅", "伤逝", "偃蹇", "悲愁", "忧伤", "思念", "孤寂",
        "讥讽", "喜悦", "爱恋", "壮思", "淡泊", "宴息",
        "慷慨", "愤恨", "惊恐", "赞美", "迷茫"
    }

    for attempt in range(1, max_attempts + 1):
        try:
            prompt = build_full_prompt(poem_line)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=150,
            )
            content = response.choices[0].message.content.strip()

            # 清理 markdown
            if content.startswith("```"):
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1].strip()
                    if content.lower().startswith("json"):
                        content = content[4:].strip()

            result = safe_json_loads(content)
            tags = result.get("情感标签", [])

            # 过滤并去重
            cleaned = []
            seen = set()
            for tag in tags:
                t = str(tag).strip()
                if t in valid_tags and t not in seen:
                    cleaned.append(t)
                    seen.add(t)
                if len(cleaned) >= MAX_SECONDARY:
                    break

            time.sleep(1.0)  # 限流

            # 成功条件：只要返回了（哪怕空列表也算成功）
            return cleaned, True

        except Exception as e:
            print(f"  第 {attempt}/{max_attempts} 次调用失败: {str(e)[:100]}")
            time.sleep(2.0)

    # 所有重试失败
    return [], False

# ======================
# 主函数：补全失败行
# ======================
def complete_all_failed_rows(file_path):
    # 自动识别格式
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, dtype=str)
    else:
        df = pd.read_excel(file_path, dtype=str)

    df = df.fillna("")
    total_rows = len(df)

    # 找出未成功行
    failed_mask = (df["调用成功"] != "是")
    failed_indices = df[failed_mask].index.tolist()

    if not failed_indices:
        print("所有行均已成功标注，无需补全。")
        return

    print(f"🔁 共发现 {len(failed_indices)} 行需要补全，开始逐行重试...")

    success_count = 0
    for idx in tqdm(failed_indices, desc="补全进度"):
        poem = str(df.at[idx, "单句"]).strip()
        if not poem or poem.lower() in ("nan", "none", "", "null"):
            df.at[idx, "调用成功"] = "是"
            success_count += 1
            continue

        # 反复调用直到成功
        tags, success = call_model_until_success(poem, max_attempts=MAX_RETRY_ATTEMPTS)
        if success:
            df.at[idx, "调用成功"] = "是"
            for i in range(1, MAX_SECONDARY + 1):
                df.at[idx, f"情感标签{i}"] = tags[i - 1] if i <= len(tags) else ""
            success_count += 1
        else:
            df.at[idx, "调用成功"] = "否"  # 仍标记为失败（但理论上不会发生）

        # 每处理 10 行保存一次，防止崩溃丢失
        if (failed_indices.index(idx) + 1) % 10 == 0:
            _save_file(df, file_path)

    # 最终保存
    _save_file(df, file_path)

    # 最终检查
    final_failed = df[df["调用成功"] != "是"].shape[0]
    print(f"\n✅ 补全完成！")
    print(f"  - 成功补全: {success_count} 行")
    print(f"  - 仍失败: {final_failed} 行（应为 0）")

    if final_failed == 0:
        print("\n恭喜！现在所有诗句均已成功标注！")
    else:
        print("\n仍有失败行，请检查网络或 API 状态。")

def _save_file(df, path):
    if path.endswith('.csv'):
        df.to_csv(path, index=False, encoding='utf-8-sig')
    else:
        df.to_excel(path, index=False, engine='openpyxl')

# ======================
# 入口
# ======================
if __name__ == "__main__":
    if not os.path.exists(OUTPUT_FILE):
        raise FileNotFoundError(f"输出文件不存在: {OUTPUT_FILE}")
    complete_all_failed_rows(OUTPUT_FILE)
