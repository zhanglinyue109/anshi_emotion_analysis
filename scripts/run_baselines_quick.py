import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


LABEL_MAP = {
    "羁旅": "Sorrow",
    "伤逝": "Sorrow",
    "偃蹇": "Sorrow",
    "悲愁": "Sorrow",
    "忧伤": "Sorrow",
    "思念": "Sorrow",
    "孤寂": "Sorrow",
    "讥讽": "Disgust",
    "喜悦": "Joy",
    "爱恋": "Joy",
    "壮思": "Joy",
    "淡泊": "Joy",
    "宴息": "Joy",
    "慷慨": "Anger",
    "愤恨": "Anger",
    "惊恐": "Fear",
    "赞美": "Praise",
    "迷茫": "Confusion",
}

CLASSES = ["Sorrow", "Disgust", "Joy", "Anger", "Fear", "Praise", "Confusion"]

LEXICON = {
    "Sorrow": ["愁", "泪", "悲", "伤", "思", "孤", "寒", "苦", "病", "老", "别", "秋", "夜", "霜"],
    "Disgust": ["讥", "嘲", "笑", "轻薄", "鄙", "恶", "讽", "哂"],
    "Joy": ["喜", "乐", "欢", "笑", "醉", "酒", "春", "花", "晴", "歌", "宴", "游"],
    "Anger": ["怒", "愤", "恨", "慨", "兵", "战", "乱", "血", "杀", "贼"],
    "Fear": ["惧", "恐", "惊", "危", "畏", "怕"],
    "Praise": ["赞", "美", "贤", "忠", "义", "高", "清"],
    "Confusion": ["迷", "茫", "何处", "不知", "未卜", "彷徨", "惘"],
}


def get_primary_label(row: pd.Series) -> str | None:
    for col in ("情感标签1", "情感标签2", "情感标签3"):
        val = str(row[col]).strip() if pd.notna(row[col]) else ""
        if val in LABEL_MAP:
            return LABEL_MAP[val]
    return None


def rule_predict(text: str, fallback: str) -> str:
    scores = {k: 0 for k in CLASSES}
    for label, cues in LEXICON.items():
        for cue in cues:
            if cue in text:
                scores[label] += 1
    best_label, best_score = max(scores.items(), key=lambda kv: kv[1])
    return best_label if best_score > 0 else fallback


def mean_std(values: list[float]) -> dict:
    return {"mean": float(np.mean(values)), "std": float(np.std(values))}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "anshi_annotated.xlsx"
    output_dir = root / "outputs" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_path)
    df["label"] = df.apply(get_primary_label, axis=1)
    df = df[df["label"].notna()].copy()
    df["text"] = df["单句"].astype(str)
    df["group"] = df["全诗"].astype(str)

    x = df["text"].tolist()
    y = df["label"].tolist()
    groups = df["group"].tolist()

    metrics = defaultdict(list)
    seeds = [42, 43, 44]

    for seed in seeds:
        split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
        train_idx, test_idx = next(split.split(x, y, groups))
        x_train = [x[i] for i in train_idx]
        y_train = [y[i] for i in train_idx]
        x_test = [x[i] for i in test_idx]
        y_test = [y[i] for i in test_idx]

        majority = Counter(y_train).most_common(1)[0][0]

        pred_majority = [majority] * len(y_test)
        metrics["majority_macro_f1"].append(
            f1_score(y_test, pred_majority, average="macro", labels=CLASSES, zero_division=0)
        )
        metrics["majority_acc"].append(accuracy_score(y_test, pred_majority))

        pred_rule = [rule_predict(t, majority) for t in x_test]
        metrics["rule_macro_f1"].append(
            f1_score(y_test, pred_rule, average="macro", labels=CLASSES, zero_division=0)
        )
        metrics["rule_acc"].append(accuracy_score(y_test, pred_rule))

        model_lr = Pipeline(
            [
                ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(1, 3), min_df=2, max_features=30000)),
                ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
            ]
        )
        model_lr.fit(x_train, y_train)
        pred_lr = model_lr.predict(x_test)
        metrics["lr_macro_f1"].append(
            f1_score(y_test, pred_lr, average="macro", labels=CLASSES, zero_division=0)
        )
        metrics["lr_acc"].append(accuracy_score(y_test, pred_lr))

        model_svm = Pipeline(
            [
                ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(1, 4), min_df=2, max_features=50000)),
                ("clf", LinearSVC(class_weight="balanced")),
            ]
        )
        model_svm.fit(x_train, y_train)
        pred_svm = model_svm.predict(x_test)
        metrics["svm_macro_f1"].append(
            f1_score(y_test, pred_svm, average="macro", labels=CLASSES, zero_division=0)
        )
        metrics["svm_acc"].append(accuracy_score(y_test, pred_svm))

    summary = {k: mean_std(v) for k, v in metrics.items()}
    summary["dataset"] = {
        "rows_total": int(len(df)),
        "class_dist": {k: int(v) for k, v in Counter(df["label"]).items()},
    }
    summary["split"] = "GroupShuffleSplit(test_size=0.2) by full poem, 3 seeds"

    out_file = output_dir / "baseline_results_quick.json"
    out_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")


if __name__ == "__main__":
    main()
