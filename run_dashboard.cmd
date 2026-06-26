@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8501
