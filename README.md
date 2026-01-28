# 💰 Financial Literacy Chatbot

An AI-powered chatbot designed to improve financial literacy among Malaysian youth through Retrieval-Augmented Generation (RAG) with interactive pre/post assessments based on PISA Financial Literacy Framework.

## ✨ Features

- **📚 RAG-Powered Responses** - Retrieves relevant information from a curated financial knowledge base
- **🔄 Multiple RAG Modes** - Strict, Hybrid, and Model-only modes for flexible response generation
- **📊 PISA-Based Assessment** - Pre/post tests measuring Financial Knowledge, Behavior, Confidence & Attitudes
- **🎯 Intent Detection** - Automatically detects query type (tips, mistakes, steps, etc.) for better formatting
- **🔍 Query Expansion** - Enhances search queries for improved retrieval accuracy
- **📝 Source Citations** - Links responses to verified Malaysian financial resources (KWSP, etc.)
- **🇲🇾 Malaysia Context** - EPF/KWSP, LHDN tax, Malaysian ringgit-focused content

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **LLM:** Ollama (supports custom fine-tuned models)
- **Embeddings:** HuggingFace `intfloat/multilingual-e5-small`
- **Vector Database:** ChromaDB
- **Framework:** LangChain

## 🚀 Quick Start

```bash
# Install dependencies
pip install streamlit langchain langchain-community langchain-chroma chromadb sentence-transformers

# Ensure Ollama is running with your model
ollama run my-finetuned

# Run the chatbot
cd streamlit
streamlit run s_app.py
```

## 📁 Project Structure

```
├── streamlit/
│   └── s_app.py          # Main Streamlit application
├── chunks/               # Knowledge base chunks (JSONL)
├── data/                 # Test results & user feedback
├── train_model/          # Fine-tuning scripts
└── finance_db/           # ChromaDB vector store (generated)
```

## 🎯 Topics Covered

- 💰 Budgeting (50/30/20 rule)
- 🏦 Saving & Emergency funds
- 💳 Debt management
- 📈 Investment basics
- 🏥 Insurance planning
- 🧾 Tax filing (LHDN)
- 👴 Retirement planning (EPF/KWSP)
- ⚠️ Scam prevention

## 📊 Assessment Framework

Based on **PISA Financial Literacy Framework**:
- Financial Knowledge
- Financial Behavior  
- Financial Confidence
- Financial Attitudes

## 📄 License

MIT License
