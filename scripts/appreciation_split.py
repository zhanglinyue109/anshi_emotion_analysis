import json
import openai
import time
import re
try:
    from api_config import get_api_config, normalize_openai_base_url
except ModuleNotFoundError:
    from scripts.api_config import get_api_config, normalize_openai_base_url

# === 配置 ===
API_KEY, BASE_URL, MODEL = get_api_config()

client = openai.OpenAI(api_key=API_KEY, base_url=normalize_openai_base_url(BASE_URL))

INPUT_FILE = "appreciation.jsonl"
OUTPUT_FILE = "aligned_output.jsonl"

# 标点符号正则（涵盖中英文常见标点 + 空白）
PUNCTUATION_REGEX = r'[……。，、；？！：:"“”‘’（）〔〕【】《》〈〉,\.\?\!\;\:\(\)\[\]\{\}\/\s]'

def split_poem_lines(content: str):
    """
    按标点符号分割诗句，并移除所有标点和空白。
    示例输入："中原初逐鹿，投笔事戎轩。" → 输出：["中原初逐鹿", "投笔事戎轩"]
    """
    lines = []
    for raw_line in content.split('\n'):
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        # 按标点分割
        parts = re.split(PUNCTUATION_REGEX, raw_line)
        for part in parts:
            clean_part = part.strip()
            if clean_part:  # 仅保留非空片段
                lines.append(clean_part)
    return lines


def align_all_lines_batch(title: str, author: str, poem_lines: list, appreciation: str, batch_size=15):
    """
    将 poem_lines 分批（每批最多 batch_size 行）发送给模型，合并结果。
    """
    all_results = []

    for i in range(0, len(poem_lines), batch_size):
        batch_lines = poem_lines[i:i + batch_size]
        poem_text = "\n".join(batch_lines)
        
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

        max_retries = 3
        success = False
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=2500,
                    timeout=60
                )
                raw_output = response.choices[0].message.content.strip()

                # 清理可能的 ```json 包裹
                if raw_output.startswith("```"):
                    raw_output = re.sub(r'^```(?:json)?\s*', '', raw_output)
                    raw_output = re.sub(r'\s*```$', '', raw_output)

                result = json.loads(raw_output)
                
                # 校验长度是否匹配
                if len(result) != len(batch_lines):
                    print(f"⚠️ 批次 {i//batch_size + 1} 返回结果数量不匹配（期望 {len(batch_lines)}，实际 {len(result)}），重试...")
                    time.sleep(1)
                    continue
                
                all_results.extend(result)
                success = True
                break  # 成功则跳出重试循环

            except Exception as e:
                print(f"❌ 批次 {i//batch_size + 1} 调用失败（《{title}》）: {e}，重试中 ({attempt+1}/{max_retries})")
                time.sleep(2)  # 稍长等待以缓解服务压力
        
        if not success:
            # 所有重试失败，填充默认值
            for line in batch_lines:
                all_results.append({"line": line, "explanation": "模型调用失败，无法获取解释。"})
    
    return all_results


def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:

        total_entries = 0
        for idx, line in enumerate(fin, 1):
            try:
                data = json.loads(line.strip())
                title = data.get("title", "")
                author = data.get("author", "")
                content = data.get("content", "")
                appreciation = data.get("appreciation", "")

                if not content or not appreciation:
                    print(f"⚠️ 第 {idx} 行缺少 content 或 appreciation，跳过。")
                    continue

                # ✅ 关键：使用标点分割断句
                poem_lines = split_poem_lines(content)

                if not poem_lines:
                    print(f"⚠️ 第 {idx} 行未提取到有效诗句，跳过。")
                    continue

                print(f"📖 正在处理《{title}》({author})，共 {len(poem_lines)} 句...")

                aligned = align_all_lines_batch(title, author, poem_lines, appreciation, batch_size=15)
                if aligned is None:
                    continue

                # 写入每句结果
                for i, line_text in enumerate(poem_lines):
                    exp = aligned[i].get("explanation", "解析缺失。") if i < len(aligned) else "结果不足。"
                    out_obj = {
                        "title": title,
                        "author": author,
                        "line": line_text,
                        "explanation": exp
                    }
                    fout.write(json.dumps(out_obj, ensure_ascii=False) + '\n')

                total_entries += len(poem_lines)
                fout.flush()
                time.sleep(0.3)  # 避免 API 过载

            except json.JSONDecodeError:
                print(f"❌ 第 {idx} 行不是合法 JSON，跳过。")
            except Exception as e:
                print(f"❌ 处理第 {idx} 行时发生未预期错误: {e}")

        print(f"\n批量处理完成！共输出 {total_entries} 条记录，保存至 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
