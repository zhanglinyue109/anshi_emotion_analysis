import asyncio
import json
import os
import re
from collections import Counter
from pathlib import Path

import httpx
import numpy as np
import pandas as pd

try:
    from api_config import get_api_config, build_chat_completions_url
except ModuleNotFoundError:
    from scripts.api_config import get_api_config, build_chat_completions_url


PROMPT_A = (
    "仅使用一个中文词语概括给定诗句的主要情感。"
    "不要解释，不要标点，不要多个词。"
    "诗句：{line}\n答案："
)

PROMPT_B = (
    "你是古典诗歌情绪标注助手。"
    "请对下面诗句输出一个最贴切的中文情感词（只许一个词）。"
    "禁止解释、禁止句子、禁止多个词。"
    "诗句：{line}\n情感词："
)


def strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json|text)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def extract_one_word(text: str) -> str:
    t = strip_code_fence(text)
    t = t.replace("答案：", "").replace("情感词：", "").strip()
    first_line = t.splitlines()[0].strip() if t else ""
    first_line = first_line.strip("“”\"'`[]()（）{}")
    # Prefer Chinese token
    zh = re.findall(r"[\u4e00-\u9fff]{1,8}", first_line)
    if zh:
        return zh[0]
    # fallback: first token
    tok = re.split(r"\s|,|，|。|；|;|：|:", first_line)[0].strip()
    return tok[:32]


async def call_one(
    client: httpx.AsyncClient,
    url: str,
    headers: dict,
    model: str,
    line: str,
    prompt_template: str,
    semaphore: asyncio.Semaphore,
    retries: int = 4,
) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt_template.format(line=line)}],
        "temperature": 0,
        "max_tokens": 16,
    }

    async with semaphore:
        for attempt in range(1, retries + 1):
            try:
                r = await client.post(url, json=payload, headers=headers)
                r.raise_for_status()
                raw = r.json()["choices"][0]["message"]["content"].strip()
                word = extract_one_word(raw)
                return {"ok": True, "word": word, "raw": raw}
            except Exception as e:
                if attempt == retries:
                    return {"ok": False, "word": "", "raw": f"[ERROR] {type(e).__name__}: {e}"}
                await asyncio.sleep(min(2 ** (attempt - 1), 4))


async def run_batch(
    lines: list[str],
    prompt_template: str,
    out_path: Path,
    model: str,
    api_key: str,
    base_url: str,
    concurrency: int,
) -> list[dict]:
    done = {}
    if out_path.exists():
        with out_path.open("r", encoding="utf-8") as f:
            for row in f:
                if row.strip():
                    obj = json.loads(row)
                    done[int(obj["idx"])] = obj

    semaphore = asyncio.Semaphore(concurrency)
    url = build_chat_completions_url(base_url)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    timeout = httpx.Timeout(60.0, connect=20.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        pending = []
        for idx, line in enumerate(lines):
            if idx in done:
                continue
            pending.append(
                asyncio.create_task(
                    call_one(
                        client=client,
                        url=url,
                        headers=headers,
                        model=model,
                        line=line,
                        prompt_template=prompt_template,
                        semaphore=semaphore,
                    )
                )
            )

        # Append mode for checkpointing
        if pending:
            with out_path.open("a", encoding="utf-8") as wf:
                start = 0
                for idx, line in enumerate(lines):
                    if idx in done:
                        continue
                    res = await pending[start]
                    start += 1
                    obj = {"idx": idx, "line": line, **res}
                    wf.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    done[idx] = obj

    return [done[i] for i in range(len(lines))]


def summarize(rows_a: list[dict], rows_b: list[dict], emb_cluster_csv: Path) -> dict:
    assert len(rows_a) == len(rows_b)
    n = len(rows_a)
    valid_pairs = 0
    exact_match = 0
    mismatch = 0
    empty_pairs = 0

    words_a = []
    words_b = []
    for a, b in zip(rows_a, rows_b):
        wa = a.get("word", "").strip()
        wb = b.get("word", "").strip()
        if wa:
            words_a.append(wa)
        if wb:
            words_b.append(wb)

        if not wa or not wb:
            empty_pairs += 1
            continue
        valid_pairs += 1
        if wa == wb:
            exact_match += 1
        else:
            mismatch += 1

    cnt_a = Counter(words_a)
    cnt_b = Counter(words_b)

    def norm_entropy(counter: Counter) -> float:
        if not counter:
            return 0.0
        arr = np.array(list(counter.values()), dtype=np.float64)
        p = arr / arr.sum()
        ent = -float(np.sum(p * np.log2(p)))
        return float(ent / np.log2(len(arr))) if len(arr) > 1 else 0.0

    emb_df = pd.read_csv(emb_cluster_csv)
    emb_counts = emb_df["cluster_label"].value_counts().values.astype(np.float64)
    p = emb_counts / emb_counts.sum()
    emb_ent = -float(np.sum(p * np.log2(p)))
    emb_norm_ent = float(emb_ent / np.log2(len(emb_counts)))

    return {
        "num_sentences": n,
        "valid_pairs": valid_pairs,
        "empty_pairs": empty_pairs,
        "exact_match_rate_promptA_vs_promptB": float(exact_match / valid_pairs) if valid_pairs else 0.0,
        "mismatch_rate_promptA_vs_promptB": float(mismatch / valid_pairs) if valid_pairs else 0.0,
        "prompt_a": {
            "unique_words": int(len(cnt_a)),
            "normalized_entropy": norm_entropy(cnt_a),
            "top10": cnt_a.most_common(10),
        },
        "prompt_b": {
            "unique_words": int(len(cnt_b)),
            "normalized_entropy": norm_entropy(cnt_b),
            "top10": cnt_b.most_common(10),
        },
        "embedding_cluster_k20": {
            "normalized_entropy": emb_norm_ent,
            "num_clusters": int(len(emb_counts)),
            "min_cluster_size": int(np.min(emb_counts)),
            "max_cluster_size": int(np.max(emb_counts)),
        },
    }


async def main() -> None:
    api_key, base_url, model = get_api_config()
    concurrency = int(os.getenv("API_CONCURRENCY", "8"))

    root = Path(__file__).resolve().parents[1]
    in_path = root / "outputs" / "tables" / "emo_poems.txt"
    emb_cluster_csv = root / "appreciation_clustering_results_20.csv"
    out_a = root / "outputs" / "tables" / "api_word_prompt_a.jsonl"
    out_b = root / "outputs" / "tables" / "api_word_prompt_b.jsonl"
    out_summary = root / "outputs" / "tables" / "api_word_stability_summary.json"

    lines = [line.strip() for line in in_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    rows_a = await run_batch(
        lines=lines,
        prompt_template=PROMPT_A,
        out_path=out_a,
        model=model,
        api_key=api_key,
        base_url=base_url,
        concurrency=concurrency,
    )
    rows_b = await run_batch(
        lines=lines,
        prompt_template=PROMPT_B,
        out_path=out_b,
        model=model,
        api_key=api_key,
        base_url=base_url,
        concurrency=concurrency,
    )

    summary = summarize(rows_a, rows_b, emb_cluster_csv=emb_cluster_csv)
    out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_summary}")


if __name__ == "__main__":
    asyncio.run(main())
