import openai
import json
from tqdm import tqdm
try:
    from api_config import get_api_config, normalize_openai_base_url
except ModuleNotFoundError:
    from scripts.api_config import get_api_config, normalize_openai_base_url
# 配置 API Key 和 Base URL
API_KEY, BASE_URL, MODEL = get_api_config()

def chat_with_gpt4(prompt, model=MODEL):
    """与ChatGPT API交互的函数"""
    client = openai.OpenAI(api_key=API_KEY, base_url=normalize_openai_base_url(BASE_URL))
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

def process_poems(input_file, output_file):
    """处理JSONL文件的主函数"""
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line_number, line in tqdm(enumerate(infile, 1)):
            try:
                # 解析JSON数据
                data = json.loads(line)
                content = data.get('content', '')
                appreciation = data.get('appreciation', '')
                
                # 构建带转义字符的prompt
                prompt = f"""根据以下诗歌内容，分别选出这首诗中直接表达情感的诗歌单句：
                
## 诗歌内容：
{content}
                
                
请完成：
找出所有情感倾向明显外露的诗句，每次严格输出一个诗歌单句（以逗号/句号/问号/感叹号为分界为一个诗歌单句，不可以输出如“不睹皇居壮,安知天子尊。”这样包含两句的诗）
                
请严格使用以下JSON格式输出（支持数组），不能在这一格式以外输出任何其他内容：
[
  {{"poem":"诗句1"}},
  {{"poem":"诗句2"}}
]"""
                
                # 获取并处理响应
                response = chat_with_gpt4(prompt)
                cleaned_response = response.strip().replace("，", ",").replace("；", ";")
                
                # 解析验证响应
                results = json.loads(cleaned_response)
                print(results)
                # 写入结果（每句单独一行）
                for item in results:
                    outfile.write(json.dumps(item, ensure_ascii=False) + '\n')
                
                print(f"第 {line_number} 行处理成功，发现{len(results)}个结果")
                
            except json.JSONDecodeError as e:
                print(f"第 {line_number} 行JSON解析失败：{str(e)}")
                print(f"原始响应：{response}")
            except Exception as e:
                print(f"第 {line_number} 行处理异常：{str(e)}")

if __name__ == "__main__":
    process_poems("appreciation.jsonl", "emo_poems.jsonl")
