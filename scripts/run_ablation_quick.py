import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
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


def get_primary_label(row: pd.Series) -> str | None:
    for col in ("情感标签1", "情感标签2", "情感标签3"):
        val = str(row[col]).strip() if pd.notna(row[col]) else ""
        if val in LABEL_MAP:
            return LABEL_MAP[val]
    return None


def evaluate_variant(pipeline: Pipeline, x: list[str], y: list[str], groups: list[str]) -> dict:
    f1_values: list[float] = []
    acc_values: list[float] = []
    for seed in (42, 43, 44):
        split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
        train_idx, test_idx = next(split.split(x, y, groups))
        x_train = [x[i] for i in train_idx]
        y_train = [y[i] for i in train_idx]
        x_test = [x[i] for i in test_idx]
        y_test = [y[i] for i in test_idx]

        pipeline.fit(x_train, y_train)
        y_pred = pipeline.predict(x_test)
        f1_values.append(f1_score(y_test, y_pred, average="macro", labels=CLASSES, zero_division=0))
        acc_values.append(accuracy_score(y_test, y_pred))

    return {
        "macro_f1_mean": float(np.mean(f1_values)),
        "macro_f1_std": float(np.std(f1_values)),
        "acc_mean": float(np.mean(acc_values)),
        "acc_std": float(np.std(acc_values)),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "anshi_annotated.xlsx"
    output_dir = root / "outputs" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_path)
    df["label"] = df.apply(get_primary_label, axis=1)
    df = df[df["label"].notna()].copy()
    x = df["单句"].astype(str).tolist()
    y = df["label"].tolist()
    groups = df["全诗"].astype(str).tolist()

    variants = {
        "svm_word13_balanced": Pipeline(
            [
                ("tfidf", TfidfVectorizer(analyzer="word", ngram_range=(1, 3), min_df=2, max_features=50000)),
                ("clf", LinearSVC(class_weight="balanced")),
            ]
        ),
        "svm_char13_balanced": Pipeline(
            [
                ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(1, 3), min_df=2, max_features=50000)),
                ("clf", LinearSVC(class_weight="balanced")),
            ]
        ),
        "svm_char14_balanced": Pipeline(
            [
                ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(1, 4), min_df=2, max_features=50000)),
                ("clf", LinearSVC(class_weight="balanced")),
            ]
        ),
        "svm_char14_unbalanced": Pipeline(
            [
                ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(1, 4), min_df=2, max_features=50000)),
                ("clf", LinearSVC()),
            ]
        ),
    }

    summary = {name: evaluate_variant(model, x, y, groups) for name, model in variants.items()}
    out_file = output_dir / "ablation_svm_quick.json"
    out_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")


if __name__ == "__main__":
    main()
