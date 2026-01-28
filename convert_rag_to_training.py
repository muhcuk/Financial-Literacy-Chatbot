"""
Convert RAG chunks from data_improved_chunks to fine-tuning format for Ollama.
Improved version with better content filtering and more relevant Q&A generation.
"""

import json
import os
import glob
import random
import re
from pathlib import Path

# Input/Output directories
INPUT_DIR = "data_improved_chunks"
OUTPUT_DIR = "train_model"

# Skip these files (not suitable for personal finance training)
SKIP_FILES = [
    "Financial Fraud Prevention and Detection",  # Too technical/corporate
]

# Topic-specific question templates
TOPIC_QA_TEMPLATES = {
    "50/30/20": [
        ("What is the 50/30/20 budgeting rule?", None),
        ("How do I apply the 50/30/20 rule?", None),
        ("How should I divide my salary using the 50/30/20 rule?", None),
        ("Can you give an example of 50/30/20 budgeting?", None),
        ("What percentage of my income should go to savings?", None),
    ],
    "savings": [
        ("How can I start saving money?", None),
        ("What is 'pay yourself first'?", None),
        ("How much should I save each month?", None),
        ("What is an emergency fund?", None),
        ("How do I build an emergency fund?", None),
        ("Why is saving important for young adults?", None),
        ("How can I save money on a low salary?", None),
    ],
    "budget": [
        ("How do I create a budget?", None),
        ("What are some budgeting tips?", None),
        ("How can I track my expenses?", None),
        ("How do I stick to my budget?", None),
        ("What are common budgeting mistakes?", None),
        ("How can I budget on a RM2000 salary?", None),
    ],
    "debt": [
        ("How can I avoid getting into debt?", None),
        ("What should I know about credit cards?", None),
        ("How do I pay off my debts?", None),
        ("What is the debt snowball method?", None),
        ("Is BNPL (Buy Now Pay Later) a good idea?", None),
        ("How do young Malaysians get into debt?", None),
    ],
    "investment": [
        ("How does compound interest work?", None),
        ("When should I start investing?", None),
        ("What are basic investment options in Malaysia?", None),
        ("What is EPF/KWSP?", None),
        ("How can compound interest help me build wealth?", None),
    ],
    "retirement": [
        ("How do I plan for retirement?", None),
        ("What habits help with early retirement?", None),
        ("How much do I need for retirement in Malaysia?", None),
        ("What expenses should I expect after retirement?", None),
    ],
    "tax": [
        ("How do I file income tax in Malaysia?", None),
        ("What tax deductions can I claim?", None),
        ("When is the tax filing deadline in Malaysia?", None),
        ("What is LHDN and how do I use it?", None),
    ],
    "insurance": [
        ("Why is medical insurance important?", None),
        ("What types of insurance should I have?", None),
        ("How do I choose the right insurance?", None),
        ("What insurance do young adults need?", None),
    ],
    "car": [
        ("Should I buy a new or used car?", None),
        ("How do I budget for a car purchase?", None),
        ("What should I know about car loans?", None),
        ("Tips for buying my first car in Malaysia?", None),
    ],
    "house": [
        ("Should I buy or rent a house in Malaysia?", None),
        ("How do I save for a house down payment?", None),
        ("What should first-time homebuyers know?", None),
        ("What are the costs of owning a home?", None),
    ],
    "scam": [
        ("How can I avoid financial scams?", None),
        ("What are common online scams to watch for?", None),
        ("How do I protect myself from fraud?", None),
    ],
    "first_salary": [
        ("What should I do with my first salary?", None),
        ("How should fresh graduates manage their money?", None),
        ("What financial mistakes do young adults make?", None),
        ("Tips for managing money in my 20s?", None),
    ],
    "mindset": [
        ("How does mindset affect financial success?", None),
        ("What is financial freedom?", None),
        ("How can I change my money mindset?", None),
    ],
    "gig_worker": [
        ("How should gig workers manage their finances?", None),
        ("What savings tips are there for freelancers?", None),
    ],
    "general": [
        ("What financial advice do you have for Malaysian youth?", None),
        ("How can I be better with money?", None),
        ("What are the basics of personal finance?", None),
    ],
}

# Keywords to identify topics in text
TOPIC_KEYWORDS = {
    "50/30/20": ["50/30/20", "50-30-20", "50 30 20", "budgeting rule", "50% for needs", "30% for wants", "20% for savings"],
    "savings": ["saving", "emergency fund", "savings account", "pay yourself first", "save money", "savings cushion", "start saving"],
    "budget": ["budget", "expense", "spending", "money management", "track your", "financial plan", "income allocation"],
    "debt": ["debt", "credit card", "loan", "bnpl", "buy now pay later", "repayment", "borrow", "owing money"],
    "investment": ["invest", "compound interest", "grow your money", "returns", "portfolio", "wealth building"],
    "retirement": ["retirement", "retire", "epf", "kwsp", "pension", "after retirement"],
    "tax": ["tax", "lhdn", "income tax", "tax relief", "tax deduction", "filing", "pcb"],
    "insurance": ["insurance", "medical cover", "protection", "policy", "coverage", "insured"],
    "car": ["car", "vehicle", "automobile", "car loan", "car financing", "first car"],
    "house": ["house", "home", "property", "housing loan", "buy vs rent", "homeowner", "mortgage"],
    "scam": ["scam", "fraud", "phishing", "trick", "con", "suspicious", "deceive"],
    "first_salary": ["first salary", "fresh graduate", "first job", "young adult", "starting work", "first paycheck"],
    "mindset": ["mindset", "financial freedom", "wealth mindset", "money mindset", "attitude", "discipline"],
    "gig_worker": ["gig worker", "freelancer", "self-employed", "gig economy", "side hustle"],
}

def should_skip_file(filename: str) -> bool:
    """Check if file should be skipped."""
    for skip in SKIP_FILES:
        if skip.lower() in filename.lower():
            return True
    return False


def clean_text(text: str) -> str:
    """Clean up chunk text for better responses."""
    # Remove navigation/menu items
    skip_patterns = [
        r"Member Employer Corporate.*?(?=\n\n|\Z)",
        r"Table of Contents.*?(?=\n\n|\Z)",
        r"Related Reads.*?(?=\n\n|\Z)",
        r"Terms & Conditions.*",
        r"Privacy Policy.*",
        r"Contact Us.*",
        r"Disclaimer:.*",
        r"HOUSING\n.*?(?=\n\n)",
        r"ACCOUNT\n.*?(?=\n\n)",
        r"PERSONAL\nFINANCE\n.*?(?=\n\n)",
        r"EPF\n.*?(?=\n\n)",
        r"EN\n.*?Myra Athena",
    ]
    
    for pattern in skip_patterns:
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()


def extract_good_sentences(text: str, min_length: int = 40) -> list:
    """Extract good, informative sentences from text."""
    # Split by sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    good = []
    for s in sentences:
        s = s.strip()
        # Filter criteria
        if len(s) < min_length:
            continue
        if len(s) > 400:
            continue
        # Skip menu/navigation-like content
        skip_words = ["Click here", "Read also", "Table of Contents", "Terms &", 
                      "Member Employer", "Related Reads", "Date:", "Myra Athena"]
        if any(x in s for x in skip_words):
            continue
        # Skip if mostly uppercase (headers)
        if sum(1 for c in s if c.isupper()) / max(len(s), 1) > 0.4:
            continue
        good.append(s)
    
    return good


def identify_topic(text: str) -> str:
    """Identify the main topic of text."""
    text_lower = text.lower()
    
    # Count keyword matches for each topic
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[topic] = score
    
    if scores:
        return max(scores, key=scores.get)
    return "general"


def create_qa_pairs_from_chunk(chunk: dict, filename: str) -> list:
    """Generate Q&A pairs from a single chunk."""
    text = chunk.get("text", "")
    
    if not text or len(text) < 150:
        return []
    
    # Clean the text
    text = clean_text(text)
    if len(text) < 100:
        return []
    
    # Get good sentences
    sentences = extract_good_sentences(text)
    if len(sentences) < 2:
        return []
    
    # Identify topic
    topic = identify_topic(text)
    
    qa_pairs = []
    
    # Get templates for this topic
    templates = TOPIC_QA_TEMPLATES.get(topic, TOPIC_QA_TEMPLATES["general"])
    
    # Create response from sentences
    response_sentences = sentences[:5]
    response_text = " ".join(response_sentences)
    
    # Make sure response is meaningful
    if len(response_text) < 80:
        return []
    
    # Select 1-2 random templates
    num_to_use = min(2, len(templates))
    selected = random.sample(templates, num_to_use)
    
    for question, preset_answer in selected:
        answer = preset_answer if preset_answer else response_text
        
        qa_pairs.append({
            "prompt": question,
            "completion": answer,
            "topic": topic,
            "source": filename
        })
    
    return qa_pairs


def create_chat_format(qa_pair: dict) -> dict:
    """Convert to Llama chat format."""
    return {
        "messages": [
            {"role": "user", "content": qa_pair["prompt"]},
            {"role": "assistant", "content": qa_pair["completion"]}
        ]
    }


def create_instruction_format(qa_pair: dict) -> dict:
    """Convert to Alpaca instruction format."""
    return {
        "instruction": qa_pair["prompt"],
        "input": "",
        "output": qa_pair["completion"]
    }


def process_all_chunks():
    """Process all JSONL files and generate training data."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_qa_pairs = []
    input_pattern = os.path.join(INPUT_DIR, "*.jsonl")
    files = glob.glob(input_pattern)
    
    print(f"Found {len(files)} JSONL files in {INPUT_DIR}")
    
    for filepath in files:
        filename = os.path.basename(filepath)
        
        if should_skip_file(filename):
            print(f"Skipping: {filename}")
            continue
            
        print(f"Processing: {filename}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        chunk = json.loads(line)
                        qa_pairs = create_qa_pairs_from_chunk(chunk, filename)
                        all_qa_pairs.extend(qa_pairs)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\nGenerated {len(all_qa_pairs)} Q&A pairs")
    
    # Group by topic for stats
    topic_counts = {}
    for pair in all_qa_pairs:
        topic = pair.get("topic", "general")
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    print("\nTopic distribution:")
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"  {topic}: {count}")
    
    # Shuffle
    random.shuffle(all_qa_pairs)
    
    # Remove duplicates based on prompt + first 100 chars of completion
    seen = set()
    unique_pairs = []
    for pair in all_qa_pairs:
        key = (pair["prompt"], pair["completion"][:100])
        if key not in seen:
            seen.add(key)
            unique_pairs.append(pair)
    
    print(f"\nAfter deduplication: {len(unique_pairs)} unique pairs")
    
    # Save files
    
    # 1. Chat format (recommended for Ollama)
    chat_file = os.path.join(OUTPUT_DIR, "finance_chat.jsonl")
    with open(chat_file, 'w', encoding='utf-8') as f:
        for pair in unique_pairs:
            f.write(json.dumps(create_chat_format(pair), ensure_ascii=False) + "\n")
    print(f"\nSaved: {chat_file}")
    
    # 2. Instruction format
    instruction_file = os.path.join(OUTPUT_DIR, "finance_instruction.jsonl")
    with open(instruction_file, 'w', encoding='utf-8') as f:
        for pair in unique_pairs:
            f.write(json.dumps(create_instruction_format(pair), ensure_ascii=False) + "\n")
    print(f"Saved: {instruction_file}")
    
    # 3. Simple format
    simple_file = os.path.join(OUTPUT_DIR, "finance_simple.jsonl")
    with open(simple_file, 'w', encoding='utf-8') as f:
        for pair in unique_pairs:
            f.write(json.dumps({"prompt": pair["prompt"], "completion": pair["completion"]}, ensure_ascii=False) + "\n")
    print(f"Saved: {simple_file}")
    
    print(f"\n✅ Training data ready!")
    print(f"\n=== Next Steps to Fine-Tune Your Model ===")
    print("Option 1: Using Unsloth (Recommended, free on Google Colab)")
    print("  1. Upload finance_chat.jsonl to Google Drive")
    print("  2. Use Unsloth notebook to fine-tune Llama/Qwen")
    print("  3. Export as GGUF and import to Ollama")
    print("")
    print("Option 2: Using LlamaFactory")
    print("  1. Install LlamaFactory: pip install llamafactory")
    print("  2. Configure training with finance_instruction.jsonl")
    print("")
    print("Option 3: Create new Ollama model with better system prompt")
    print("  1. Run: ollama create my-finetuned-v2 -f train_model/Modelfile")
    
    return unique_pairs


if __name__ == "__main__":
    process_all_chunks()
