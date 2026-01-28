import os
import sys
import json
import argparse
from glob import glob
from pathlib import Path
from tqdm import tqdm

# Import pipeline helpers
from data_pipeline import pdf_processor, data_cleaner


def process_pdf_file(pdf_path: str, out_raw_dir: str, chunk_size: int, chunk_overlap: int, ocr_threshold: int):
    try:
        out_path = pdf_processor.process_pdf(pdf_path, out_raw_dir, chunk_size, chunk_overlap, ocr_threshold)
        lines = 0
        with open(out_path, "r", encoding="utf-8") as f:
            for _ in f:
                lines += 1
        return {"status": "ok", "raw_path": out_path, "chunks": lines}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def clean_jsonl(in_path: str, out_path: str):
    kept = 0
    original = 0
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(in_path, "r", encoding="utf-8") as fin, open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            original += 1
            try:
                obj = json.loads(line)
                text = data_cleaner.clean_text(obj.get("text", ""))
                if not text:
                    continue
                obj["text"] = text
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                kept += 1
            except json.JSONDecodeError:
                continue
    return {"original": original, "kept": kept}


def process_existing_jsonl(jsonl_path: str, out_clean_dir: str):
    stem = Path(jsonl_path).stem
    out_clean = os.path.join(out_clean_dir, f"{stem}.jsonl")
    stats = clean_jsonl(jsonl_path, out_clean)
    return {"status": "ok", "clean_path": out_clean, **stats}


def main():
    parser = argparse.ArgumentParser(description="Rerun data pipeline per-file and save per-file summaries.")
    parser.add_argument("--pdf_dir", default="pdfs", help="Folder with input PDFs")
    parser.add_argument("--jsonl_dir", default="data_chunks", help="Folder with existing JSONL files to (re)clean")
    parser.add_argument("--out_dir", default="data_pipeline/reruns_results", help="Output folder for per-file results")
    parser.add_argument("--chunk_size", type=int, default=1500)
    parser.add_argument("--chunk_overlap", type=int, default=200)
    parser.add_argument("--ocr_threshold", type=int, default=60)
    args = parser.parse_args()

    out_dir = args.out_dir
    raw_out = os.path.join(out_dir, "raw_outputs")
    clean_out = os.path.join(out_dir, "cleaned")
    summaries = os.path.join(out_dir, "summaries")
    os.makedirs(raw_out, exist_ok=True)
    os.makedirs(clean_out, exist_ok=True)
    os.makedirs(summaries, exist_ok=True)

    results = {"pdfs": {}, "jsonl": {}}

    # Process PDFs
    if os.path.isdir(args.pdf_dir):
        pdfs = [os.path.join(args.pdf_dir, f) for f in os.listdir(args.pdf_dir) if f.lower().endswith(".pdf")]
    else:
        pdfs = []

    if pdfs:
        print(f"Found {len(pdfs)} PDFs to process.")
    for pdf_path in tqdm(pdfs, desc="Processing PDFs"):
        name = Path(pdf_path).stem
        res = process_pdf_file(pdf_path, raw_out, args.chunk_size, args.chunk_overlap, args.ocr_threshold)
        # If raw JSONL produced, clean it
        if res.get("status") == "ok":
            raw_path = res["raw_path"]
            clean_stats = clean_jsonl(raw_path, os.path.join(clean_out, f"{name}.jsonl"))
            res["cleaned_path"] = os.path.join(clean_out, f"{name}.jsonl")
            res.update(clean_stats)
        results["pdfs"][name] = res
        # write per-file summary
        with open(os.path.join(summaries, f"{name}.json"), "w", encoding="utf-8") as sf:
            json.dump(res, sf, ensure_ascii=False, indent=2)

    # Process existing JSONL files
    jsonl_glob = glob(os.path.join(args.jsonl_dir, "*.jsonl"))
    for jpath in tqdm(jsonl_glob, desc="Cleaning existing JSONL files"):
        name = Path(jpath).stem
        try:
            res = process_existing_jsonl(jpath, clean_out)
        except Exception as e:
            res = {"status": "error", "error": str(e)}
        results["jsonl"][name] = res
        with open(os.path.join(summaries, f"{name}.json"), "w", encoding="utf-8") as sf:
            json.dump(res, sf, ensure_ascii=False, indent=2)

    # Write aggregated summary
    with open(os.path.join(out_dir, "aggregated_summary.json"), "w", encoding="utf-8") as af:
        json.dump(results, af, ensure_ascii=False, indent=2)

    print("Done. Per-file summaries saved to:", summaries)


if __name__ == "__main__":
    main()
