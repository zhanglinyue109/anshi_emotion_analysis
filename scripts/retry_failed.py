import json
import openai
import time
import re
from collections import defaultdict
from tqdm import tqdm
try:
    from api_config import get_api_config, normalize_openai_base_url
except ModuleNotFoundError:
    from scripts.api_config import get_api_config, normalize_openai_base_url

# === 配置（与主脚本一致）===
API_KEY, BASE_URL, MODEL = get_api_config()

client = openai.OpenAI(api_key=API_KEY, base_url=normalize_openai_base_url(BASE_URL))

# 输入输出文件
INPUT_FILE = "aligned_output.jsonl"
OUTPUT_FILE = "retry_aligned_output.jsonl"
ORIGINAL_INPUT_FOR_APPRECIATION = "appreciation.jsonl"  # 用于查找原始鉴赏文本

# 标点正则（保持一致）
PUNCTUATION_REGEX = r'[……。，、；？！：:"“”‘’（）〔〕【】《》〈〉,\.\?\!\;\:\(\)\[\]\{\}\/\s]'

# 失败标记
FAILURE_MSG = "模型调用失败，无法获取解释。"


def load_appreciations():
    """从原始 appreciation.jsonl 加载 { (title, author): appreciation } 映射"""
    mapping = {}
    try:
        with open(ORIGINAL_INPUT_FOR_APPRECIATION, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                key = (data.get("title", "").strip(), data.get("author", "").strip())
                mapping[key] = data.get("appreciation", "").strip()
    except Exception as e:
        print(f"❌ 无法加载原始鉴赏文件 {ORIGINAL_INPUT_FOR_APPRECIATION}: {e}")
        exit(1)
    return mapping


def split_poem_lines(content: str):
    lines = []
    for raw_line in content.split('\n'):
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        parts = re.split(PUNCTUATION_REGEX, raw_line)
        for part in parts:
            clean_part = part.strip()
            if clean_part:
                lines.append(clean_part)
    return lines


def align_batch_for_retry(title, author, failed_lines, appreciation, batch_size=15):
    all_results = []
    for i in range(0, len(failed_lines), batch_size):
        batch = failed_lines[i:i + batch_size]
        poem_text = "\n".join(batch)
        prompt = f"""你是一位古典文学专家。请根据以下诗歌的完整鉴赏文字，为每一句诗找出最直接、最相关的解释段落。

诗歌标题：{title}
作者：{author}

诗句列表（已去除所有标点，每句一行）：
{poem_text}

完整鉴赏内容：
{appreciation}

请严格按照以下要求输出：
1. 输出一个 JSON 数组，长度必须等于诗句数量。
2. 每个元素格式：{{"line": "原诗句", "explanation": "对应的解释文本"}}
3. 解释必须忠实于鉴赏原文，不要总结或改写。
4. 若无明确对应，请将 explanation 设为 "无直接对应解释。"
5. 仅输出纯 JSON，不要任何额外文字、说明或 markdown。

现在请输出对齐结果："""

        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=2500,
                    timeout=60
                )
                raw = response.choices[0].message.content.strip()
                if raw.startswith("```"):
                    raw = re.sub(r'^```(?:json)?\s*', '', raw)
                    raw = re.sub(r'\s*```$', '', raw)
                result = json.loads(raw)
                if len(result) == len(batch):
                    all_results.extend(result)
                    break
                else:
                    time.sleep(1)
            except Exception as e:
                time.sleep(2)
        else:
            for line in batch:
                all_results.append({"line": line, "explanation": "重试仍失败。"})
    return all_results


def main():
    # 1. 加载原始鉴赏文本
    print("📚 正在加载原始鉴赏文本...")
    appreciation_map = load_appreciations()

    # 2. 收集失败条目，按 (title, author) 分组
    print("🔍 正在扫描失败条目...")
    failed_groups = defaultdict(list)
    all_records = []

    with open(INPUT_FILE, 'r', encoding='utf-8') as fin:
        for line in fin:
            if not line.strip():
                continue
            record = json.loads(line)
            all_records.append(record)
            if record.get("explanation") == FAILURE_MSG:
                key = (record["title"], record["author"])
                failed_groups[key].append(record["line"])

    total_failed = sum(len(lines) for lines in failed_groups.items())
    if total_failed == 0:
        print("✅ 没有发现失败条目，无需重试。")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
            with open(INPUT_FILE, 'r', encoding='utf-8') as fin:
                fout.write(fin.read())
        return

    poem_items = list(failed_groups.items())
    print(f"🔁 共发现 {total_failed} 条失败记录，涉及 {len(poem_items)} 首诗，开始重试...")

    # 3. 构建映射：key -> 重试后的解释字典 {line: explanation}
    retry_explanations = {}

    # 使用 tqdm 显示进度条
    for (title, author), lines in tqdm(poem_items, desc="🔄 重试诗歌", unit="首"):
        key = (title, author)
        appreciation = appreciation_map.get(key, "")
        if not appreciation:
            for line in lines:
                retry_explanations[(title, author, line)] = "缺少原始鉴赏，无法重试。"
            continue

        results = align_batch_for_retry(title, author, lines, appreciation, batch_size=15)
        for res in results:
            retry_explanations[(title, author, res["line"])] = res["explanation"]
        time.sleep(0.3)  # 节流

    # 4. 写入新文件
    success_count = 0
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
        for record in all_records:
            title = record["title"]
            author = record["author"]
            line = record["line"]
            if record["explanation"] == FAILURE_MSG:
                new_exp = retry_explanations.get((title, author, line), "重试逻辑异常。")
                if "失败" not in new_exp and "缺少" not in new_exp and "异常" not in new_exp:
                    success_count += 1
                record["explanation"] = new_exp
            fout.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"\n✅ 重试完成！成功修复 {success_count} 条，结果已保存至 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
