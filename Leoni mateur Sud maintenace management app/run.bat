@echo off
echo Installing dependencies...
pip install -r requirements.txt -q
echo.
echo Starting Leoni Defect Analysis Dashboard...
echo Open http://localhost:8501 in your browser
echo.
streamlit run app.py
