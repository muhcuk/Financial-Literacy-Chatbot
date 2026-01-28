# =================================================================
#  FINANCIAL LITERACY RAG CHATBOT - SETUP & RUN SCRIPT (PowerShell)
# =================================================================

function Build-KnowledgeBase {
    $ErrorActionPreference = 'Stop'

    # Menu for build strategy
    $choices = @(
        (New-Object System.Management.Automation.Host.ChoiceDescription "&Rebuild from scratch","Deletes old data and rebuilds"),
        (New-Object System.Management.Automation.Host.ChoiceDescription "&Update with new files only","Keeps existing data and adds new"),
        (New-Object System.Management.Automation.Host.ChoiceDescription "&Cancel","Return to main menu")
    )
    $choice = $host.UI.PromptForChoice("Database Build Options","Choose how to build the database:",$choices,0)

    $resetFlag = ""
    switch ($choice) {
        0 { $resetFlag = "--reset"; Write-Host "Database will be rebuilt." -ForegroundColor Green }
        1 { Write-Host "Database will be updated." -ForegroundColor Green }
        2 { Write-Host "Operation cancelled." -ForegroundColor Yellow; return }
        default { return }
    }

    $py = ".\venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { Write-Host "Python venv not found at $py" -ForegroundColor Red; return }

    $sourcePdfDir = "source_pdfs"
    Write-Host "`n➡️  Step 1 of 3: Processing PDFs from '$sourcePdfDir'..."
    if (-not (Test-Path $sourcePdfDir) -or -not (Get-ChildItem -Path $sourcePdfDir -File)) {
        Write-Host "❌ Error: The '$sourcePdfDir' directory does not exist or is empty." -ForegroundColor Red
        return
    }
    & $py .\process_pdfs.py --input_dir $sourcePdfDir --output_dir data/chunks

    Write-Host "`n➡️  Step 2 of 3: Cleaning and refining text chunks..."
    & $py .\clean_chunks.py

    Write-Host "`n➡️  Step 3 of 3: Building the vector database..."
    & $py .\database_build.py --input_glob "data/clean_chunks/*.jsonl" $resetFlag

    Write-Host "`n✅ Pipeline complete. The knowledge base is ready." -ForegroundColor Green
}

function Launch-Chatbot {
    $ErrorActionPreference = 'Stop'
    $py = ".\venv\Scripts\python.exe"
    $streamlit = ".\venv\Scripts\streamlit.exe"

    if (Test-Path .\app_finance.py) {
        if (-not (Test-Path $streamlit)) {
            Write-Host "Installing Streamlit..." -ForegroundColor Yellow
            & ".\venv\Scripts\pip.exe" install streamlit | Out-Null
        }
        Write-Host "`nLaunching Streamlit app..." -ForegroundColor Cyan
        Write-Host "Open your browser to http://localhost:8501"
        & $streamlit run .\app_finance.py
        return
    }

    if (Test-Path .\run_chatbot_app.py) {
        Write-Host "`nLaunching Flask app..." -ForegroundColor Cyan
        Write-Host "Open your browser to http://127.0.0.1:5000"
        & $py .\run_chatbot_app.py
        return
    }

    Write-Host "No app entrypoint found (app_finance.py or run_chatbot_app.py)." -ForegroundColor Yellow
}

# --- SCRIPT EXECUTION STARTS HERE ---
$ErrorActionPreference = 'Stop'
Write-Host "🚀 Starting the Financial Chatbot Setup..." -ForegroundColor Cyan

# Create folders
$dirs = @("source_pdfs","data/chunks","data/clean_chunks","finance_db","templates","static")
foreach ($d in $dirs) { if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null } }

# Create venv if missing
if (-not (Test-Path ".\venv")) {
    Write-Host "   - Setting up Python virtual environment..."
    python -m venv venv
}
# Install deps
Write-Host "   - Installing dependencies from requirements2.txt..."
& ".\venv\Scripts\pip.exe" install -r requirements2.txt

# Optional: Ollama + model check (non-blocking)
Write-Host "   - Checking for Ollama and Llama 3 model..."
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    try {
        $list = ollama list
        if ($list -match "llama3:8b") {
            Write-Host "✅ Llama 3 model is already installed." -ForegroundColor Green
        } else {
            Write-Host "⚠️  Llama 3 model not found. Pulling it now..." -ForegroundColor Yellow
            ollama pull llama3:8b
        }
    } catch {
        Write-Host "⚠️  Warning: Cannot connect to Ollama. Continuing..." -ForegroundColor Yellow
    }
} else {
    Write-Host "ℹ️  Ollama not installed. Skipping local LLM checks (this is fine)." -ForegroundColor DarkYellow
}

Write-Host "`n✅ Setup Complete!" -ForegroundColor Green
Write-Host "--------------------------------------------------------"

# Main menu loop
while ($true) {
    $choices = @(
        (New-Object System.Management.Automation.Host.ChoiceDescription "&Build/Rebuild Knowledge Base","Build or rebuild the vector DB"),
        (New-Object System.Management.Automation.Host.ChoiceDescription "&Launch Chatbot","Start Streamlit or Flask app"),
        (New-Object System.Management.Automation.Host.ChoiceDescription "&Quit","Exit")
    )
    $menuChoice = $host.UI.PromptForChoice("Main Menu","Select an option:",$choices,0)

    switch ($menuChoice) {
        0 { Build-KnowledgeBase; continue }  # return to menu
        1 { Launch-Chatbot; continue }       # return to menu
        2 { Write-Host "Exiting."; break }   # exit the while loop
        default { continue }
    }
}


### **How to Run Your Project Now**

#1.  **Delete Old Scripts**: To avoid confusion, you can delete `setupRun.sh` and `run_pipeline_flask.sh`. This new `setupRun.ps1` file replaces both of them.

#2.  **Run with PowerShell**:
#    * Right-click the `setupRun.ps1` file in your file explorer.
#    * Select **"Run with PowerShell"**.

    

#    You may see a security warning the first time you run a script. If so, you might need to change your execution policy. Open PowerShell as an Administrator and run:
#    ```powershell
#    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#.\rag_env\Scripts\Activate
#.\setupRun.ps1
    
