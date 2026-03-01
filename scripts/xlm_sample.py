import torch
import pandas as pd
import numpy as np
from tqdm import tqdm
from transformers import XLMRobertaTokenizer
import torch.nn as nn

# 假设你的自定义模型在 mymodel.py 中
from src.mymodel import XLMRobertaForSequenceClassificationSig

class XLMRVARegressor(nn.Module):
    def __init__(self, model_path):
        super().__init__()
        self.encoder = XLMRobertaForSequenceClassificationSig.from_pretrained(
            model_path, num_labels=2
        )
        # 如果训练时没用 sigmoid，但需要 [0,1] 输出，取消下一行注释：
        # self.sigmoid = nn.Hardsigmoid()
    
    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        # if hasattr(self, 'sigmoid'):
        #     logits = self.sigmoid(logits)
        return logits

def load_model_and_tokenizer(model_path, device="cpu"):
    print(f"Loading tokenizer from {model_path}...")
    tokenizer = XLMRobertaTokenizer.from_pretrained(model_path)

    print("Loading model structure...")
    model = XLMRVARegressor(model_path)

    print("Loading model weights...")
    state_dict = torch.load(f"{model_path}/pytorch_model.bin", map_location=device)
    model.load_state_dict(state_dict, strict=False)

    model.to(device)
    model.eval()
    print("✅ Model loaded.")
    return model, tokenizer

def predict_va_batch(texts, model, tokenizer, device, max_length=128):
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        return outputs.cpu().numpy()

def main():
    # === 配置区 ===
    MODEL_PATH = "/home/kongcunliang/zhanglinyue/tang_jscd/appreciation_poem/models/XLM-RoBERTa-large MSE"
    INPUT_FILE = "/home/kongcunliang/zhanglinyue/tang_jscd/appreciation_poem/translate_sample_100.xlsx"          # ← 支持 .xlsx 或 .xls
    OUTPUT_FILE = "va_sample100.xlsx"  # ← 可改为 .csv 如果你更喜欢 CSV
    BATCH_SIZE = 8
    MAX_LENGTH = 128
    DEVICE = "cpu"

    torch.set_num_threads(4)

    # === 加载模型 ===
    model, tokenizer = load_model_and_tokenizer(MODEL_PATH, device=DEVICE)

    # === 读取 Excel 文件 ===
    print(f"Reading Excel file: {INPUT_FILE}")
    df = pd.read_excel(INPUT_FILE, dtype=str)  # 保持所有列为字符串，避免 NaN 类型问题

    if df.shape[1] < 3:
        raise ValueError("Excel 表格至少需要三列！")

    sentences = df.iloc[:, 2].fillna("").astype(str).tolist()  # 第三列（索引 2）

    # === 批量预测 ===
    print(f"Predicting for {len(sentences)} rows...")
    all_valences = []
    all_arousals = []

    for i in tqdm(range(0, len(sentences), BATCH_SIZE), desc="Batches"):
        batch_texts = sentences[i:i + BATCH_SIZE]
        try:
            preds = predict_va_batch(batch_texts, model, tokenizer, DEVICE, max_length=MAX_LENGTH)
            all_valences.extend(preds[:, 0].tolist())
            all_arousals.extend(preds[:, 1].tolist())
        except Exception as e:
            print(f"\n⚠️ Error at batch starting row {i}: {e}")
            for _ in range(len(batch_texts)):
                all_valences.append(None)
                all_arousals.append(None)

    # === 添加结果列 ===
    df['Valence'] = all_valences
    df['Arousal'] = all_arousals

    # === 保存输出 ===
    if OUTPUT_FILE.endswith('.xlsx'):
        df.to_excel(OUTPUT_FILE, index=False)
    elif OUTPUT_FILE.endswith('.csv'):
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    else:
        # 默认保存为 Excel
        df.to_excel(OUTPUT_FILE, index=False)

    print(f"\n🎉 Done! Results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
