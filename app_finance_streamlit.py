# --- SQLite patch for Windows (Chroma needs sqlite3) ---
import sys
try:
    import sqlite3
except Exception:
    import pysqlite3 as sqlite3
    sys.modules["sqlite3"] = sqlite3
# -------------------------------------------------------

import os
import re
from dotenv import load_dotenv
import streamlit as st

# Free local embeddings for BM/EN
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Import ChatOllama for local LLM integration
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama

load_dotenv()

# --- Configuration ---
PERSIST_DIR = "./finance_db"
COLLECTION_NAME = "finance_knowledge"
EMB_MODEL = "intfloat/multilingual-e5-small"
# Define the local model to use with Ollama
LLM_MODEL = "llama3:8b" 

# --- Load Database and Retriever ---
@st.cache_resource
def load_retriever():
    """Load the Chroma DB and retriever once to save time."""
    embedding_model = HuggingFaceEmbeddings(model_name=EMB_MODEL)
    db = Chroma(
        collection_name=COLLECTION_NAME, 
        embedding_function=embedding_model, 
        persist_directory=PERSIST_DIR
    )
    return db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

retriever = load_retriever()

# --- Helper Functions ---
def pretty_snippet(s: str, max_chars: int = 1200) -> str:
    """A helper function to format the context for display."""
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = s.strip()
    if len(s) > max_chars:
        s = s[:max_chars].rsplit(" ", 1)[0] + "…"
    return s

# --- RAG Chain ---
def run_rag_chain(query: str):
    """Executes the RAG pipeline: retrieve, augment, and generate."""
    template = """
You are a helpful financial literacy assistant for Malaysia (you can answer in Bahasa Melayu or English).
Use ONLY the following context to answer the user's question. If the information is not in the context,
state that you don't have enough information to answer. Do not make up facts.

Context:
{context}

Question:
{question}

Provide a clear and actionable answer based on the context.
"""
    prompt_tmpl = ChatPromptTemplate.from_template(template)
    
    # 1. Retrieve relevant documents
    docs = retriever.get_relevant_documents(query)
    if not docs:
        return "I couldn't find relevant information in the knowledge base. Please try rephrasing your question or add more documents.", []

    # 2. Augment the prompt with the retrieved context
    context_tidy = pretty_snippet("\n\n".join([d.page_content for d in docs]))
    prompt = prompt_tmpl.format_prompt(context=context_tidy, question=query)

    # 3. Generate a response using the local LLM
    llm = ChatOllama(model=LLM_MODEL, temperature=0.1)
    
    # The function now returns the stream iterator and the source documents
    return llm.stream(prompt.to_messages()), docs

# --- Streamlit User Interface ---
st.set_page_config(page_title="Financial Literacy — RAG Chatbot", page_icon="💰", layout="wide")
st.title("💰 Financial Literacy Chatbot (Powered by Llama 3)")

# Sidebar for app information and example questions
with st.sidebar:
    st.header("About")
    st.info(
        "This chatbot uses a local Llama 3 model to answer questions about "
        "Malaysian financial literacy based on a custom knowledge base."
    )
    st.markdown("---")
    st.header("Example Questions")
    if st.button("What is a good emergency fund amount?"):
        st.session_state.query = "What is a good emergency fund amount?"
    if st.button("How to start investing in Malaysia?"):
        st.session_state.query = "How to start investing in Malaysia?"
    if st.button("Bagaimana cara untuk menguruskan hutang?"):
        st.session_state.query = "Bagaimana cara untuk menguruskan hutang?"

# Initialize session state for the query to allow button clicks to update it
if "query" not in st.session_state:
    st.session_state.query = ""

# Main chat interface
query = st.text_area(
    "Ask a question (BM/EN):", 
    value=st.session_state.query,
    placeholder="e.g., Berapa jumlah tabung kecemasan yang sesuai?"
)

if st.button("🔎 Get Answer", type="primary"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking... (Llama is warming up!)"):
            # Execute the RAG chain and get the response stream and sources
            response_stream, sources = run_rag_chain(query.strip())
            
            st.markdown("### 🧠 Answer")
            # Use st.write_stream to display the response as it's generated
            answer_container = st.empty()
            full_response = answer_container.write_stream(response_stream)
            
            # Display interactive source documents
            if sources:
                st.markdown("---")
                st.markdown("### 📚 Sources")
                for doc in sources:
                    # Use an expander for each source to keep the UI clean
                    with st.expander(f"**{os.path.basename(doc.metadata.get('source', 'Unknown'))}** - Page {doc.metadata.get('page_start', 'N/A')}"):
                        st.text(doc.page_content)