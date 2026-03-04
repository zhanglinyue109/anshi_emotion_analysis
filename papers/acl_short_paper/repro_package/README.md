# Reproducibility Package (ACL Short Paper)

This folder summarizes the minimum materials needed to reproduce the paper results.

## Repository
- GitHub: https://github.com/zhanglinyue109/anshi_emotion_analysis
- Paper source: `papers/acl_short_paper/main.tex`

## Environment
1. Use Python 3.10+.
2. Install dependencies from repository requirements.
3. Set environment variables (do not hardcode secrets):
   - `API_KEY`
   - `BASE_URL`
   - `MODEL`

## Reproduction Order
1. Data preparation and annotation
   - `scripts/annotate.py`
   - `scripts/anshi_count.py`
2. Embedding and clustering
   - `scripts/emopoem_get.py`
   - `scripts/embedding_get.py`
   - `scripts/kcluster.py`
3. Main experiment tables
   - `scripts/run_multilabel_baselines.py`
   - `scripts/run_api_word_stability.py`
   - `scripts/run_embedding_innovation_compare.py`
   - `scripts/run_ablation_quick.py`
   - `scripts/run_baselines_quick.py`
4. Compile paper
   - `tectonic --outdir build main.tex` (run inside `papers/acl_short_paper`)

## Expected Output Tables
- `outputs/tables/multilabel_baselines_18.json`
- `outputs/tables/api_word_prompt_a.jsonl`
- `outputs/tables/api_word_prompt_b.jsonl`
- `outputs/tables/api_word_stability_summary.json`
- `outputs/tables/embedding_innovation_compare.json`
- `outputs/tables/ablation_svm_quick.json`
- `outputs/tables/baseline_results_quick.json`
- `outputs/tables/year_poet_analysis_summary.json`
- `outputs/tables/interpretative_error_checks.json`
- `outputs/tables/svm_error_analysis_seed42.json`

## Notes
- Use the canonical annotated table as denominator for sentence and label statistics.
- Keep run logs with model version, prompt template version, decoding settings, random seed, and timestamp.
- Do not introduce synthetic/fabricated values when rerunning.
