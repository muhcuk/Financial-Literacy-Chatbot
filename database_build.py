#This patch must be at the very top of the file
import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import json
import argparse
import hashlib
from glob import glob
from typing import List, Dict, Any
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# ... (the rest of the file remains the same) ...
def load_and_prepare_docs(glob_path: str) -> List[Document]:
    docs: List[Document] = []
    files = glob(glob_path)
    if not files: raise FileNotFoundError(f"No JSONL files found at: {glob_path}")
    print(f"Found {len(files)} JSONL files...")
    for file_path in tqdm(files, desc="Loading documents"):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    text = data.get("text")
                    if not text: continue
                    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
                    metadata: Dict[str, Any] = data.copy()
                    metadata["content_hash"] = h
                    docs.append(Document(page_content=text, metadata=metadata))
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Skipping malformed line in {file_path}: {e}")
    return docs

def main():
    parser = argparse.ArgumentParser(description="Build ChromaDB from cleaned JSONL data.")
    parser.add_argument("--input_glob", default="data/clean_chunks/*.jsonl")
    parser.add_argument("--persist_dir", default="./finance_db")
    parser.add_argument("--collection", default="finance_knowledge")
    parser.add_argument("--model_name", default="intfloat/multilingual-e5-small")
    parser.add_argument("--reset", action="store_true", help="Reset the existing database.")
    args = parser.parse_args()

    try:
        docs = load_and_prepare_docs(args.input_glob)
        if not docs:
            print("No valid documents found.")
            return
        print(f"📚 Loaded {len(docs)} document chunks.")
    except FileNotFoundError as e:
        print(f"Error: {e}. Run processing scripts first.")
        return

    embeddings = HuggingFaceEmbeddings(model_name=args.model_name)
    db = Chroma(collection_name=args.collection, embedding_function=embeddings, persist_directory=args.persist_dir)

    if args.reset:
        print(f"🗑️ Resetting collection: {args.collection}")
        db.delete_collection()
        db = Chroma.from_documents(docs, embeddings, collection_name=args.collection, persist_directory=args.persist_dir)
        print(f"✅ Created new collection with {len(docs)} documents.")
    else:
        existing_hashes = {meta["content_hash"] for meta in db.get(include=["metadatas"]).get("metadatas", []) if meta and "content_hash" in meta}
        new_docs = [doc for doc in docs if doc.metadata.get("content_hash") not in existing_hashes]
        if not new_docs:
            print("✅ No new documents to add.")
            return
        print(f"➕ Found {len(new_docs)} new documents to add.")
        db.add_documents(new_docs)
        print(f"✅ Added {len(new_docs)} new documents.")
    print("\n🎉 Ingestion complete.")

if __name__ == "__main__":
    main()
