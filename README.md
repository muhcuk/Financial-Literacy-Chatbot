# 💰 Financial Literacy RAG Chatbot

A final year project demonstrating a Retrieval-Augmented Generation (RAG) chatbot focused on Malaysian financial literacy. The chatbot uses a local Llama 3 model to answer questions based on a knowledge base built from PDF documents.



## ✨ Features

* **PDF Knowledge Base**: Ingests information from PDF files to create a custom knowledge base.
* **OCR Fallback**: Automatically uses Tesseract OCR to extract text from image-based PDFs.
* **Local & Private**: Powered by a locally-run Llama 3 model via Ollama, ensuring cost-free operation and data privacy.
* **Context-Aware Answers**: Implements a RAG pipeline to provide answers grounded in the provided documents, reducing hallucinations.
* **Interactive UI**: A user-friendly web interface built with Streamlit, featuring streaming responses and interactive source verification.
* **Bilingual**: Capable of understanding and responding in both English and Bahasa Melayu.

## ⚙️ Project Architecture

The project follows a two-stage process: **1. Data Ingestion** and **2. Application Inference**.

```
[Stage 1: Ingestion Pipeline]
📚 PDFs -> [pdf_to_rag.py] -> 📄 Raw JSONL -> [cleanjsonl.py] -> ✨ Clean JSONL -> [app.py] -> 🧠 Chroma Vector DB

[Stage 2: Chatbot Application]
❓ User Query -> [app_finance.py] -> 🧠 Chroma Vector DB ->  contexto -> 🦙 Llama 3 -> 💬 Answer
```

## 🚀 Setup and Installation

Follow these steps to set up and run the project locally.

### 1. Prerequisites
- **Python 3.9+**
- **Ollama**: Download and install from [ollama.com](https://ollama.com).
- **(Optional) Tesseract OCR**: For processing scanned PDFs. Follow installation instructions at [Tesseract's GitHub](https://github.com/tesseract-ocr/tesseract).

### 2. Clone the Repository
```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

### 3. Set Up Python Environment
It is highly recommended to use a virtual environment.
```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
Install all the required Python libraries using the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

### 5. Download the Local LLM
Pull the Llama 3 model using Ollama. Make sure the Ollama application is running.
```bash
ollama pull llama3:8b
```

## USAGE

Follow these steps to build the knowledge base and run the chatbot.

### Step 1: Add Your Documents
Create a folder named `source_pdfs` (or any name you prefer) and place all your financial literacy PDF documents inside it.

### Step 2: Process PDFs into JSONL
Run the `pdf_to_rag.py` script to extract and chunk text from the PDFs.
```bash
python pdf_to_rag.py --input_dir source_pdfs --output_dir data/chunks
```

### Step 3: (Optional) Clean the JSONL Chunks
Run the `cleanjsonl.py` script to further refine the extracted text.
```bash
python cleanjsonl.py
```
*This script reads from `data/chunks` and writes to `data/clean_chunks` by default.*

### Step 4: Build the Vector Database
Run the ingestion script (`app.py`) to create vector embeddings and build the Chroma database.
```bash
# This will build the database from the cleaned chunks
python app.py --input_glob "data/clean_chunks/*.jsonl"
```
*To rebuild the database from scratch, add the `--reset` flag.*
```bash
python app.py --input_glob "data/clean_chunks/*.jsonl" --reset
```

### Step 5: Launch the Chatbot
With the Ollama application running in the background, start the Streamlit app.
```bash
streamlit run app_finance.py
```
Open your web browser and navigate to the local URL provided (usually `http://localhost:8501`).