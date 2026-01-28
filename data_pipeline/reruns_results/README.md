This folder contains results produced by `rerun_pipeline.py`.

Usage:

- From workspace root run:

```bash
python data_pipeline/rerun_pipeline.py --pdf_dir pdfs --jsonl_dir data_chunks --out_dir data_pipeline/reruns_results
```

- The script will:
  - Process each PDF in `--pdf_dir` (via `pdf_processor.process_pdf`) producing per-PDF raw JSONL in `out_dir/raw_outputs`.
  - Clean each JSONL (via `data_cleaner.clean_text`) saving cleaned files to `out_dir/cleaned`.
  - Produce a per-file summary JSON in `out_dir/summaries` with counts and any errors.

Notes:
- This script avoids heavy optional steps (embeddings/Chroma). It focuses on extraction + cleaning and per-file summaries.
- Adjust `--chunk_size` and `--chunk_overlap` to match your pipeline if needed.
