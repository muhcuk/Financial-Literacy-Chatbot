import json
import os
from pathlib import Path

def clean_redundancy(text):
    """Remove redundant text that appears at chunk boundaries"""
    lines = text.split('\n')
    if len(lines) < 2:
        return text
    
    # Join lines for processing
    clean_text = ' '.join(lines)
    # Remove multiple spaces
    while '  ' in clean_text:
        clean_text = clean_text.replace('  ', ' ')
    
    return clean_text.strip()

def process_jsonl_file(file_path):
    """Process a single JSONL file to remove redundancies"""
    try:
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    records.append(record)
        
        # Check for redundancy between consecutive chunks
        for i in range(len(records) - 1):
            current_text = records[i].get('text', '')
            next_text = records[i + 1].get('text', '')
            
            if current_text and next_text:
                # Find overlapping text at boundaries
                # Check if start of next chunk is in end of current chunk
                current_end = current_text[-200:] if len(current_text) > 200 else current_text
                next_start = next_text[:200] if len(next_text) > 200 else next_text
                
                # Look for redundant sentences
                current_words = current_end.split()
                next_words = next_start.split()
                
                # Find overlap
                overlap_len = 0
                for j in range(1, min(len(current_words), len(next_words)) + 1):
                    if current_words[-j] == next_words[0]:
                        # Found potential overlap, extend it
                        matches = True
                        for k in range(1, j):
                            if current_words[-(j-k)] != next_words[k]:
                                matches = False
                                break
                        if matches:
                            overlap_len = j
                
                # Remove overlap from next chunk
                if overlap_len > 0:
                    overlap_text = ' '.join(next_words[:overlap_len])
                    # Remove from start of next text
                    if next_text.startswith(overlap_text):
                        records[i + 1]['text'] = next_text[len(overlap_text):].lstrip()
                    else:
                        # Try to find and remove the overlapping portion more flexibly
                        for start_idx in range(len(next_text) - len(overlap_text)):
                            if overlap_text in next_text[start_idx:start_idx + len(overlap_text) + 50]:
                                end_idx = start_idx + len(overlap_text)
                                records[i + 1]['text'] = (next_text[:start_idx] + next_text[end_idx:]).strip()
                                break
        
        # Write cleaned records back
        with open(file_path, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    folder_path = r"c:\Users\User10\Desktop\DEGREE\SEM 6\CSP 650\data_clean_chunks(1)"
    
    files_processed = 0
    files_failed = 0
    
    for file_path in Path(folder_path).glob('*.jsonl'):
        print(f"Processing: {file_path.name}...", end=" ")
        if process_jsonl_file(str(file_path)):
            files_processed += 1
            print("✓")
        else:
            files_failed += 1
            print("✗")
    
    print(f"\n\nSummary:")
    print(f"Files processed successfully: {files_processed}")
    print(f"Files failed: {files_failed}")

if __name__ == "__main__":
    main()
