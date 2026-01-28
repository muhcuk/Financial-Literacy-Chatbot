"""
MCP Server for Financial Literacy Chatbot
Wraps ChromaDB to provide structured, verified responses
"""

import json
from typing import Any
from mcp.server.fastmcp import FastMCP
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os

# --- Configuration ---
PERSIST_DIR = "../finance_db"
COLLECTION_NAME = "finance_knowledge"
EMB_MODEL = "intfloat/multilingual-e5-small"

# Initialize MCP Server
mcp = FastMCP("Financial Literacy Knowledge Base")

# Global database instance
_db = None
_embeddings = None

def get_database():
    """Lazy load database connection"""
    global _db, _embeddings
    if _db is None:
        print("Loading embeddings model...")
        _embeddings = HuggingFaceEmbeddings(model_name=EMB_MODEL)
        print("Connecting to ChromaDB...")
        _db = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=_embeddings,
            persist_directory=PERSIST_DIR
        )
        print(f"Connected! Collection has {_db._collection.count()} documents")
    return _db


# =============================================================================
# MCP TOOLS - Structured access to knowledge base
# =============================================================================

@mcp.tool()
def search_financial_knowledge(query: str, max_results: int = 3) -> dict:
    """
    Search the verified financial knowledge base for information.
    Returns structured results with exact content and sources.
    
    Args:
        query: The search query about financial topics
        max_results: Maximum number of results to return (1-5)
    
    Returns:
        Dictionary with results, sources, and metadata
    """
    db = get_database()
    max_results = min(max(1, max_results), 5)  # Clamp between 1-5
    
    try:
        # Use MMR for diverse results
        docs = db.max_marginal_relevance_search(
            query, 
            k=max_results, 
            fetch_k=max_results * 2,
            lambda_mult=0.5
        )
        
        results = []
        sources = set()
        
        for doc in docs:
            content = doc.page_content.strip()
            metadata = doc.metadata or {}
            source = metadata.get("source", metadata.get("url", "Unknown"))
            
            results.append({
                "content": content,
                "source": source,
                "category": metadata.get("category", "General"),
                "title": metadata.get("title", "")
            })
            sources.add(source)
        
        return {
            "success": True,
            "query": query,
            "total_found": len(results),
            "results": results,
            "sources_used": list(sources),
            "instruction": "Use ONLY the content above to answer. Do not add information not present in these results."
        }
        
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "total_found": 0,
            "results": [],
            "error": str(e),
            "instruction": "No results found. Tell the user you don't have information on this topic."
        }


@mcp.tool()
def search_by_category(category: str, query: str = "") -> dict:
    """
    Search for financial information within a specific category.
    
    Args:
        category: One of: budgeting, saving, debt, investment, insurance, tax, scam, retirement
        query: Optional additional search terms
    
    Returns:
        Dictionary with category-specific results
    """
    db = get_database()
    
    category_keywords = {
        "budgeting": "budget spending 50/30/20 expenses money management",
        "saving": "save savings emergency fund pay yourself first",
        "debt": "debt loan credit card PTPTN interest payment",
        "investment": "invest investment stocks ASB unit trust returns",
        "insurance": "insurance medical coverage takaful protection",
        "tax": "tax LHDN income tax filing deduction relief",
        "scam": "scam fraud prevention phishing red flags",
        "retirement": "retirement EPF KWSP pension planning"
    }
    
    search_query = f"{category_keywords.get(category.lower(), category)} {query}".strip()
    
    try:
        docs = db.similarity_search(search_query, k=3)
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content.strip(),
                "source": doc.metadata.get("source", "Unknown"),
                "title": doc.metadata.get("title", "")
            })
        
        return {
            "success": True,
            "category": category,
            "query": search_query,
            "total_found": len(results),
            "results": results,
            "instruction": f"Present these {category} tips clearly. Only use information from the results."
        }
        
    except Exception as e:
        return {
            "success": False,
            "category": category,
            "error": str(e),
            "results": []
        }


@mcp.tool()
def calculate_compound_interest(
    principal: float, 
    annual_rate: float, 
    years: int,
    monthly_contribution: float = 0
) -> dict:
    """
    Calculate compound interest for savings/investment.
    Provides exact calculations - no hallucination possible.
    
    Args:
        principal: Initial amount in RM
        annual_rate: Annual interest rate as percentage (e.g., 5 for 5%)
        years: Number of years
        monthly_contribution: Optional monthly addition in RM
    
    Returns:
        Dictionary with calculated values
    """
    rate = annual_rate / 100
    
    # Basic compound interest
    basic_final = principal * (1 + rate) ** years
    
    # With monthly contributions (compound monthly)
    if monthly_contribution > 0:
        monthly_rate = rate / 12
        months = years * 12
        contribution_final = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
        total_final = basic_final + contribution_final
        total_contributed = principal + (monthly_contribution * months)
    else:
        total_final = basic_final
        total_contributed = principal
    
    return {
        "success": True,
        "inputs": {
            "principal_rm": principal,
            "annual_rate_percent": annual_rate,
            "years": years,
            "monthly_contribution_rm": monthly_contribution
        },
        "results": {
            "final_amount_rm": round(total_final, 2),
            "total_contributed_rm": round(total_contributed, 2),
            "interest_earned_rm": round(total_final - total_contributed, 2),
            "growth_percentage": round((total_final / total_contributed - 1) * 100, 2)
        },
        "explanation": f"After {years} years, RM{principal:,.2f} at {annual_rate}% grows to RM{total_final:,.2f}"
    }


@mcp.tool()
def calculate_50_30_20_budget(monthly_income: float) -> dict:
    """
    Calculate budget allocation using the 50/30/20 rule.
    
    Args:
        monthly_income: Monthly income in RM
    
    Returns:
        Dictionary with budget breakdown
    """
    needs = monthly_income * 0.50
    wants = monthly_income * 0.30
    savings = monthly_income * 0.20
    
    return {
        "success": True,
        "monthly_income_rm": monthly_income,
        "budget_breakdown": {
            "needs_50_percent": {
                "amount_rm": round(needs, 2),
                "includes": ["Rent/mortgage", "Utilities", "Groceries", "Transportation", "Insurance", "Minimum debt payments"]
            },
            "wants_30_percent": {
                "amount_rm": round(wants, 2),
                "includes": ["Dining out", "Entertainment", "Shopping", "Hobbies", "Subscriptions"]
            },
            "savings_20_percent": {
                "amount_rm": round(savings, 2),
                "includes": ["Emergency fund", "EPF top-up", "Investments", "Extra debt payments", "Savings goals"]
            }
        },
        "tip": "Start with this as a guideline and adjust based on your situation. High cost of living areas may need 60/20/20."
    }


@mcp.tool()
def get_emergency_fund_target(monthly_expenses: float, risk_level: str = "medium") -> dict:
    """
    Calculate recommended emergency fund target.
    
    Args:
        monthly_expenses: Your total monthly expenses in RM
        risk_level: Job stability - 'low' (stable), 'medium', or 'high' (freelance/unstable)
    
    Returns:
        Dictionary with emergency fund recommendations
    """
    months_needed = {
        "low": 3,
        "medium": 6,
        "high": 9
    }
    
    months = months_needed.get(risk_level.lower(), 6)
    target = monthly_expenses * months
    
    return {
        "success": True,
        "inputs": {
            "monthly_expenses_rm": monthly_expenses,
            "risk_level": risk_level
        },
        "recommendation": {
            "months_coverage": months,
            "target_amount_rm": round(target, 2),
            "minimum_rm": round(monthly_expenses * 3, 2),
            "ideal_rm": round(monthly_expenses * 6, 2)
        },
        "savings_plan": {
            "save_500_per_month": f"{round(target / 500)} months to reach target",
            "save_1000_per_month": f"{round(target / 1000)} months to reach target"
        },
        "tip": "Keep emergency fund in high-interest savings account for easy access."
    }


@mcp.tool()
def check_debt_ratio(monthly_income: float, total_monthly_debt_payments: float) -> dict:
    """
    Check if debt level is healthy using Debt-to-Income ratio.
    
    Args:
        monthly_income: Gross monthly income in RM
        total_monthly_debt_payments: Total monthly payments for all debts (car, house, PTPTN, credit cards)
    
    Returns:
        Dictionary with debt health assessment
    """
    dti_ratio = (total_monthly_debt_payments / monthly_income) * 100
    
    if dti_ratio <= 30:
        status = "Healthy"
        advice = "Your debt level is manageable. Consider investing the extra money."
    elif dti_ratio <= 40:
        status = "Moderate"
        advice = "Be cautious about taking new debt. Focus on paying down existing debt."
    elif dti_ratio <= 50:
        status = "High"
        advice = "Your debt is becoming burdensome. Prioritize debt repayment and avoid new debt."
    else:
        status = "Critical"
        advice = "Seek financial counseling. Consider AKPK (Agensi Kaunseling dan Pengurusan Kredit)."
    
    return {
        "success": True,
        "inputs": {
            "monthly_income_rm": monthly_income,
            "monthly_debt_payments_rm": total_monthly_debt_payments
        },
        "assessment": {
            "debt_to_income_ratio": round(dti_ratio, 1),
            "status": status,
            "advice": advice
        },
        "benchmarks": {
            "healthy": "Below 30%",
            "moderate": "30-40%",
            "high": "40-50%",
            "critical": "Above 50%"
        },
        "tip": "Banks typically won't approve loans if DTI exceeds 60-70%."
    }


# =============================================================================
# MCP RESOURCES - Static information
# =============================================================================

@mcp.resource("finance://malaysian-context")
def get_malaysian_context() -> str:
    """Provides Malaysian financial context for the assistant"""
    return """
    Malaysian Financial Context:
    - Currency: Ringgit Malaysia (RM)
    - Retirement fund: EPF (Employees Provident Fund) / KWSP
    - Tax authority: LHDN (Lembaga Hasil Dalam Negeri)
    - Credit counseling: AKPK (Agensi Kaunseling dan Pengurusan Kredit)
    - Student loan: PTPTN
    - Popular investments: ASB, ASM, Unit Trusts
    - Islamic finance: Widely available (Takaful, Islamic banking)
    """


# =============================================================================
# Run server
# =============================================================================

if __name__ == "__main__":
    print("Starting Financial Literacy MCP Server...")
    print(f"Database: {PERSIST_DIR}")
    print(f"Collection: {COLLECTION_NAME}")
    mcp.run()
