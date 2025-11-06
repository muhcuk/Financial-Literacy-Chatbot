import os
import re
import json
import uuid
import time
import argparse
import pathlib
from typing import List
import pdfplumber
from tqdm import tqdm

try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

def read_pdf_text_pages(pdf_path: str, dpi: int = 300, ocr_threshold: int = 60) -> List[str]:
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(tqdm(pdf.pages, desc=f"Reading pages from {os.path.basename(pdf_path)}")):
            txt = (page.extract_text() or '').strip()
            if len(txt) < ocr_threshold and OCR_AVAILABLE:
                try:
                    images = convert_from_path(pdf_path, first_page=i + 1, last_page=i + 1, dpi=dpi)
                    if images:
                        txt = (pytesseract.image_to_string(images[0]) or '').strip()
                except Exception as e:
                    print(f"Warning: OCR failed on page {i+1} of {pdf_path}. Error: {e}")
            texts.append(txt)
    return texts

def clean_and_stitch_text(pages: List[str]) -> str:
    full_text = "\n\n".join(pages)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    full_text = re.sub(r"[ \t]{2,}", " ", full_text)
    full_text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", full_text)
    return full_text.strip()

def chunk_text(text: str, chunk_size: int = 1500, chunk_overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text): break
        start += chunk_size - chunk_overlap
    return [c.strip() for c in chunks if c.strip()]

def process_pdf(pdf_path: str, out_dir: str, chunk_size: int, chunk_overlap: int, ocr_threshold: int) -> str:
    pages = read_pdf_text_pages(pdf_path, ocr_threshold=ocr_threshold)
    if not pages: raise RuntimeError(f"No text extracted from {pdf_path}")
    full_text = clean_and_stitch_text(pages)
    if not full_text: raise RuntimeError(f"No text remained after cleaning {pdf_path}")
    chunks = chunk_text(full_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    doc_id = str(uuid.uuid4())
    title = pathlib.Path(pdf_path).stem.replace("_", " ").title()
    out_path = os.path.join(out_dir, f"{pathlib.Path(pdf_path).stem}.jsonl")
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for i, chunk_text in enumerate(chunks):
            record = {
                "id": str(uuid.uuid4()), "doc_id": doc_id, "title": title,
                "source_file": str(pdf_path), "chunk_index": i, "text": chunk_text,
                "created_at": time.strftime("%Y-%m-%d")
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return out_path

def main():
    parser = argparse.ArgumentParser(description="Process PDFs into chunked JSONL files.")
    parser.add_argument("--input_dir", required=True, help="Input folder with PDFs.")
    parser.add_argument("--output_dir", default="./data/chunks", help="Output folder for JSONL files.")
    parser.add_argument("--chunk_size", type=int, default=1500)
    parser.add_argument("--chunk_overlap", type=int, default=200)
    parser.add_argument("--ocr_threshold", type=int, default=60)
    args = parser.parse_args()
    pdf_paths = [os.path.join(args.input_dir, f) for f in os.listdir(args.input_dir) if f.lower().endswith(".pdf")]
    if not pdf_paths:
        print(f"No PDFs found in: {args.input_dir}")
        return
    print(f"Found {len(pdf_paths)} PDFs. OCR available: {OCR_AVAILABLE}")
    for pdf_path in tqdm(pdf_paths, desc="Processing PDFs"):
        try:
            out_path = process_pdf(pdf_path, args.output_dir, args.chunk_size, args.chunk_overlap, args.ocr_threshold)
            print(f"✅ Processed {os.path.basename(pdf_path)} -> {out_path}")
        except Exception as e:
            print(f"❌ Failed to process {os.path.basename(pdf_path)}: {e}")

if __name__ == "__main__":
    main()
