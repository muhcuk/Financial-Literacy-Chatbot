# ============================
# Financial RAG Chatbot Setup
# ============================

Write-Host "🚀 Starting setup process..."

# 1. Create and activate virtual environment
Write-Host "📦 Creating virtual environment..."
python -m venv rag_env

Write-Host "✅ Activating virtual environment..."
& .\rag_env\Scripts\Activate

# 2. Upgrade pip
Write-Host "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# 3. Install all required packages (in one line)
Write-Host "📥 Installing required packages..."
pip install `
    langchain-community `
    langchain-chroma `
    sentence-transformers `
    chromadb `
    streamlit `
    python-dotenv `
    openai `
    langchain-openai `
    pysqlite3 `
    pypdf

Write-Host "✅ All packages installed successfully."

# 4. Clean and embed data into Chroma
Write-Host "🧹 Cleaning and embedding data..."
python app.py --glob "data/chunks/*.jsonl" --persist_dir "./finance_db" --collection "finance_knowledge" --reset

# 5. Run Streamlit chatbot
Write-Host "🤖 Launching the chatbot..."
streamlit run app_finance_streamlit.py

#run all
#.\setup_and_run.ps1
