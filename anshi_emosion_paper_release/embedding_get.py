import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm
import numpy as np

# 配置参数
MODEL_NAME = "/home/kongcunliang/zhanglinyue/唐诗鉴赏辞典/Qwen3-8B"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 8  # 根据GPU显存调整
MAX_LENGTH = 512
PROMPT = """\
仅使用一个词语概括给定诗句的情感。
诗句：白日放歌须纵酒
答案：“喜悦”
诗句：{}
答案：“
"""

# 初始化模型
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True,
)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True,
    dtype=torch.bfloat16 if DEVICE == "cuda" else torch.float32,
    device_map="auto"
).eval()

# 从文件读取诗句
def load_poems_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        poems = []
        for line in file:
            stripped_line = line.strip().replace('\r', '')  # 去除首尾空白和回车符
            if stripped_line:
                poems.append(stripped_line)
    return poems

def process_poems(poems):
    # 构建prompt
    prompts = [PROMPT.format(poem) for poem in poems]
    # 批量编码
    inputs = tokenizer(
        prompts,
        padding=True,
        truncation=True,
        padding_side='left',
        max_length=MAX_LENGTH,
        return_tensors="pt"
    ).to(DEVICE)
    
    # 情感词生成
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=4,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id
        )
    
    # 解码结果
    answers = [
        tokenizer.decode(ids[len(prompt_ids):], skip_special_tokens=True)
        for ids, prompt_ids in zip(outputs, inputs.input_ids)
    ]
    
    # 提取embedding
    with torch.no_grad():
        hidden_states = model(**inputs, output_hidden_states=True).hidden_states
    
    # 取最后一层第一个[CLS]位置的embedding
    embeddings = hidden_states[-1][:, -1, :].to(torch.float32).cpu().numpy()
    
    return list(zip(answers, embeddings))

# 读取诗句文件
poems_file_path = '/home/kongcunliang/zhanglinyue/唐诗鉴赏辞典/appreciation_poem/emo_poems.txt'  # 指定你的TXT文件路径
poems = load_poems_from_file(poems_file_path)

# 批量处理
results = []
for i in tqdm(range(0, len(poems), BATCH_SIZE)):
    batch = poems[i:i+BATCH_SIZE]
    results.extend(process_poems(batch))

# 处理结果
for poem, res in zip(poems, results):
    print(f"诗句: {poem}, 情感词: {res[0]}")

# 保存嵌入作为numpy数组文件
embeddings = np.array([res[1] for res in results])
np.save("appreciation_embeddings.npy", embeddings)