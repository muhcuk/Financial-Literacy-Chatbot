# How to Fix Chunks Metadata

## The Problem
When chunks are ingested into the vector database, the metadata doesn't have proper `source`, `title`, and `url` fields. This causes sources to display with wrong titles and default to the KWSP homepage.

## The Solution

### Step 1: Run the Metadata Fix Script
```bash
cd c:\Users\User10\Desktop\DEGREE\SEM 6\CSP 650
python fix_chunks_metadata.py --input-dir data_improved_chunks
# or, if you prefer the old folder
python fix_chunks_metadata.py --input-dir data_clean_chunks
```

This script will:
- Read all `.jsonl` files in `data_improved_chunks/` by default (or specify another folder via `--input-dir`)
- Match filenames to your `ARTICLE_URLS` mapping
- Add/update `metadata` fields in each chunk:
  - `source`: The filename (for matching)
  - `title`: The proper article title
  - `url`: The specific article URL
  - `from`: The company/source name

### Step 2: Rebuild the Vector Database
After updating the chunks, you need to rebuild the Chroma database:

```bash
# Delete old database
rmdir /s finance_db

# Re-ingest the updated chunks (default now reads data_improved_chunks)
python data_pipeline/database_builder.py --reset
# Or explicitly point to the folder
python data_pipeline/database_builder.py --input_glob "data_improved_chunks/*.jsonl" --reset
```

> **Note:** This will recreate `finance_db/` with all chunks and proper metadata.

### Step 3: Test the Chatbot
```bash
cd streamlit
streamlit run s_app.py
```

Now when you ask a question, the "View Sources" section will display:
```
[Article Title] (linked)
From: KWSP Malaysia
[Content preview...]
```

---

## What Gets Updated in Each Chunk

### Before:
```json
{
  "id": "...",
  "title": "Kwsp Gov My W Article Fomo Shopping",
  "source_file": "pdfs\\...",
  "text": "...",
  "created_at": "..."
}
```

### After:
```json
{
  "id": "...",
  "title": "Kwsp Gov My W Article Fomo Shopping",
  "source_file": "pdfs\\...",
  "metadata": {
    "source": "kwsp_gov_my_w_article_fomo_shopping.jsonl",
    "title": "FOMO Shopping",
    "url": "https://www.kwsp.gov.my/w/article/fomo-shopping",
    "from": "KWSP Malaysia"
  },
  "text": "...",
  "created_at": "..."
}
```

---

## Adding New Articles to the Mapping

If you add new chunks that aren't in the `ARTICLE_URLS` mapping:

1. Edit `fix_chunks_metadata.py`
2. Add entry to `ARTICLE_URLS` dictionary:
   ```python
   "your_article_name": {
       "title": "Your Article Title",
       "url": "https://www.example.com/your-article",
       "company": "Source Company Name"
   }
   ```
3. Run the script again
4. Rebuild the database

---

## Troubleshooting

**Problem:** Script says "No mapping found for: xxx.jsonl"
- **Solution:** Add the mapping to `ARTICLE_URLS` in the script

**Problem:** Chunks still show wrong source after re-ingesting
- **Solution:** Make sure you deleted the old `finance_db/` before re-ingesting

**Problem:** Some URLs still point to KWSP homepage
- **Solution:** Check the `get_article_info()` function in `s_app.py` is working correctly. It falls back to homepage only if source name isn't found.
