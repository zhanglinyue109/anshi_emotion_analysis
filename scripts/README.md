# scripts

本目录放置可直接执行的实验脚本入口。

## 主流程

```bash
python scripts/anshi.py
python scripts/annotate.py
python scripts/anshi_count.py
python scripts/emopoem_get.py
python scripts/embedding_get.py
python scripts/kcluster.py
```

## 说明

1. 多数脚本来自历史实验，部分仍使用硬编码路径与配置。
2. 建议后续统一改造成 CLI 参数（`--input`、`--output`、`--config`）。
3. 可复用模型逻辑已迁移至 `src/`。
