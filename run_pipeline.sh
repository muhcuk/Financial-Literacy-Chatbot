# =================================================================
#      FINANCIAL LITERACY RAG CHATBOT - DATA PIPELINE SCRIPT
# =================================================================

# --- STEP 1: Process PDFs into Raw Chunks ---
# This command reads all PDFs from 'source_pdfs' and creates chunked
# JSONL files in the 'data/chunks' directory.
echo " "
echo "➡️  Step 1 of 4: Processing PDFs into raw text chunks..."
python pdf_to_rag.py --input_dir source_pdfs --output_dir data/chunks

# --- STEP 2: Clean the Raw Chunks ---
# (Optional but Recommended)
# This command reads the raw chunks and applies deeper cleaning rules,
# saving the refined output to 'data/clean_chunks'.
echo " "
echo "➡️  Step 2 of 4: Cleaning and refining text chunks..."
python cleanjsonl.py

# --- STEP 3: Build the Vector Database ---
# This command takes the cleaned chunks, creates vector embeddings,
# and builds/updates the ChromaDB in the 'finance_db' folder.
# The --reset flag wipes the old database and builds a new one.
# Remove --reset to only add new documents.
echo " "
echo "➡️  Step 3 of 4: Building the vector database (ChromaDB)..."
python app.py --input_glob "data/clean_chunks/*.jsonl" --reset

# --- STEP 4: Launch the Chatbot Application ---
# This command starts the Streamlit web server.
# Make sure the Ollama application is running in the background first!
echo " "
echo "✅ Pipeline complete. Knowledge base is ready."
echo "🚀 Step 4 of 4: Launching the chatbot application..."
echo " "
streamlit run app_finance_streamlit.py