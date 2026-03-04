import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, hamming_loss
from sklearn.model_selection import GroupShuffleSplit
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import LinearSVC


LABELS_18 = [
    "羁旅",
    "伤逝",
    "偃蹇",
    "悲愁",
    "忧伤",
    "思念",
    "孤寂",
    "讥讽",
    "喜悦",
    "爱恋",
    "壮思",
    "淡泊",
    "宴息",
    "慷慨",
    "愤恨",
    "惊恐",
    "赞美",
    "迷茫",
]


def collect_labels(row: pd.Series) -> list[str]:
    labels: list[str] = []
    for col in ("情感标签1", "情感标签2", "情感标签3"):
        val = str(row[col]).strip() if pd.notna(row[col]) else ""
        if val in LABELS_18 and val not in labels:
            labels.append(val)
    return labels


def safe_f1(y_true: np.ndarray, y_pred: np.ndarray, average: str) -> float:
    return float(f1_score(y_true, y_pred, average=average, zero_division=0))


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "micro_f1": safe_f1(y_true, y_pred, average="micro"),
        "macro_f1": safe_f1(y_true, y_pred, average="macro"),
        "samples_f1": safe_f1(y_true, y_pred, average="samples"),
        "subset_accuracy": float(accuracy_score(y_true, y_pred)),
        "hamming_loss": float(hamming_loss(y_true, y_pred)),
    }


def mean_std(values: list[float]) -> dict[str, float]:
    return {"mean": float(np.mean(values)), "std": float(np.std(values))}


def build_models() -> dict[str, Pipeline]:
    return {
        "tfidf_char13_ovr_lr": Pipeline(
            [
                ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(1, 3), min_df=2, max_features=50000)),
                (
                    "clf",
                    OneVsRestClassifier(
                        LogisticRegression(max_iter=3000, class_weight="balanced")
                    ),
                ),
            ]
        ),
        "tfidf_char14_ovr_linsvm": Pipeline(
            [
                ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(1, 4), min_df=2, max_features=50000)),
                ("clf", OneVsRestClassifier(LinearSVC(class_weight="balanced"))),
            ]
        ),
        "tfidf_word12_ovr_linsvm": Pipeline(
            [
                ("tfidf", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, max_features=50000)),
                ("clf", OneVsRestClassifier(LinearSVC(class_weight="balanced"))),
            ]
        ),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "anshi_annotated.xlsx"
    output_dir = root / "outputs" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_path)
    df["labels"] = df.apply(collect_labels, axis=1)
    df["text"] = df["单句"].astype(str)
    df["group"] = df["全诗"].astype(str)

    x_all = df["text"].tolist()
    groups_all = df["group"].tolist()

    mlb = MultiLabelBinarizer(classes=LABELS_18)
    y_all = mlb.fit_transform(df["labels"].tolist())

    seeds = [42, 43, 44]
    models = build_models()

    metrics_by_model: dict[str, dict[str, list[float]]] = {}
    for name in models:
        metrics_by_model[name] = {
            "micro_f1": [],
            "macro_f1": [],
            "samples_f1": [],
            "subset_accuracy": [],
            "hamming_loss": [],
        }

    split_compare = {
        "group_split_char14_ovr_linsvm_micro_f1": [],
        "random_split_char14_ovr_linsvm_micro_f1": [],
    }

    for seed in seeds:
        # Group split by full poem (main result)
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
        train_idx, test_idx = next(gss.split(x_all, y_all, groups_all))
        x_train = [x_all[i] for i in train_idx]
        x_test = [x_all[i] for i in test_idx]
        y_train = y_all[train_idx]
        y_test = y_all[test_idx]

        # Majority-label baseline: always predict the most frequent label in training set
        label_counts = np.sum(y_train, axis=0)
        majority_idx = int(np.argmax(label_counts))
        y_pred_majority = np.zeros_like(y_test)
        y_pred_majority[:, majority_idx] = 1
        majority_metrics = evaluate_predictions(y_test, y_pred_majority)

        if "majority_single_label" not in metrics_by_model:
            metrics_by_model["majority_single_label"] = {
                "micro_f1": [],
                "macro_f1": [],
                "samples_f1": [],
                "subset_accuracy": [],
                "hamming_loss": [],
            }
        for k, v in majority_metrics.items():
            metrics_by_model["majority_single_label"][k].append(v)

        for name, model in models.items():
            model.fit(x_train, y_train)
            y_pred = model.predict(x_test)
            run_metrics = evaluate_predictions(y_test, y_pred)
            for k, v in run_metrics.items():
                metrics_by_model[name][k].append(v)

        # Random sentence split comparison (for leakage check)
        rng = np.random.RandomState(seed)
        indices = np.arange(len(x_all))
        rng.shuffle(indices)
        cut = int(len(indices) * 0.8)
        rs_train = indices[:cut]
        rs_test = indices[cut:]
        x_train_rs = [x_all[i] for i in rs_train]
        x_test_rs = [x_all[i] for i in rs_test]
        y_train_rs = y_all[rs_train]
        y_test_rs = y_all[rs_test]

        best_model_group = models["tfidf_char14_ovr_linsvm"]
        best_model_group.fit(x_train, y_train)
        y_pred_group = best_model_group.predict(x_test)
        split_compare["group_split_char14_ovr_linsvm_micro_f1"].append(
            safe_f1(y_test, y_pred_group, average="micro")
        )

        best_model_random = build_models()["tfidf_char14_ovr_linsvm"]
        best_model_random.fit(x_train_rs, y_train_rs)
        y_pred_rs = best_model_random.predict(x_test_rs)
        split_compare["random_split_char14_ovr_linsvm_micro_f1"].append(
            safe_f1(y_test_rs, y_pred_rs, average="micro")
        )

    summary: dict[str, dict] = {"models": {}, "split_sanity_check": {}}
    for name, metric_dict in metrics_by_model.items():
        summary["models"][name] = {metric: mean_std(values) for metric, values in metric_dict.items()}

    for k, v in split_compare.items():
        summary["split_sanity_check"][k] = mean_std(v)

    # Dataset profile for traceability
    label_counts = {label: int(y_all[:, i].sum()) for i, label in enumerate(LABELS_18)}
    per_row_labels = [len(labels) for labels in df["labels"].tolist()]
    summary["dataset"] = {
        "rows_total": int(len(df)),
        "rows_with_nonempty_label": int(sum(1 for n in per_row_labels if n > 0)),
        "rows_without_label": int(sum(1 for n in per_row_labels if n == 0)),
        "label_count_distribution": {
            "0": int(sum(1 for n in per_row_labels if n == 0)),
            "1": int(sum(1 for n in per_row_labels if n == 1)),
            "2": int(sum(1 for n in per_row_labels if n == 2)),
            "3": int(sum(1 for n in per_row_labels if n == 3)),
        },
        "label_frequency": label_counts,
        "evaluation_protocol": "3 seeds; group split by full poem (80/20) unless explicitly noted",
    }

    out_file = output_dir / "multilabel_baselines_18.json"
    out_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")


if __name__ == "__main__":
    main()
