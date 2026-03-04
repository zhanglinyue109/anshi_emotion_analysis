import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score


# A deterministic single-word proxy baseline for comparison.
# It approximates "one-word emotion output" with a fixed lexicon.
LEXICON = {
    "Sorrow": ["愁", "泪", "悲", "伤", "思", "孤", "寒", "苦", "病", "老", "别", "秋", "夜", "霜"],
    "Disgust": ["讥", "嘲", "笑", "轻薄", "鄙", "恶", "讽", "哂"],
    "Joy": ["喜", "乐", "欢", "笑", "醉", "酒", "春", "花", "晴", "歌", "宴", "游"],
    "Anger": ["怒", "愤", "恨", "慨", "兵", "战", "乱", "血", "杀", "贼"],
    "Fear": ["惧", "恐", "惊", "危", "畏", "怕"],
    "Praise": ["赞", "美", "贤", "忠", "义", "高", "清"],
    "Confusion": ["迷", "茫", "何处", "不知", "未卜", "彷徨", "惘"],
}


def entropy_bits(counts: np.ndarray) -> float:
    probs = counts / np.sum(counts)
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def word_proxy_label(text: str, label_order: list[str]) -> str:
    scores = {label: 0 for label in label_order}
    for label, cues in LEXICON.items():
        for cue in cues:
            if cue in text:
                scores[label] += 1
    best_label, best_score = max(scores.items(), key=lambda kv: kv[1])
    return best_label if best_score > 0 else "Sorrow"


def kmeans_numpy(x: np.ndarray, k: int, seed: int, max_iter: int = 30) -> np.ndarray:
    rs = np.random.RandomState(seed)
    n = x.shape[0]
    centers = x[rs.choice(n, k, replace=False)].copy()
    labels = np.full(n, -1, dtype=np.int32)

    for _ in range(max_iter):
        x2 = np.sum(x * x, axis=1, keepdims=True)
        c2 = np.sum(centers * centers, axis=1)[None, :]
        d2 = x2 + c2 - 2.0 * np.dot(x, centers.T)
        new_labels = np.argmin(d2, axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels

        for j in range(k):
            mask = labels == j
            if np.any(mask):
                centers[j] = x[mask].mean(axis=0)
            else:
                centers[j] = x[rs.randint(0, n)]

    return labels


def cluster_stability(x: np.ndarray, k: int, seeds: list[int]) -> dict:
    runs = []
    non_empty = []
    for seed in seeds:
        labels = kmeans_numpy(x, k=k, seed=seed)
        runs.append(labels)
        non_empty.append(int(len(np.unique(labels))))

    pair_aris = [
        float(adjusted_rand_score(runs[i], runs[j]))
        for i, j in combinations(range(len(runs)), 2)
    ]
    return {
        "ari_mean": float(np.mean(pair_aris)),
        "ari_std": float(np.std(pair_aris)),
        "non_empty_clusters_mean": float(np.mean(non_empty)),
        "non_empty_clusters_std": float(np.std(non_empty)),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    poems_path = root / "outputs" / "tables" / "emo_poems.txt"
    emb_path = root / "appreciation_embeddings.npy"
    emb_cluster_path = root / "appreciation_clustering_results_20.csv"
    output_path = root / "outputs" / "tables" / "embedding_innovation_compare.json"

    poems = [line.strip() for line in poems_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    embeddings = np.load(emb_path)

    n = min(len(poems), int(embeddings.shape[0]))
    poems = poems[:n]
    embeddings = embeddings[:n].astype(np.float32)

    # Standardize for distance-based clustering.
    mean = embeddings.mean(axis=0, keepdims=True)
    std = embeddings.std(axis=0, keepdims=True) + 1e-6
    emb_std = (embeddings - mean) / std

    labels_order = list(LEXICON.keys())
    label_to_idx = {label: i for i, label in enumerate(labels_order)}
    proxy_labels = [word_proxy_label(text, labels_order) for text in poems]
    word_matrix = np.zeros((n, len(labels_order)), dtype=np.float32)
    for i, label in enumerate(proxy_labels):
        word_matrix[i, label_to_idx[label]] = 1.0

    seeds = list(range(42, 52))  # 10 runs
    emb_stability_k20 = cluster_stability(emb_std, k=20, seeds=seeds)
    word_stability_k20 = cluster_stability(word_matrix, k=20, seeds=seeds)

    emb_stability_k7 = cluster_stability(emb_std, k=7, seeds=seeds)
    word_stability_k7 = cluster_stability(word_matrix, k=7, seeds=seeds)

    word_counter = Counter(proxy_labels)
    word_counts = np.array([word_counter[label] for label in labels_order], dtype=np.float64)
    word_entropy = entropy_bits(word_counts)
    word_entropy_norm = float(word_entropy / np.log2(len(labels_order)))

    # Existing embedding clustering result (k=20) for entropy profiling.
    emb_clusters_df = pd.read_csv(emb_cluster_path)
    emb_cluster_counts = emb_clusters_df["cluster_label"].value_counts().sort_index().values.astype(np.float64)
    emb_entropy = entropy_bits(emb_cluster_counts)
    emb_entropy_norm = float(emb_entropy / np.log2(len(emb_cluster_counts)))

    result = {
        "dataset": {
            "num_samples": n,
            "embedding_dim": int(embeddings.shape[1]),
            "word_proxy_labels": labels_order,
        },
        "word_proxy_distribution": {
            "counts": {label: int(word_counter[label]) for label in labels_order},
            "entropy_bits": word_entropy,
            "normalized_entropy": word_entropy_norm,
        },
        "embedding_cluster_distribution_k20": {
            "num_clusters": int(len(emb_cluster_counts)),
            "min_cluster_size": int(np.min(emb_cluster_counts)),
            "max_cluster_size": int(np.max(emb_cluster_counts)),
            "entropy_bits": emb_entropy,
            "normalized_entropy": emb_entropy_norm,
        },
        "stability": {
            "k20": {
                "embedding": emb_stability_k20,
                "word_proxy": word_stability_k20,
            },
            "k7": {
                "embedding": emb_stability_k7,
                "word_proxy": word_stability_k7,
            },
            "seeds": seeds,
        },
        "notes": [
            "Word proxy is a deterministic single-word baseline built from lexical cues.",
            "Embedding uses existing Qwen hidden-state vectors from appreciation_embeddings.npy.",
            "KMeans is implemented in NumPy for environment portability.",
        ],
    }

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
