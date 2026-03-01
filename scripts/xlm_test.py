import torch
from transformers import XLMRobertaTokenizer, XLMRobertaModel
from transformers import DistilBertForSequenceClassification, XLMRobertaForSequenceClassification
import torch.nn as nn

from src.mymodel import XLMRobertaForSequenceClassificationSig

class XLMRVARegressor(nn.Module):
    def __init__(self, model_path):
        super().__init__()
        # self.encoder = XLMRobertaForSequenceClassification.from_pretrained(model_path)
        self.encoder = XLMRobertaForSequenceClassificationSig.from_pretrained(model_path, num_labels=2)
        # self.encoder = XLMRobertaModel.from_pretrained(model_path)
        # self.regressor = nn.Linear(self.encoder.config.hidden_size, 2)
        self.sigmoid = nn.Hardsigmoid()  # 论文使用 hard sigmoid 将输出压缩到 [0, 1]

    def forward(self, input_ids, attention_mask): 
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        # cls_emb = outputs.last_hidden_state[:, 0]  # [CLS] token
        # logits = self.regressor(cls_emb)
        # return self.sigmoid(outputs.logits)
        return outputs.logits

def load_model_and_tokenizer(model_path):
    device = "cpu"
    print(f"Using device: {device}")

    tokenizer = XLMRobertaTokenizer.from_pretrained(model_path)
    model = XLMRVARegressor(model_path)
    state_dict = torch.load(f"{model_path}/pytorch_model.bin", map_location=device)
    model.load_state_dict(state_dict, strict=False)
    model.to(device)
    model.eval()
    return model, tokenizer, device

def predict_va(text, model, tokenizer, device):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=False,          
        truncation=True,
        max_length=128        
    ).to(device)

    with torch.no_grad():
        output = model(input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"])
        valence, arousal = output.squeeze().cpu().numpy()
    return float(valence), float(arousal)

def main():
    MODEL_PATH = "/home/kongcunliang/zhanglinyue/tang_jscd/appreciation_poem/models/XLM-RoBERTa-large MSE" #/Users/linyuezhang/Desktop/XLM-RoBERTa-large MSE/XLM-RoBERTa-large MSE
    model, tokenizer, device = load_model_and_tokenizer(MODEL_PATH)

    chinese_sentences = [
        "这一去，只怕是再无重逢之日了。",
    ]

    print("正在使用微调后的 ...\n")
    print(f"{'文本':<25} | {'Valence (效价)':<15} | {'Arousal (唤醒度)'}")
    print("-" * 65)

    for text in chinese_sentences:
        v, a = predict_va(text, model, tokenizer, device)
        valence_label = "正向" if v > 0.5 else "负向"
        arousal_label = "高唤醒" if a > 0.5 else "低唤醒"
        print(f"{text:<25} | {v:.3f} ({valence_label})     | {a:.3f} ({arousal_label})")

if __name__ == "__main__":
    main()
