@echo off
cd /d "%~dp0"
call conversion_env\Scripts\activate
streamlit run s_app.py --server.port 8501
pause
