import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.llms import Ollama
import os
import json
import subprocess
import re
from datetime import datetime
import time
import threading
from functools import lru_cache

# --- Configuration ---
PERSIST_DIR = "../finance_db"
COLLECTION_NAME = "finance_knowledge"
EMB_MODEL = "intfloat/multilingual-e5-small"
# Note: LLM_MODEL is now dynamic based on user selection

# --- Page Configuration ---
st.set_page_config(
    page_title="Financial Literacy Chatbot",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #FFD700;
    }
    .quiz-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #1e1e1e;
        margin-bottom: 1rem;
        border-left: 4px solid #FFD700;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #2b313e;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "welcome"
if "pre_test_completed" not in st.session_state:
    st.session_state.pre_test_completed = False
if "post_test_completed" not in st.session_state:
    st.session_state.post_test_completed = False
if "user_id" not in st.session_state:
    st.session_state.user_id = datetime.now().strftime("%Y%m%d_%H%M%S")
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "my-finetuned"  # Default model
if "resources_loaded" not in st.session_state:
    st.session_state.resources_loaded = False

# --- Reset Session Function ---
def reset_session():
    """Reset all session state for new user"""
    st.session_state.messages = []
    st.session_state.current_page = "welcome"
    st.session_state.pre_test_completed = False
    st.session_state.post_test_completed = False
    st.session_state.user_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Reset to fixed defaults
    st.session_state.selected_model = "my-finetuned"
    st.session_state.rag_mode = "Strict"
    # Keep resources_loaded = True so we don't reload
    if "pre_test_scores" in st.session_state:
        del st.session_state.pre_test_scores
    if "post_test_scores" in st.session_state:
        del st.session_state.post_test_scores
    if "participant_info" in st.session_state:
        del st.session_state.participant_info

# --- PISA Questions ---
PISA_QUESTIONS = {
    "Financial Knowledge": [
        {
            "id": "FL164Q01",
            "question": "Have you heard of or learnt about: Interest payment",
            "options": ["Never heard of it", "Heard of it, but don't recall meaning", "Know what it means"],
            "weight": 1
        },
        {
            "id": "FL164Q02",
            "question": "Have you heard of or learnt about: Compound interest",
            "options": ["Never heard of it", "Heard of it, but don't recall meaning", "Know what it means"],
            "weight": 1
        },
        {
            "id": "FL164Q12",
            "question": "Have you heard of or learnt about: Budget",
            "options": ["Never heard of it", "Heard of it, but don't recall meaning", "Know what it means"],
            "weight": 1
        }
    ],
    "Financial Behavior": [
        {
            "id": "FL160Q01",
            "question": "When buying a product, how often do you compare prices in different shops?",
            "options": ["Never", "Rarely", "Sometimes", "Always"],
            "weight": 1
        },
        {
            "id": "FL171Q08",
            "question": "In the last 12 months, how often have you checked how much money you have?",
            "options": ["Never/Almost never", "Once/twice a year", "Once/twice a month", "Weekly", "Daily"],
            "weight": 1
        }
    ],
    "Financial Confidence": [
        {
            "id": "FL162Q03",
            "question": "How confident would you feel about understanding bank statements?",
            "options": ["Not at all confident", "Not very confident", "Confident", "Very confident"],
            "weight": 1
        },
        {
            "id": "FL162Q06",
            "question": "How confident are you about planning spending with consideration of your financial situation?",
            "options": ["Not at all confident", "Not very confident", "Confident", "Very confident"],
            "weight": 1
        }
    ],
    "Financial Attitudes": [
        {
            "id": "FL169Q05",
            "question": "To what extent do you agree: I know how to manage my money",
            "options": ["Strongly disagree", "Disagree", "Agree", "Strongly agree"],
            "weight": 1
        },
        {
            "id": "FL169Q10",
            "question": "To what extent do you agree: I make savings goals for things I want to buy",
            "options": ["Strongly disagree", "Disagree", "Agree", "Strongly agree"],
            "weight": 1
        }
    ]
}

# --- Get Available Models ---
def get_available_models():
    """Get list of available models from Ollama"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        available_models = []
        
        for line in result.stdout.split('\n')[1:]:  # Skip header
            if line.strip():
                model_name = line.split()[0]
                if model_name and ':' not in model_name:  # Filter out tags
                    available_models.append(model_name)
        
        # Remove duplicates and sort
        available_models = sorted(list(set(available_models)))
        
        if not available_models:
            available_models = ["llama3.2", "my-finetuned"]
        
        return available_models
    except:
        return ["llama3.2", "my-finetuned"]

# --- Load Resources (Optimized with separate caching) ---
@st.cache_resource(show_spinner=False)
def load_embeddings():
    """Load embeddings model - cached separately since it never changes"""
    return HuggingFaceEmbeddings(model_name=EMB_MODEL)

@st.cache_resource(show_spinner=False)
def load_database(_embeddings):
    """Load Chroma database - cached separately"""
    if not os.path.exists(PERSIST_DIR):
        st.error(f"Database not found at {PERSIST_DIR}")
        st.stop()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_embeddings,
        persist_directory=PERSIST_DIR
    )

@st.cache_resource(show_spinner=False)
def load_llm(_model_name):
    """Load LLM - cached by model name"""
    return Ollama(
        model=_model_name,
        temperature=0.7,
        num_predict=450,  # Allow complete multi-point responses
        top_k=35,
        top_p=0.9,
        repeat_penalty=1.15  # Prevent repetition
    )

def load_resources(model_name):
    """Load all resources with optimized caching"""
    embeddings = load_embeddings()
    db = load_database(embeddings)
    llm = load_llm(model_name)
    return db, llm

# --- Data Storage Functions ---
def save_test_results(test_type, participant_info, responses, scores):
    """Save test results to JSON file"""
    filename = "data/test_results.json"
    os.makedirs("data", exist_ok=True)
    
    result_data = {
        "user_id": st.session_state.user_id,
        "timestamp": datetime.now().isoformat(),
        "test_type": test_type,
        "participant_info": participant_info,
        "responses": responses,
        "scores": scores,
        "model_used": st.session_state.selected_model
    }
    
    try:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except FileNotFoundError:
            all_data = {"results": []}
        except Exception as e:
            st.error(f"Error loading test results: {e}")
            all_data = {"results": []}
        
        all_data["results"].append(result_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {test_type} test for user {st.session_state.user_id}")
    except Exception as e:
        st.error(f"Error saving test results: {e}")
        print(f"❌ Failed to save {test_type} test: {e}")

def save_feedback(question, answer, rating, sources):
    """Save user feedback"""
    feedback_file = "data/user_feedback.json"
    os.makedirs("data", exist_ok=True)
    
    feedback_entry = {
        "user_id": st.session_state.user_id,
        "timestamp": datetime.now().isoformat(),
        "feedback_type": "response",
        "question": question,
        "answer": answer[:500],
        "rating": rating,
        "sources_count": len(sources),
        "model_used": st.session_state.selected_model
    }
    
    try:
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
        except FileNotFoundError:
            feedback_data = {"feedback": []}
        except Exception as e:
            st.error(f"Error loading feedback: {e}")
            feedback_data = {"feedback": []}
        
        feedback_data["feedback"].append(feedback_entry)
        
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved feedback: {rating}")
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
        print(f"❌ Failed to save feedback: {e}")

def save_general_feedback(user_id, feedback_text, rating):
    """Save general user feedback about the chatbot experience"""
    feedback_file = "data/user_feedback.json"
    os.makedirs("data", exist_ok=True)
    
    feedback_entry = {
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "feedback_type": "general",
        "feedback_text": feedback_text,
        "rating": rating,
        "question": "General Feedback",
        "answer": "N/A",
        "sources_count": 0,
        "model_used": st.session_state.selected_model
    }
    
    try:
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
        except FileNotFoundError:
            feedback_data = {"feedback": []}
        except Exception as e:
            feedback_data = {"feedback": []}
        
        feedback_data["feedback"].append(feedback_entry)
        
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved general feedback")
    except Exception as e:
        st.error(f"Error saving general feedback: {e}")
        print(f"❌ Failed to save feedback: {e}")

# --- Score Calculation ---
def calculate_scores(responses):
    """Calculate scores by category"""
    category_scores = {}
    
    for category, questions in PISA_QUESTIONS.items():
        total_score = 0
        max_score = 0
        
        for q in questions:
            response = next((r for r in responses if r["question_id"] == q["id"]), None)
            if response:
                score_value = response["score"]
                total_score += score_value
                max_score += len(q["options"]) - 1
        
        category_scores[category] = (total_score / max_score * 100) if max_score > 0 else 0
    
    all_scores = list(category_scores.values())
    category_scores["Overall"] = sum(all_scores) / len(all_scores) if all_scores else 0
    
    return category_scores

# --- RAG Functions ---
def rewrite_query(query: str) -> str:
    """Expand query for better retrieval"""
    financial_keywords = {
        "save": "saving tips money management",
        "budget": "budgeting financial planning spending",
        "debt": "debt management loan credit card",
        "invest": "investment returns stocks bonds",
        "retire": "retirement planning EPF KWSP",
        "emergency": "emergency fund savings buffer",
        "mistake": "common mistakes errors avoid financial",
        "scam": "scam fraud prevention red flags",
        "insurance": "insurance medical coverage protection",
        "tax": "income tax filing LHDN deduction"
    }
    
    query_lower = query.lower()
    for keyword, expansion in financial_keywords.items():
        if keyword in query_lower:
            return f"{query} {expansion}"
    return query


def detect_query_intent(query: str) -> dict:
    """Detect user intent from query to customize response format."""
    query_lower = query.lower()
    intent = {
        "list_type": None,  # "mistakes", "tips", "ways", "steps", "reasons"
        "count": None,      # Number if specified (e.g., "5 mistakes")
        "is_question": "?" in query or query_lower.startswith(("what", "how", "why", "when", "where", "can", "should", "is", "are", "do", "does"))
    }
    
    # Detect list type
    list_patterns = {
        "mistakes": ["mistake", "error", "wrong", "avoid", "don't", "never"],
        "tips": ["tip", "advice", "suggestion", "recommend"],
        "ways": ["way", "method", "how to"],
        "steps": ["step", "process", "procedure"],
        "reasons": ["reason", "why", "cause"],
        "habits": ["habit", "practice", "routine"]
    }
    
    for list_type, patterns in list_patterns.items():
        if any(p in query_lower for p in patterns):
            intent["list_type"] = list_type
            break
    
    # Detect count (e.g., "5 mistakes", "top 10 tips")
    count_match = re.search(r'(\d+)\s*(mistake|tip|way|step|reason|habit|thing|point)', query_lower)
    if count_match:
        intent["count"] = int(count_match.group(1))
    else:
        # Check for word numbers
        word_nums = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, 
                     "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        for word, num in word_nums.items():
            if word in query_lower:
                intent["count"] = num
                break
    
    return intent


def run_rag_chain(query: str, db, llm, rag_mode: str = "Strict"):
    """Run RAG chain with provided database and LLM.

    rag_mode: "Strict" | "Hybrid" | "Model-only"
    """
    expanded_query = rewrite_query(query)
    intent = detect_query_intent(query)

    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 2, "fetch_k": 5, "lambda_mult": 0.5}  # Reduced for faster retrieval
    )
    # Try common retriever methods to get documents (compat with different retriever implementations)
    docs = []
    for method in ("get_relevant_documents", "get_retrievals", "retrieve", "get_documents", "invoke"):
        if hasattr(retriever, method):
            try:
                docs = getattr(retriever, method)(expanded_query)
                break
            except Exception:
                continue

    # Ensure docs is a list
    if docs is None:
        docs = []

    context_parts = []
    total_chars = 0
    max_chars = 1500  # Balanced for thorough context

    for doc in docs:
        # Support both LangChain Document and simple dict-like objects
        content = getattr(doc, "page_content", None) or getattr(doc, "content", None) or (doc.get("page_content") if isinstance(doc, dict) else None)
        if not content:
            continue
        if total_chars + len(content) <= max_chars:
            context_parts.append(content)
            total_chars += len(content)
        else:
            remaining = max_chars - total_chars
            if remaining > 200:
                context_parts.append(content[:remaining])
            break
    
    context = "\n\n".join(context_parts)
    
    # Prepare sources list for debug/metadata
    sources = [{"content": getattr(doc, "page_content", ""), "metadata": getattr(doc, "metadata", {})} for doc in docs]

    # Build dynamic format instructions based on intent
    count_instruction = ""
    if intent["count"]:
        count_instruction = f"The user asked for exactly {intent['count']} items. You MUST provide exactly {intent['count']} items, no more, no less."
    
    list_format = "tips"
    if intent["list_type"] == "mistakes":
        list_format = "mistakes (things to AVOID)"
    elif intent["list_type"] == "steps":
        list_format = "steps (in order)"
    elif intent["list_type"] == "reasons":
        list_format = "reasons"
    elif intent["list_type"] == "ways":
        list_format = "ways"
    elif intent["list_type"] == "habits":
        list_format = "habits"

    # Build prompts depending on RAG mode
    if rag_mode == "Strict":
        prompt = f"""You are a friendly financial literacy assistant helping Malaysian youth with money management.

STRICT RULES:
1. Answer ONLY using information from the Context below
2. Do NOT make up information not in the Context
3. Keep each point BRIEF (1-2 sentences max per point)
4. Use Malaysian context (RM, EPF/KWSP)

{count_instruction}

Context:
{context}

User Question: {query}

RESPONSE FORMAT:
- One sentence introduction
- List multiple points concisely:
  1. **[Title]**: Brief explanation (1-2 sentences)
  2. **[Title]**: Brief explanation (1-2 sentences)
  3. **[Title]**: Brief explanation (1-2 sentences)
- One practical tip at the end

IMPORTANT: Keep each point SHORT. Cover MORE points rather than explaining one point in detail.

Answer:"""

        response_stream = llm.stream(prompt)

    elif rag_mode == "Hybrid":
        # Allow model to use its knowledge to supplement but prefer context
        prompt = f"""You are a financial literacy assistant for Malaysian youth.

RULES:
1. Use the Context below as your PRIMARY source
2. You may add supplementary info, label it "[Supplementary]"
3. Keep each point BRIEF (1-2 sentences)
4. Use Malaysian context (RM, EPF/KWSP)

{count_instruction}

Context:
{context}

Question: {query}

RESPONSE FORMAT:
- Brief introduction
- List points concisely:
  1. **[Title]**: Brief explanation
  2. **[Title]**: Brief explanation
- One practical tip

IMPORTANT: Cover MORE points briefly rather than few points in detail.

Answer:"""

        response_stream = llm.stream(prompt)

    else:  # Model-only
        prompt = f"""You are a financial literacy assistant for Malaysian youth.

{count_instruction}

Question: {query}

RULES:
1. Provide thorough, educational explanations (200-250 words)
2. Use Malaysian context (RM, EPF/KWSP) where possible
3. If listing {list_format}, explain WHY each point matters
4. Include practical examples with specific amounts
5. If unsure, acknowledge it but still provide helpful guidance

Answer:"""

        response_stream = llm.stream(prompt)

        # clear sources for model-only
        sources = []

    return response_stream, sources


# --- Article URL & Title Mapping ---
ARTICLE_URLS = {
    "smart_budgeting_technique": {
        "title": "Smart Budgeting Technique",
        "url": "https://www.kwsp.gov.my/w/infographic/smart-budgeting-technique"
    },
    "first_salary_tips": {
        "title": "First Salary Tips",
        "url": "https://www.kwsp.gov.my/w/article/first-salary-tips"
    },
    "travelling_green_tips": {
        "title": "Travelling Green Tips",
        "url": "https://www.kwsp.gov.my/w/article/travelling-green-tips"
    },
    "insurance_tips": {
        "title": "Insurance Tips",
        "url": "https://www.kwsp.gov.my/w/infographic/insurance-tips"
    },
    "saving_tips_for_gig_worker": {
        "title": "Savings Tips for Gig Workers",
        "url": "https://www.kwsp.gov.my/w/infographic/savings-tips-for-gig-workers"
    },
    "death_assistance": {
        "title": "EPF Death Assistance",
        "url": "https://www.kwsp.gov.my/w/article/epf-death-assistance"
    },
    "multiple_savings_with_i_saraan": {
        "title": "Multiply Savings with i-Saraan",
        "url": "https://www.kwsp.gov.my/w/infographic/multiply-savings-with-i-saraan"
    },
    "expense_after_retired": {
        "title": "Expenses After Retirement",
        "url": "https://www.kwsp.gov.my/w/article/expenses-after-retired"
    },
    "fomo_shopping": {
        "title": "FOMO Shopping",
        "url": "https://www.kwsp.gov.my/w/article/fomo-shopping"
    },
    "why_medical_insurance_importance": {
        "title": "Why Medical Insurance is Important",
        "url": "https://www.kwsp.gov.my/w/article/why-medical-insurance-is-important"
    },
    "buy_vs_rent": {
        "title": "Buy vs Rent Malaysia",
        "url": "https://www.kwsp.gov.my/w/article/buy-vs-rent-malaysia"
    },
    "fashion_on_a_budget": {
        "title": "Fashion on a Budget",
        "url": "https://www.kwsp.gov.my/w/article/fashion-on-a-budget"
    },
    "budgeting_rule": {
        "title": "50-30-20 Rule",
        "url": "https://www.kwsp.gov.my/w/article/50-30-20-rule"
    },
    "file_income_tax": {
        "title": "How to File Income Tax",
        "url": "https://www.kwsp.gov.my/w/article/how-to-file-income-tax"
    },
    "compound_interest_benefits": {
        "title": "Compound Interest Benefits",
        "url": "https://www.kwsp.gov.my/w/article/compound-interest-benefits"
    },
    "pay_yourself_first": {
        "title": "Pay Yourself First",
        "url": "https://www.kwsp.gov.my/w/article/pay-yourself-first"
    },
    "new_year_financial_goals": {
        "title": "New Year Financial Goals",
        "url": "https://www.kwsp.gov.my/w/article/new-year-financial-goals"
    },
    "master_your_finance": {
        "title": "Master Your Finance",
        "url": "https://www.kwsp.gov.my/w/article/master-your-finance"
    },
    "quick_ways_to_losing_savings": {
        "title": "Quick Ways to Lose Savings",
        "url": "https://www.kwsp.gov.my/w/article/quick-ways-to-lose-savings"
    },
    "surviving_on_paycheck": {
        "title": "Surviving on Paycheck",
        "url": "https://www.kwsp.gov.my/w/article/surviving-on-paycheck"
    },
    "scam_red_flags": {
        "title": "Scam Red Flags",
        "url": "https://www.kwsp.gov.my/w/article/scam-red-flags"
    },
    "vacation_on_budget": {
        "title": "Vacation on Budget",
        "url": "https://www.kwsp.gov.my/w/article/vacation-on-budget"
    },
    "save_money_malaysian_ways": {
        "title": "Save Money Malaysian Ways",
        "url": "https://www.kwsp.gov.my/w/article/save-money-malaysian-ways"
    },
    "financial_independence": {
        "title": "Financial Independence",
        "url": "https://www.kwsp.gov.my/w/article/financial-independence"
    },
    "how_to_avoid_online_scam": {
        "title": "How to Avoid Online Scam",
        "url": "https://www.kwsp.gov.my/w/article/how-to-avoid-online-scam"
    },
    "buy_first_think_later": {
        "title": "Buy First Think Later",
        "url": "https://www.kwsp.gov.my/w/article/buy-first-think-later"
    },
    "income_and_your_savings": {
        "title": "Income and Your Savings",
        "url": "https://www.kwsp.gov.my/w/article/income-and-your-savings"
    },
    "retirement_planning_tips": {
        "title": "Retirement Planning Tips",
        "url": "https://www.kwsp.gov.my/w/article/retirement-planning-tips"
    },
    "savings_and_inflation": {
        "title": "Savings and Inflation",
        "url": "https://www.kwsp.gov.my/w/article/savings-and-inflation"
    },
    "achieve_money_goals": {
        "title": "Achieve Money Goals",
        "url": "https://www.kwsp.gov.my/w/article/achieve-money-goal"
    },
    "how_to_use_akaun_3": {
        "title": "How to Use Akaun 3",
        "url": "https://www.kwsp.gov.my/w/article/how-to-use-akaun-3"
    },
    "saving_for_festives": {
        "title": "Savings for Festives",
        "url": "https://www.kwsp.gov.my/w/article/savings-for-festives"
    },
    "shariah_retirement": {
        "title": "Simpanan Shariah Retirement",
        "url": "https://www.kwsp.gov.my/w/article/simpanan-shariah-retirement"
    },
    "invest_smarter": {
        "title": "Invest Smarter",
        "url": "https://www.kwsp.gov.my/w/article/invest-smarter"
    },
    "retirement_calculator": {
        "title": "Retirement Calculator",
        "url": "https://www.kwsp.gov.my/w/article/retirement-calculator"
    },
    "ensuring_wife_future": {
        "title": "Ensuring Wife Future",
        "url": "https://www.kwsp.gov.my/w/article/ensuring-wife-future"
    },
    "epf_house": {
        "title": "EPF Housing Withdrawal",
        "url": "https://www.kwsp.gov.my/w/article/epf-housing-withdrawal"
    },
    "emergency_fund": {
        "title": "Emergency Fund",
        "url": "https://www.kwsp.gov.my/w/article/emergency-fund"
    },
    "reward_yourself": {
        "title": "Reward Yourself",
        "url": "https://www.kwsp.gov.my/w/article/reward-yourself"
    },
    "unwise_spending_habits": {
        "title": "Unwise Spending Habits",
        "url": "https://www.kwsp.gov.my/w/article/unwise-spending-habits"
    },
    "boost_your_savings": {
        "title": "Boost Your Savings",
        "url": "https://www.kwsp.gov.my/w/article/boost-your-savings"
    },
    "reasons_to_save_money": {
        "title": "Reasons to Save Money",
        "url": "https://www.kwsp.gov.my/w/article/reasons-to-save-money"
    },
    # KWSP articles with full filename keys  
    "kwsp_gov_my_w_article_50_30_20_rule": {
        "title": "50-30-20 Rule",
        "url": "https://www.kwsp.gov.my/w/article/50-30-20-rule"
    },
    "kwsp_gov_my_w_article_expenses_after_retired": {
        "title": "Expenses After Retirement",
        "url": "https://www.kwsp.gov.my/w/article/expenses-after-retired"
    },
    "kwsp_gov_my_w_article_why_medical_insurance_is_important": {
        "title": "Why Medical Insurance is Important",
        "url": "https://www.kwsp.gov.my/w/article/why-medical-insurance-is-important"
    },
    "kwsp_gov_my_w_infographic_savings_tips_for_gig_workers": {
        "title": "Savings Tips for Gig Workers",
        "url": "https://www.kwsp.gov.my/w/infographic/savings-tips-for-gig-workers"
    },
    # Educational frameworks
    "educational_methodologies_of_personal_finance": {
        "title": "Educational Methodologies of Personal Finance",
        "url": "https://www.financialeducatorscouncil.org/wp-content/uploads/Educational-Methodologies-of-Personal-Finance.pdf"
    },
    "flcc_for_malaysian_adults_compressed": {
        "title": "Financial Literacy for Malaysian Adults",
        "url": "https://www.fenetwork.my/wp-content/uploads/2023/02/Financial-Literacy-Core-Competencies-for-Malaysian-Adults.pdf"
    },
    "framework_for_teaching_personal_finance": {
        "title": "Framework for Teaching Personal Finance",
        "url": "https://www.financialeducatorscouncil.org/wp-content/uploads/Framework-for-Teaching-Personal-Finance.pdf"
    },
    "learner_framework_standards_for_high_school_college_adults": {
        "title": "Learner Framework Standards for Financial Literacy",
        "url": "https://www.financialeducatorscouncil.org/wp-content/uploads/DOC_PKG_EXC_-NFEC-Learner-Framework-Standards-for-High-School-College-Adults-_3.4.09.pdf"
    },
    "nfec_report_policy_and_standards_framework_for_high_school_financial_literacy_education": {
        "title": "NFEC: Policy and Standards Framework for Financial Literacy",
        "url": "https://www.financialeducatorscouncil.org/wp-content/uploads/nfec-report-policy-and-standards-framework-for-high-school-financial-literacy-education.pdf"
    },
    "smart_technique_an_easy_way_to_achieve_financial_goals_kwsp_malaysia": {
        "title": "S.M.A.R.T Technique: Achieve Financial Goals",
        "url": "https://www.kwsp.gov.my/en/w/infographic/smart-budgeting-technique"
    },
    # Files with special characters - map by exact filename
    "5 mistakes young adult make with money — lalua rahsiad.jsonl": {
        "title": "5 Mistakes Young Adults Make With Money",
        "url": "https://www.laluarahsiad.com/blog-2/blog2"
    },
    "what no one tells you about budgeting in your 20s — lalua rahsiad.jsonl": {
        "title": "What No One Tells You About Budgeting in Your 20s",
        "url": "https://www.laluarahsiad.com/blog-2/blog3"
    },
    "why financial freedom starts with your mindset — lalua rahsiad.jsonl": {
        "title": "Why Financial Freedom Starts with Your Mindset",
        "url": "https://www.laluarahsiad.com/blog-2/blog1"
    },
    "how to celebrate deepavali without overspending - kwsp malaysia.jsonl": {
        "title": "Celebrate Deepavali Without Overspending",
        "url": "https://www.kwsp.gov.my/en/w/article/celebrate-deepavali-without-overspending"
    },
    "article 4 (digital financial).jsonl": {
        "title": "Digital Financial Management",
        "url": "https://www.akpk.org.my/sites/default/files/2024-12/ARTICLE%204%20%28DIGITAL%20FINANCIAL%29.pdf"
    },
    "article 6 (getting into debt).jsonl": {
        "title": "Getting Into Debt: What You Need to Know",
        "url": "https://www.akpk.org.my/sites/default/files/2025-02/ARTICLE%206%20%28GETTING%20INTO%20DEBT%29.pdf"
    },
    "article 8 (breaking the chains).jsonl": {
        "title": "Breaking the Chains of Debt",
        "url": "https://www.akpk.org.my/sites/default/files/2025-02/ARTICLE%208%20%28BREAKING%20THE%20CHAINS%29.pdf"
    },
    "s.m.a.r.t technique_ an easy way to achieve financial goals - kwsp malaysia.jsonl": {
        "title": "S.M.A.R.T Technique: Achieve Financial Goals",
        "url": "https://www.kwsp.gov.my/en/w/infographic/smart-budgeting-technique"
    },
    "financial fraud prevention and detection_ governance and effective practices ( pdfdrive ).jsonl": {
        "title": "Financial Fraud Prevention and Detection",
        "url": "https://institutes.abu.edu.ng/idr/public/assets/docs/Financial%20Fraud%20Prevention%20and%20Detection_%20Governance%20and%20Effective%20Practices%20(%20PDFDrive%20).pdf"
    },
    # Generic/Additional articles from www_kwsp.gov files
    "www_kwsp.gov": {
        "title": "BNPL: Buy Now Pay Later",
        "url": "https://www.kwsp.gov.my/w/article/buy-now-pay-later"
    },
    "buying_first_car": {
        "title": "Buying Your First Car",
        "url": "https://www.kwsp.gov.my/w/article/buying-first-car"
    },
    "early_retirement_habits": {
        "title": "Early Retirement Habits",
        "url": "https://www.kwsp.gov.my/w/article/early-retirement-habits"
    },
    # Lalua Rahsiad normalized keys
    "5_mistakes_young_adult_make_with_money_lalua_rahsiad": {
        "title": "5 Mistakes Young Adults Make With Money",
        "url": "https://www.laluarahsiad.com/blog-2/blog2"
    },
    "what_no_one_tells_you_about_budgeting_in_your_20s_lalua_rahsiad": {
        "title": "What No One Tells You About Budgeting in Your 20s",
        "url": "https://www.laluarahsiad.com/blog-2/blog3"
    },
    "why_financial_freedom_starts_with_your_mindset_lalua_rahsiad": {
        "title": "Why Financial Freedom Starts with Your Mindset",
        "url": "https://www.laluarahsiad.com/blog-2/blog1"
    },
    "how_to_celebrate_deepavali_without_overspending_kwsp_malaysia": {
        "title": "Celebrate Deepavali Without Overspending",
        "url": "https://www.kwsp.gov.my/en/w/article/celebrate-deepavali-without-overspending"
    },
    # Article series normalized keys
    "article_4_digital_financial": {
        "title": "Digital Financial Management",
        "url": "https://www.akpk.org.my/sites/default/files/2024-12/ARTICLE%204%20%28DIGITAL%20FINANCIAL%29.pdf"
    },
    "article_6_getting_into_debt": {
        "title": "Getting Into Debt: What You Need to Know",
        "url": "https://www.akpk.org.my/sites/default/files/2025-02/ARTICLE%206%20%28GETTING%20INTO%20DEBT%29.pdf"
    },
    "article_8_breaking_the_chains": {
        "title": "Breaking the Chains of Debt",
        "url": "https://www.akpk.org.my/sites/default/files/2025-02/ARTICLE%208%20%28BREAKING%20THE%20CHAINS%29.pdf"
    },
}


def get_article_info(source_name: str, metadata: dict) -> tuple:
    """Extract proper title and URL from source name and metadata."""
    
    # Try to get source_file from metadata first
    source_file = metadata.get("source_file", "")
    if source_file and not source_name:
        source_name = os.path.basename(source_file)
    
    # Get title from metadata
    meta_title = metadata.get("title", "")
    
    # Normalize source name for matching
    if source_name:
        source_key = source_name.lower().replace(" ", "_").replace("-", "_").replace("—", "_").replace(".jsonl", "").replace(".pdf", "").strip()
    else:
        source_key = ""
    
    # Special handling for Lalua Rahsiad articles (check first for priority)
    if "lalua" in source_key.lower() or (meta_title and "lalua" in meta_title.lower()):
        if "mistake" in source_key.lower() or (meta_title and "mistake" in meta_title.lower()):
            return "5 Mistakes Young Adults Make With Money", "https://www.laluarahsiad.com/blog-2/blog2"
        elif "budget" in source_key.lower() or (meta_title and "budget" in meta_title.lower()):
            return "What No One Tells You About Budgeting in Your 20s", "https://www.laluarahsiad.com/blog-2/blog3"
        elif "mindset" in source_key.lower() or "freedom" in source_key.lower() or (meta_title and ("mindset" in meta_title.lower() or "freedom" in meta_title.lower())):
            return "Why Financial Freedom Starts with Your Mindset", "https://www.laluarahsiad.com/blog-2/blog1"
    
    # Check if we can match by metadata title
    if meta_title:
        title_key = meta_title.lower().replace(" ", "_").replace("-", "_").replace("—", "_").replace(".jsonl", "").replace(".pdf", "").strip()
        
        # Try exact match on title
        if title_key in ARTICLE_URLS:
            info = ARTICLE_URLS[title_key]
            return info["title"], info["url"]
        
        # Try partial match on title
        for key in ARTICLE_URLS:
            if key in title_key or title_key in key:
                info = ARTICLE_URLS[key]
                return info["title"], info["url"]
    
    if not source_name:
        return metadata.get("title", "Unknown Source"), extract_source_url(metadata)
    
    # Try exact match on source key
    if source_key in ARTICLE_URLS:
        info = ARTICLE_URLS[source_key]
        return info["title"], info["url"]
    
    # Try partial matching
    for key in ARTICLE_URLS:
        if key in source_key or source_key in key:
            info = ARTICLE_URLS[key]
            return info["title"], info["url"]
    
    # Fallback: use metadata title if available
    title = metadata.get("title", source_name)
    url = extract_source_url(metadata)
    
    return title, url


def extract_source_url(metadata: dict) -> str:
    """Return the best URL found in metadata or a sensible default."""
    if not metadata:
        return "https://www.kwsp.gov.my"

    # Common keys that may contain URLs
    keys = ["url", "source", "source_url", "link", "href", "webpage_url", "uri"]
    for k in keys:
        v = metadata.get(k)
        if not v:
            continue
        if isinstance(v, str) and (v.startswith("http") or v.startswith("www")):
            if v.startswith("www"):
                return "https://" + v
            return v

    # Fallback: try to find any string value that looks like a URL
    for v in metadata.values():
        if isinstance(v, str) and ("http" in v or v.startswith("www")):
            if v.startswith("www"):
                return "https://" + v
            return v

    return "https://www.kwsp.gov.my"


def is_greeting(text: str) -> bool:
    """Return True if the text looks like a simple greeting."""
    if not text:
        return False
    t = text.strip().lower()
    greetings = ["hi", "hello", "hey", "hiya", "good morning", "good afternoon", "good evening", "yo"]
    # treat very short greetings or single-word matches as greeting
    if t in greetings or len(t.split()) <= 2 and any(t.startswith(g) for g in greetings):
        return True
    return False

# --- UI Pages ---
def show_welcome_page():
    """Welcome page"""
    st.markdown('<p class="main-header">💰 Financial Literacy Chatbot</p>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome! 👋
    
    This AI-powered chatbot helps you learn about financial literacy using information from 
    **Malaysian EPF (KWSP)** and financial education resources.
    
    #### 📋 How it works:
    1. **Pre-Test** - Complete a short quiz to assess your current financial knowledge
    2. **Learn** - Ask the chatbot any questions about financial literacy
    3. **Post-Test** - Take the quiz again to see your improvement
    4. **Results** - View your learning progress
    
    #### ⏱️ Time Required:
    - Pre-test: ~5 minutes
    - Chatbot interaction: 15-20 minutes (recommended)
    - Post-test: ~5 minutes
    
    ---
    
    **Ready to start?** Click the button below!
    """)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Start Pre-Test", type="primary", use_container_width=True):
            st.session_state.current_page = "pre_test"
            st.rerun()

def show_pisa_test(test_type="pre"):
    """Show PISA test"""
    st.title(f"📋 {'Pre' if test_type == 'pre' else 'Post'}-Test: Financial Literacy Assessment")
    
    st.markdown(f"""
    ### {f'Let us assess your current financial knowledge' if test_type == 'pre' else 'Final Assessment - See Your Progress!'}
    
    This assessment is based on the **PISA 2022 Financial Literacy Framework** used globally by OECD.
    
    **Questions:** {sum(len(v) for v in PISA_QUESTIONS.values())} | **Time:** ~5 minutes
    """)
    
    if test_type == "pre":
        with st.expander("👤 Your Information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Age", min_value=15, max_value=99, value=20)
                education = st.selectbox("Education Level",
                    ["Secondary School", "Diploma", "Bachelor's", "Master's", "PhD", "Other"])
            with col2:
                gender = st.selectbox("Gender", ["Male", "Female", "Prefer not to say"])
                occupation = st.selectbox("Occupation",
                    ["Student", "Employee", "Self-employed", "Unemployed", "Other"])
        
        participant_info = {
            "age": age,
            "education": education,
            "gender": gender,
            "occupation": occupation
        }
        st.session_state.participant_info = participant_info
    else:
        participant_info = st.session_state.get("participant_info", {})
    
    st.divider()
    
    all_responses = []
    question_number = 1
    
    for category, questions in PISA_QUESTIONS.items():
        st.subheader(f"📊 {category}")
        
        for q in questions:
            st.markdown(f"**Q{question_number}. {q['question']}**")
            
            response = st.radio(
                "Select your answer:",
                options=q["options"],
                key=f"{test_type}_{q['id']}",
                label_visibility="collapsed"
            )
            
            score = q["options"].index(response) if response else 0
            
            all_responses.append({
                "question_id": q["id"],
                "question": q["question"],
                "category": category,
                "response": response,
                "score": score
            })
            
            question_number += 1
            st.divider()
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📤 Submit Assessment", type="primary", use_container_width=True):
            scores = calculate_scores(all_responses)
            save_test_results(test_type, participant_info, all_responses, scores)
            
            if test_type == "pre":
                st.session_state.pre_test_completed = True
                st.session_state.pre_test_scores = scores
                st.session_state.current_page = "chatbot"
            else:
                st.session_state.post_test_completed = True
                st.session_state.post_test_scores = scores
                st.session_state.current_page = "results"
            
            st.success("✅ Assessment submitted!")
            st.balloons()
            st.rerun()

def show_chatbot_page():
    """Main chatbot interface"""
    st.markdown('<p class="main-header">💰 Financial Literacy Chatbot</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("✅ Pre-Test Complete")
    with col2:
        st.info("💬 Currently Using Chatbot")
    with col3:
        if st.button("📝 Take Post-Test"):
            st.session_state.current_page = "post_test"
            st.rerun()
    
    try:
        db, llm = load_resources(st.session_state.selected_model)
    except Exception as e:
        st.error(f"❌ Error loading model '{st.session_state.selected_model}': {str(e)}")
        st.info("💡 Make sure the model is imported to Ollama. Run: `ollama list` to check available models")
        return
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📚 View Sources"):
                    for i, source in enumerate(message["sources"], 1):
                        metadata = source["metadata"]
                        # Get source from source_file (full path) or title
                        source_file = metadata.get("source_file", "")
                        if source_file:
                            # Extract filename from path
                            source_name = os.path.basename(source_file)
                        else:
                            source_name = metadata.get("title", metadata.get("source", ""))
                        
                        title, url = get_article_info(source_name, metadata)
                        
                        # Extract additional metadata - detect source properly
                        if "lalua" in source_name.lower() or "lalua" in title.lower():
                            from_source = "Lalua Rahsiad Blog"
                        elif "akpk" in url.lower():
                            from_source = "AKPK Malaysia"
                        elif "kwsp" in url.lower() or "epf" in url.lower():
                            from_source = "KWSP Malaysia"
                        else:
                            from_source = metadata.get("from", metadata.get("company", "Financial Education Resource"))
                        page_num = metadata.get("page", metadata.get("page_number", ""))
                        section = metadata.get("section", "")
                        
                        # Build section text
                        section_text = ""
                        if section and page_num:
                            section_text = f"Section: {section}, p.{page_num}"
                        elif page_num:
                            section_text = f"p.{page_num}"
                        elif section:
                            section_text = f"Section: {section}"
                        
                        # Render with custom format
                        st.markdown(f"<a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\"><strong>{title}</strong></a>", unsafe_allow_html=True)
                        st.caption(f"From: {from_source}")
                        if section_text:
                            st.caption(section_text)
                        st.caption(source["content"][:300] + "...")
                        st.divider()
    
    if prompt := st.chat_input("Ask about financial literacy..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Animated thinking indicator
            thinking_placeholder = st.empty()
            stop_animation = threading.Event()
            
            def animate_thinking(placeholder, stop_event):
                dots = ["", ".", "..", "..."]
                idx = 0
                while not stop_event.is_set():
                    placeholder.markdown(f"💭 chatbot is thinking{dots[idx]}")
                    idx = (idx + 1) % len(dots)
                    time.sleep(0.5)
                placeholder.empty()
            
            try:
                short_circuit = False
                # Greeting shortcut: handle simple salutations without running RAG
                if is_greeting(prompt):
                    full_response = (
                        "Hello! I understand that a greeting means you'd like to start a conversation. "
                        "As a financial literacy chatbot, I'm here to help with questions about budgeting, saving, investing, debt, retirement (EPF/KWSP), and other personal finance topics. "
                        "How can I assist you today?"
                    )
                    retrieved_count = 0
                    sources = []
                    # (hidden) do not display model/RAG debug info to users
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sources": sources,
                        "model": st.session_state.get('selected_model', 'unknown'),
                        "retrieved_count": retrieved_count,
                        "rag_mode": st.session_state.get('rag_mode', 'Hybrid')
                    })
                    stop_animation.set()
                    short_circuit = True
                else:
                    # Start animation
                    animation_thread = threading.Thread(target=animate_thinking, args=(thinking_placeholder, stop_animation))
                    animation_thread.start()

                    # Get response (pass RAG mode)
                    rag_mode = st.session_state.get("rag_mode", "Hybrid")
                    response_stream, sources = run_rag_chain(prompt, db, llm, rag_mode=rag_mode)

                    # Stop animation
                    stop_animation.set()
                    animation_thread.join()
                
                # Stream the response (skip if we already handled a short-circuit greeting)
                if not short_circuit:
                    try:
                        retrieved_count = len(sources) if sources is not None else 0
                    except Exception:
                        retrieved_count = 0

                    for chunk in response_stream:
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                
                # Feedback buttons with cus
                # tom styling to prevent text wrapping
                st.markdown("""
                <style>
                    div[data-testid="column"] button {
                        white-space: nowrap !important;
                        width: auto !important;
                        min-width: fit-content !important;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    if st.button("👍 Helpful", key=f"helpful_{len(st.session_state.messages)}", use_container_width=False):
                        save_feedback(prompt, full_response, "helpful", sources)
                        st.success("Thanks!")
                with col2:
                    if st.button("👎 Not Helpful", key=f"not_helpful_{len(st.session_state.messages)}", use_container_width=False):
                        save_feedback(prompt, full_response, "not_helpful", sources)
                        st.warning("We'll improve!")
                
                with st.expander("📚 View Sources"):
                    for i, source in enumerate(sources, 1):
                        metadata = source["metadata"]
                        # Get source from source_file (full path) or title
                        source_file = metadata.get("source_file", "")
                        if source_file:
                            # Extract filename from path
                            source_name = os.path.basename(source_file)
                        else:
                            source_name = metadata.get("title", metadata.get("source", ""))
                        
                        title, url = get_article_info(source_name, metadata)
                        
                        # Extract additional metadata - detect source properly
                        if "lalua" in source_name.lower() or "lalua" in title.lower():
                            from_source = "Lalua Rahsiad Blog"
                        elif "akpk" in url.lower():
                            from_source = "AKPK Malaysia"
                        elif "kwsp" in url.lower() or "epf" in url.lower():
                            from_source = "KWSP Malaysia"
                        else:
                            from_source = metadata.get("from", metadata.get("company", "Financial Education Resource"))
                        page_num = metadata.get("page", metadata.get("page_number", ""))
                        section = metadata.get("section", "")
                        
                        # Build section text
                        section_text = ""
                        if section and page_num:
                            section_text = f"Section: {section}, p.{page_num}"
                        elif page_num:
                            section_text = f"p.{page_num}"
                        elif section:
                            section_text = f"Section: {section}"
                        
                        # Render with custom format
                        st.markdown(f"<a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\"><strong>{title}</strong></a>", unsafe_allow_html=True)
                        st.caption(f"From: {from_source}")
                        if section_text:
                            st.caption(section_text)
                        st.caption(source["content"][:300] + "...")
                        st.divider()
                
                if not short_circuit:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sources": sources,
                        "model": st.session_state.get('selected_model', 'unknown'),
                        "retrieved_count": retrieved_count,
                        "rag_mode": st.session_state.get('rag_mode', 'Hybrid')
                    })
                # keep debug banner with the message for a short time
                # (it will remain visible in the assistant block as part of the UI)
                
            except Exception as e:
                # Stop animation if error occurs
                stop_animation.set()
                if 'animation_thread' in locals():
                    animation_thread.join()
                
                error_msg = f"❌ Error: {str(e)}"
                message_placeholder.markdown(error_msg)
                
                if "model" in str(e).lower() or "not found" in str(e).lower():
                    st.error(f"Model '{st.session_state.selected_model}' not found in Ollama.")
                    st.info("💡 Run `ollama list` to see available models, or import your model first.")

def show_results_page():
    """Show final results and improvement"""
    st.title("🎉 Congratulations! You've Completed the Assessment")
    
    pre_scores = st.session_state.get("pre_test_scores", {})
    post_scores = st.session_state.get("post_test_scores", {})
    
    st.subheader("📊 Your Progress")
    
    categories = ["Financial Knowledge", "Financial Behavior", "Financial Confidence", "Financial Attitudes", "Overall"]
    
    for category in categories:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"**{category}**")
        with col2:
            st.metric("Before", f"{pre_scores.get(category, 0):.0f}%")
        with col3:
            st.metric("After", f"{post_scores.get(category, 0):.0f}%")
        with col4:
            improvement = post_scores.get(category, 0) - pre_scores.get(category, 0)
            if improvement > 0:
                st.success(f"+{improvement:.0f}%")
            elif improvement < 0:
                st.error(f"{improvement:.0f}%")
            else:
                st.info("0%")
    
    st.divider()
    
    overall_improvement = post_scores.get("Overall", 0) - pre_scores.get("Overall", 0)
    
    if overall_improvement > 15:
        st.success(f"🌟 **Excellent Progress!** You improved by {overall_improvement:.1f}% overall!")
    elif overall_improvement > 5:
        st.info(f"✅ **Good Work!** You improved by {overall_improvement:.1f}%")
    elif overall_improvement > 0:
        st.info(f"👍 **You Improved!** +{overall_improvement:.1f}%")
    else:
        st.warning("Consider spending more time learning with the chatbot.")
    
    st.divider()
    
    st.subheader("💭 We'd Love Your Feedback!")
    
    with st.form("feedback_form"):
        st.write("Please share your experience with the Financial Literacy Chatbot:")
        
        rating = st.radio(
            "How would you rate your overall experience?",
            ["⭐ Excellent", "⭐ Good", "⭐ Average", "⭐ Poor"],
            horizontal=True
        )
        
        col1, col2 = st.columns(2)
        with col1:
            helpful = st.select_slider(
                "How helpful was the chatbot?",
                options=["Not helpful", "Somewhat helpful", "Helpful", "Very helpful", "Extremely helpful"]
            )
        with col2:
            easy_to_use = st.select_slider(
                "How easy was it to use?",
                options=["Very difficult", "Difficult", "Neutral", "Easy", "Very easy"]
            )
        
        feedback_text = st.text_area(
            "What did you like or dislike about the chatbot? Any suggestions for improvement?",
            placeholder="Your feedback helps us improve...",
            height=100
        )
        
        topics = st.multiselect(
            "Which topics did you find most useful? (Optional)",
            ["Saving Money", "Budgeting", "EPF/KWSP", "Investing", "Debt Management", 
             "Emergency Fund", "Credit Cards", "Insurance", "Other"]
        )
        
        submitted = st.form_submit_button("📤 Submit Feedback", type="primary")
        
        if submitted:
            if feedback_text.strip():
                comprehensive_feedback = {
                    "overall_rating": rating,
                    "helpfulness": helpful,
                    "ease_of_use": easy_to_use,
                    "feedback_text": feedback_text,
                    "useful_topics": topics,
                    "model_used": st.session_state.selected_model
                }
                
                save_general_feedback(
                    st.session_state.user_id,
                    str(comprehensive_feedback),
                    rating.split()[1].lower()
                )
                
                st.success("✅ Thank you for your feedback!")
                st.balloons()
            else:
                st.warning("Please provide some feedback in the text area.")
    
    st.divider()
    
    st.markdown("### 💡 Thank you for participating!")
    st.markdown("Your feedback helps us improve the chatbot for future users.")
    
    st.subheader("🔄 Next Steps")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("👤 Start New User Session", type="primary", use_container_width=True):
            reset_session()
            st.rerun()
    
    st.caption("Click above to reset and allow another person to use the chatbot")

def show_admin_dashboard():
    """Admin page to view all user results"""
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.title("👨‍💼 Admin Dashboard")
    with col3:
        if st.button("🚪 Logout", type="secondary"):
            st.session_state.current_page = "welcome"
            st.rerun()
    
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["📊 Test Results", "💬 Feedback", "📈 Analytics"])
    
    with tab1:
        st.subheader("All Test Results")
        
        try:
            with open("data/test_results.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get("results", [])
            
            if not results:
                st.warning("No test data available yet.")
            else:
                st.metric("Total Participants", len(set(r["user_id"] for r in results)))
                
                test_type_filter = st.selectbox("Filter by test type:", ["All", "pre", "post"])
                
                for result in results:
                    if test_type_filter != "All" and result["test_type"] != test_type_filter:
                        continue
                    
                    model_used = result.get("model_used", "unknown")
                    with st.expander(f"User: {result['user_id']} - {result['test_type'].upper()} Test - {result['timestamp'][:10]} - Model: {model_used}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Participant Info:**")
                            for key, value in result["participant_info"].items():
                                st.write(f"- {key.title()}: {value}")
                        
                        with col2:
                            st.write("**Scores:**")
                            for key, value in result["scores"].items():
                                st.write(f"- {key}: {value:.1f}%")
                        
                        st.write("**Detailed Responses:**")
                        for resp in result["responses"]:
                            st.write(f"**Q:** {resp['question']}")
                            st.write(f"**A:** {resp['response']} (Score: {resp['score']})")
                            st.divider()
        
        except FileNotFoundError:
            st.error("No test results file found.")
    
    with tab2:
        st.subheader("User Feedback")
        
        try:
            with open("data/user_feedback.json", 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
            
            feedbacks = feedback_data.get("feedback", [])
            
            if not feedbacks:
                st.warning("No feedback data available yet.")
            else:
                helpful = sum(1 for f in feedbacks if f["rating"] == "helpful")
                not_helpful = sum(1 for f in feedbacks if f["rating"] == "not_helpful")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Feedback", len(feedbacks))
                with col2:
                    st.metric("👍 Helpful", helpful)
                with col3:
                    st.metric("👎 Not Helpful", not_helpful)
                
                st.divider()
                
                for fb in feedbacks:
                    feedback_type = fb.get("feedback_type", "response")
                    model_used = fb.get("model_used", "unknown")
                    
                    if feedback_type == "general":
                        with st.expander(f"💭 General Feedback - {fb['timestamp'][:10]} - Model: {model_used}"):
                            st.write(f"**User:** {fb['user_id']}")
                            st.write(f"**Rating:** {fb['rating'].upper()}")
                            st.write(f"**Feedback:**")
                            st.info(fb['feedback_text'])
                    else:
                        with st.expander(f"{fb['rating'].title()} - {fb['timestamp'][:10]} - Model: {model_used}"):
                            st.write(f"**User:** {fb['user_id']}")
                            st.write(f"**Question:** {fb['question']}")
                            st.write(f"**Answer:** {fb['answer']}")
                            st.write(f"**Sources Used:** {fb['sources_count']}")
        
        except FileNotFoundError:
            st.error("No feedback file found.")
    
    with tab3:
        st.subheader("Analytics")
        
        try:
            with open("data/test_results.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get("results", [])
            
            if results:
                user_improvements = {}
                
                for result in results:
                    user_id = result["user_id"]
                    test_type = result["test_type"]
                    overall_score = result["scores"]["Overall"]
                    
                    if user_id not in user_improvements:
                        user_improvements[user_id] = {}
                    
                    user_improvements[user_id][test_type] = overall_score
                
                improvements = []
                for user_id, scores in user_improvements.items():
                    if "pre" in scores and "post" in scores:
                        improvement = scores["post"] - scores["pre"]
                        improvements.append(improvement)
                
                if improvements:
                    avg_improvement = sum(improvements) / len(improvements)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Users with Both Tests", len(improvements))
                    with col2:
                        st.metric("Average Improvement", f"{avg_improvement:.1f}%")
                    with col3:
                        improved = sum(1 for i in improvements if i > 0)
                        st.metric("Users Improved", f"{improved}/{len(improvements)}")
                else:
                    st.info("No complete pre/post test pairs yet.")
            else:
                st.warning("No data available.")
        
        except FileNotFoundError:
            st.error("No test results file found.")

# --- Main App Navigation ---
def main():
    """Main application"""
    
    # Preload resources at startup (runs once, cached thereafter)
    if not st.session_state.resources_loaded:
        with st.spinner("🚀 Loading AI resources... (first time only)"):
            try:
                load_resources("my-finetuned")
                st.session_state.resources_loaded = True
            except Exception as e:
                st.error(f"Failed to preload resources: {e}")
    
    with st.sidebar:
        st.title("📍 Navigation")
        
        if st.session_state.current_page == "welcome":
            st.info("👋 Welcome Page")
        elif not st.session_state.pre_test_completed:
            st.info("📝 Pre-Test")
        elif not st.session_state.post_test_completed:
            st.success("✅ Pre-Test Done")
            st.info("💬 Using Chatbot")
        else:
            st.success("✅ All Complete!")
        
        #st.divider()
        
        # Hidden: enforce fixed defaults (no UI display)
        st.session_state.selected_model = "my-finetuned"
        st.session_state.rag_mode = "Strict"
        
        st.divider()
        
        st.header("📊 Progress")
        progress = 0
        if st.session_state.pre_test_completed:
            progress += 33
        if len(st.session_state.messages) > 0:
            progress += 34
        if st.session_state.post_test_completed:
            progress += 33
        
        st.progress(progress / 100)
        st.caption(f"{progress}% Complete")
        
        st.divider()
        
        # NEW USER RESET BUTTON
        if st.button("🔄 New User", help="Reset for a new participant"):
            if st.session_state.current_page not in ["welcome", "admin"]:
                st.warning("⚠️ This will reset all progress!")
                if st.button("✅ Confirm Reset"):
                    reset_session()
                    st.rerun()
            else:
                reset_session()
                st.rerun()
        
        st.divider()
        
        st.header("ℹ️ About")
        st.markdown("""
        This chatbot uses:
        - 🤖 RAG (Retrieval-Augmented Generation)
        - 📚 KWSP/EPF Resources
        - 📋 PISA 2022 Framework
        - 🎯 Multiple AI Models
        """)
        
        st.divider()
        
        admin_password = st.text_input("Admin Access", type="password")
        if admin_password == "admin123":
            if st.button("📊 View Dashboard"):
                st.session_state.current_page = "admin"
                st.rerun()
        
        st.divider()
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Main content area
    if st.session_state.current_page == "welcome":
        show_welcome_page()
    elif st.session_state.current_page == "pre_test":
        show_pisa_test("pre")
    elif st.session_state.current_page == "chatbot":
        show_chatbot_page()
    elif st.session_state.current_page == "post_test":
        show_pisa_test("post")
    elif st.session_state.current_page == "results":
        show_results_page()
    elif st.session_state.current_page == "admin":
        show_admin_dashboard()

if __name__ == "__main__":
    main()