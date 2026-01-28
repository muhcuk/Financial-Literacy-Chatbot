#!/usr/bin/env python3
"""Debug script to see normalized filenames."""

import re
from pathlib import Path

def normalize_filename(filename: str) -> str:
    """Normalize filename to match ARTICLE_URLS keys."""
    # Remove .jsonl extension
    name = filename.lower().replace(".jsonl", "").strip()
    # Remove (1), (2), etc. duplicates
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    # Replace spaces and hyphens with underscores
    name = name.replace(" ", "_").replace("-", "_")
    # Handle 'www_kwsp' patterns - extract the meaningful part
    if name.startswith("www"):
        # If it's just "www_kwsp_gov", keep it as is for generic mapping
        if name in ["www_kwsp", "www_kwsp_gov"]:
            return name
        # Otherwise remove www prefix and continue
        name = name.replace("www_", "").replace("www.", "")
    return name

files_to_check = [
    "kwsp_gov_my_w_article_50_30_20_rule.jsonl",
    "kwsp_gov_my_w_article_expenses_after_retired.jsonl",
    "kwsp_gov_my_w_article_why_medical_insurance_is_important.jsonl",
    "kwsp_gov_my_w_infographic_savings_tips_for_gig_workers.jsonl",
]

for f in files_to_check:
    normalized = normalize_filename(f)
    print(f"{f:60} -> {normalized}")
