#!/usr/bin/env python3
"""
Script to fix metadata in JSONL chunk files to match ARTICLE_URLS mapping.
This ensures sources display correctly in the chatbot.
"""

import json
import os
from pathlib import Path
import sys
import argparse

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Mapping from filename patterns to proper titles and URLs
ARTICLE_URLS = {
    "smart_budgeting_technique": {
        "title": "Smart Budgeting Technique",
        "url": "https://www.kwsp.gov.my/w/infographic/smart-budgeting-technique",
        "company": "KWSP Malaysia"
    },
    "first_salary_tips": {
        "title": "First Salary Tips",
        "url": "https://www.kwsp.gov.my/w/article/first-salary-tips",
        "company": "KWSP Malaysia"
    },
    "travelling_green_tips": {
        "title": "Travelling Green Tips",
        "url": "https://www.kwsp.gov.my/w/article/travelling-green-tips",
        "company": "KWSP Malaysia"
    },
    "insurance_tips": {
        "title": "Insurance Tips",
        "url": "https://www.kwsp.gov.my/w/infographic/insurance-tips",
        "company": "KWSP Malaysia"
    },
    "saving_tips_for_gig_worker": {
        "title": "Savings Tips for Gig Workers",
        "url": "https://www.kwsp.gov.my/w/infographic/savings-tips-for-gig-workers",
        "company": "KWSP Malaysia"
    },
    "death_assistance": {
        "title": "EPF Death Assistance",
        "url": "https://www.kwsp.gov.my/w/article/epf-death-assistance",
        "company": "KWSP Malaysia"
    },
    "multiple_savings_with_i_saraan": {
        "title": "Multiply Savings with i-Saraan",
        "url": "https://www.kwsp.gov.my/w/infographic/multiply-savings-with-i-saraan",
        "company": "KWSP Malaysia"
    },
    "expense_after_retired": {
        "title": "Expenses After Retirement",
        "url": "https://www.kwsp.gov.my/w/article/expenses-after-retired",
        "company": "KWSP Malaysia"
    },
    "fomo_shopping": {
        "title": "FOMO Shopping",
        "url": "https://www.kwsp.gov.my/w/article/fomo-shopping",
        "company": "KWSP Malaysia"
    },
    "why_medical_insurance_importance": {
        "title": "Why Medical Insurance is Important",
        "url": "https://www.kwsp.gov.my/w/article/why-medical-insurance-is-important",
        "company": "KWSP Malaysia"
    },
    "buy_vs_rent": {
        "title": "Buy vs Rent Malaysia",
        "url": "https://www.kwsp.gov.my/w/article/buy-vs-rent-malaysia",
        "company": "KWSP Malaysia"
    },
    "fashion_on_a_budget": {
        "title": "Fashion on a Budget",
        "url": "https://www.kwsp.gov.my/w/article/fashion-on-a-budget",
        "company": "KWSP Malaysia"
    },
    "budgeting_rule": {
        "title": "50-30-20 Rule",
        "url": "https://www.kwsp.gov.my/w/article/50-30-20-rule",
        "company": "KWSP Malaysia"
    },
    "file_income_tax": {
        "title": "How to File Income Tax",
        "url": "https://www.kwsp.gov.my/w/article/how-to-file-income-tax",
        "company": "KWSP Malaysia"
    },
    "compound_interest_benefits": {
        "title": "Compound Interest Benefits",
        "url": "https://www.kwsp.gov.my/w/article/compound-interest-benefits",
        "company": "KWSP Malaysia"
    },
    "pay_yourself_first": {
        "title": "Pay Yourself First",
        "url": "https://www.kwsp.gov.my/w/article/pay-yourself-first",
        "company": "KWSP Malaysia"
    },
    "new_year_financial_goals": {
        "title": "New Year Financial Goals",
        "url": "https://www.kwsp.gov.my/w/article/new-year-financial-goals",
        "company": "KWSP Malaysia"
    },
    "master_your_finance": {
        "title": "Master Your Finance",
        "url": "https://www.kwsp.gov.my/w/article/master-your-finance",
        "company": "KWSP Malaysia"
    },
    "quick_ways_to_losing_savings": {
        "title": "Quick Ways to Lose Savings",
        "url": "https://www.kwsp.gov.my/w/article/quick-ways-to-lose-savings",
        "company": "KWSP Malaysia"
    },
    "surviving_on_paycheck": {
        "title": "Surviving on Paycheck",
        "url": "https://www.kwsp.gov.my/w/article/surviving-on-paycheck",
        "company": "KWSP Malaysia"
    },
    "scam_red_flags": {
        "title": "Scam Red Flags",
        "url": "https://www.kwsp.gov.my/w/article/scam-red-flags",
        "company": "KWSP Malaysia"
    },
    "vacation_on_budget": {
        "title": "Vacation on Budget",
        "url": "https://www.kwsp.gov.my/w/article/vacation-on-budget",
        "company": "KWSP Malaysia"
    },
    "save_money_malaysian_ways": {
        "title": "Save Money Malaysian Ways",
        "url": "https://www.kwsp.gov.my/w/article/save-money-malaysian-ways",
        "company": "KWSP Malaysia"
    },
    "financial_independence": {
        "title": "Financial Independence",
        "url": "https://www.kwsp.gov.my/w/article/financial-independence",
        "company": "KWSP Malaysia"
    },
    "how_to_avoid_online_scam": {
        "title": "How to Avoid Online Scam",
        "url": "https://www.kwsp.gov.my/w/article/how-to-avoid-online-scam",
        "company": "KWSP Malaysia"
    },
    "buy_first_think_later": {
        "title": "Buy First Think Later",
        "url": "https://www.kwsp.gov.my/w/article/buy-first-think-later",
        "company": "KWSP Malaysia"
    },
    "income_and_your_savings": {
        "title": "Income and Your Savings",
        "url": "https://www.kwsp.gov.my/w/article/income-and-your-savings",
        "company": "KWSP Malaysia"
    },
    "retirement_planning_tips": {
        "title": "Retirement Planning Tips",
        "url": "https://www.kwsp.gov.my/w/article/retirement-planning-tips",
        "company": "KWSP Malaysia"
    },
    "savings_and_inflation": {
        "title": "Savings and Inflation",
        "url": "https://www.kwsp.gov.my/w/article/savings-and-inflation",
        "company": "KWSP Malaysia"
    },
    "achieve_money_goals": {
        "title": "Achieve Money Goals",
        "url": "https://www.kwsp.gov.my/w/article/achieve-money-goal",
        "company": "KWSP Malaysia"
    },
    "how_to_use_akaun_3": {
        "title": "How to Use Akaun 3",
        "url": "https://www.kwsp.gov.my/w/article/how-to-use-akaun-3",
        "company": "KWSP Malaysia"
    },
    "saving_for_festives": {
        "title": "Savings for Festives",
        "url": "https://www.kwsp.gov.my/w/article/savings-for-festives",
        "company": "KWSP Malaysia"
    },
    "shariah_retirement": {
        "title": "Simpanan Shariah Retirement",
        "url": "https://www.kwsp.gov.my/w/article/simpanan-shariah-retirement",
        "company": "KWSP Malaysia"
    },
    "invest_smarter": {
        "title": "Invest Smarter",
        "url": "https://www.kwsp.gov.my/w/article/invest-smarter",
        "company": "KWSP Malaysia"
    },
    "retirement_calculator": {
        "title": "Retirement Calculator",
        "url": "https://www.kwsp.gov.my/w/article/retirement-calculator",
        "company": "KWSP Malaysia"
    },
    "ensuring_wife_future": {
        "title": "Ensuring Wife Future",
        "url": "https://www.kwsp.gov.my/w/article/ensuring-wife-future",
        "company": "KWSP Malaysia"
    },
    "epf_house": {
        "title": "EPF Housing Withdrawal",
        "url": "https://www.kwsp.gov.my/w/article/epf-housing-withdrawal",
        "company": "KWSP Malaysia"
    },
    "emergency_fund": {
        "title": "Emergency Fund",
        "url": "https://www.kwsp.gov.my/w/article/emergency-fund",
        "company": "KWSP Malaysia"
    },
    "reward_yourself": {
        "title": "Reward Yourself",
        "url": "https://www.kwsp.gov.my/w/article/reward-yourself",
        "company": "KWSP Malaysia"
    },
    "unwise_spending_habits": {
        "title": "Unwise Spending Habits",
        "url": "https://www.kwsp.gov.my/w/article/unwise-spending-habits",
        "company": "KWSP Malaysia"
    },
    "boost_your_savings": {
        "title": "Boost Your Savings",
        "url": "https://www.kwsp.gov.my/w/article/boost-your-savings",
        "company": "KWSP Malaysia"
    },
    "reasons_to_save_money": {
        "title": "Reasons to Save Money",
        "url": "https://www.kwsp.gov.my/w/article/reasons-to-save-money",
        "company": "KWSP Malaysia"
    },
    # KWSP articles with full filename keys
    "kwsp_gov_my_w_article_50_30_20_rule": {
        "title": "50-30-20 Rule",
        "url": "https://www.kwsp.gov.my/w/article/50-30-20-rule",
        "company": "KWSP Malaysia"
    },
    "kwsp_gov_my_w_article_expenses_after_retired": {
        "title": "Expenses After Retirement",
        "url": "https://www.kwsp.gov.my/w/article/expenses-after-retired",
        "company": "KWSP Malaysia"
    },
    "kwsp_gov_my_w_article_why_medical_insurance_is_important": {
        "title": "Why Medical Insurance is Important",
        "url": "https://www.kwsp.gov.my/w/article/why-medical-insurance-is-important",
        "company": "KWSP Malaysia"
    },
    "kwsp_gov_my_w_infographic_savings_tips_for_gig_workers": {
        "title": "Savings Tips for Gig Workers",
        "url": "https://www.kwsp.gov.my/w/infographic/savings-tips-for-gig-workers",
        "company": "KWSP Malaysia"
    },
    # Educational frameworks
    "educational_methodologies_of_personal_finance": {
        "title": "Educational Methodologies of Personal Finance",
        "url": "https://www.financialeducatorscouncil.org/wp-content/uploads/Educational-Methodologies-of-Personal-Finance.pdf",
        "company": "Educational Resource"
    },
    "flcc_for_malaysian_adults_compressed": {
        "title": "Financial Literacy for Malaysian Adults",
        "url": "https://www.fenetwork.my/wp-content/uploads/2023/02/Financial-Literacy-Core-Competencies-for-Malaysian-Adults.pdf",
        "company": "Educational Resource"
    },
    "framework_for_teaching_personal_finance": {
        "title": "Framework for Teaching Personal Finance",
        "url": "https://www.financialeducatorscouncil.org/wp-content/uploads/Framework-for-Teaching-Personal-Finance.pdf",
        "company": "Educational Resource"
    },
    "learner_framework_standards_for_high_school_college_adults": {
        "title": "Learner Framework Standards for Financial Literacy",
        "url": "https://www.financialeducatorscouncil.org/wp-content/uploads/DOC_PKG_EXC_-NFEC-Learner-Framework-Standards-for-High-School-College-Adults-_3.4.09.pdf",
        "company": "Educational Resource"
    },
    "nfec_report_policy_and_standards_framework_for_high_school_financial_literacy_education": {
        "title": "NFEC: Policy and Standards Framework for Financial Literacy",
        "url": "https://www.financialeducatorscouncil.org/wp-content/uploads/nfec-report-policy-and-standards-framework-for-high-school-financial-literacy-education.pdf",
        "company": "Educational Resource"
    },
    "smart_technique_an_easy_way_to_achieve_financial_goals_kwsp_malaysia": {
        "title": "S.M.A.R.T Technique: Achieve Financial Goals",
        "url": "https://www.kwsp.gov.my/en/w/infographic/smart-budgeting-technique",
        "company": "KWSP Malaysia"
    },
    # Files with special characters - map by exact filename
    "5 mistakes young adult make with money — lalua rahsiad.jsonl": {
        "title": "5 Mistakes Young Adults Make With Money",
        "url": "https://www.laluarahsiad.com/blog-2/blog2",
        "company": "Lalua Rahsiad"
    },
    "what no one tells you about budgeting in your 20s — lalua rahsiad.jsonl": {
        "title": "What No One Tells You About Budgeting in Your 20s",
        "url": "https://www.laluarahsiad.com/blog-2/blog3",
        "company": "Lalua Rahsiad"
    },
    "why financial freedom starts with your mindset — lalua rahsiad.jsonl": {
        "title": "Why Financial Freedom Starts with Your Mindset",
        "url": "https://www.laluarahsiad.com/blog-2/blog1",
        "company": "Lalua Rahsiad"
    },
    "how to celebrate deepavali without overspending - kwsp malaysia.jsonl": {
        "title": "Celebrate Deepavali Without Overspending",
        "url": "https://www.kwsp.gov.my/en/w/article/celebrate-deepavali-without-overspending",
        "company": "KWSP Malaysia"
    },
    "article 4 (digital financial).jsonl": {
        "title": "Digital Financial Management",
        "url": "https://www.akpk.org.my/sites/default/files/2024-12/ARTICLE%204%20%28DIGITAL%20FINANCIAL%29.pdf",
        "company": "AKPK Malaysia"
    },
    "article 6 (getting into debt).jsonl": {
        "title": "Getting Into Debt: What You Need to Know",
        "url": "https://www.akpk.org.my/sites/default/files/2025-02/ARTICLE%206%20%28GETTING%20INTO%20DEBT%29.pdf",
        "company": "AKPK Malaysia"
    },
    "article 8 (breaking the chains).jsonl": {
        "title": "Breaking the Chains of Debt",
        "url": "https://www.akpk.org.my/sites/default/files/2025-02/ARTICLE%208%20%28BREAKING%20THE%20CHAINS%29.pdf",
        "company": "AKPK Malaysia"
    },
    "s.m.a.r.t technique_ an easy way to achieve financial goals - kwsp malaysia.jsonl": {
        "title": "S.M.A.R.T Technique: Achieve Financial Goals",
        "url": "https://www.kwsp.gov.my/en/w/infographic/smart-budgeting-technique",
        "company": "KWSP Malaysia"
    },
    "financial fraud prevention and detection_ governance and effective practices ( pdfdrive ).jsonl": {
        "title": "Financial Fraud Prevention and Detection",
        "url": "https://www.wiley.com/en-us/Financial+Fraud+Prevention+and+Detection%3A+Governance+and+Effective+Practices-p-9781118617632",
        "company": "Financial Resource"
    },
    # Generic/Additional articles from www_kwsp.gov files
    "www_kwsp.gov": {
        "title": "BNPL: Buy Now Pay Later",
        "url": "https://www.kwsp.gov.my/w/article/buy-now-pay-later",
        "company": "KWSP Malaysia"
    },
    "buying_first_car": {
        "title": "Buying Your First Car",
        "url": "https://www.kwsp.gov.my/w/article/buying-first-car",
        "company": "KWSP Malaysia"
    },
    "early_retirement_habits": {
        "title": "Early Retirement Habits",
        "url": "https://www.kwsp.gov.my/w/article/early-retirement-habits",
        "company": "KWSP Malaysia"
    }
}


def normalize_filename(filename: str) -> str:
    """Normalize filename to match ARTICLE_URLS keys."""
    # Remove .jsonl extension
    name = filename.lower().replace(".jsonl", "").strip()
    # Remove (1), (2), etc. duplicates
    import re
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


def find_article_info(filename: str):
    """Find article info based on filename."""
    normalized = normalize_filename(filename)
    
    # Try exact match first
    if normalized in ARTICLE_URLS:
        return ARTICLE_URLS[normalized]
    
    # Try exact filename match (for special characters)
    if filename.lower() in ARTICLE_URLS:
        return ARTICLE_URLS[filename.lower()]
    
    # Try partial match with both underscore and hyphen variants
    normalized_hyphen = normalized.replace("_", "-")
    
    for key, value in ARTICLE_URLS.items():
        key_hyphen = key.replace("_", "-")
        # Check if normalized or its hyphen variant matches
        if (key in normalized or normalized in key or 
            key_hyphen in normalized_hyphen or normalized_hyphen in key_hyphen):
            return value
    
    return None


def update_chunk_file(filepath: str):
    """Update metadata in a single JSONL file."""
    filename = Path(filepath).name
    article_info = find_article_info(filename)
    
    if not article_info:
        print(f"⚠️  No mapping found for: {filename}")
        return False
    
    updated_count = 0
    lines = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                chunk = json.loads(line)
                
                # Add or update source metadata
                if "metadata" not in chunk:
                    chunk["metadata"] = {}
                
                chunk["metadata"]["source"] = filename
                chunk["metadata"]["title"] = article_info["title"]
                chunk["metadata"]["url"] = article_info["url"]
                chunk["metadata"]["from"] = article_info["company"]
                
                lines.append(json.dumps(chunk, ensure_ascii=False))
                updated_count += 1
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
        
        print(f"✅ {filename}: Updated {updated_count} chunks")
        return True
    
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        return False


def main():
    """Process all JSONL files in a target chunks directory."""
    parser = argparse.ArgumentParser(description="Fix chunk metadata in JSONL files.")
    parser.add_argument("--input-dir", default="data_improved_chunks", help="Directory containing .jsonl chunk files")
    args = parser.parse_args()

    chunks_dir = Path(args.input_dir)
    
    if not chunks_dir.exists():
        print(f"❌ Directory not found: {chunks_dir}")
        return
    
    jsonl_files = list(chunks_dir.glob("*.jsonl"))
    print(f"Found {len(jsonl_files)} JSONL files in {chunks_dir}\n")
    
    success_count = 0
    for filepath in sorted(jsonl_files):
        if update_chunk_file(str(filepath)):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully updated: {success_count}/{len(jsonl_files)} files")
    print(f"\n💡 Next step: Delete your Chroma database and re-ingest chunks")
    print(f"   rm -r finance_db/")
    print(f"   python data_pipeline/ingest_chunks.py")


if __name__ == "__main__":
    main()
