# ⚖️ LegalReasonerX: Legal Document Analysis System

A simple Streamlit app template for you to modify!

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   $ pip install streamlit requests networkx matplotlib numpy plotly bs4 openai
   ```
2. Save the code as app.py
3. Run the app: 
   ```
   $ streamlit run streamlit_app.py
   ```
4. Enter your CourtListener API token in the sidebar (required)
5. Optionally, enter an OpenAI API key if you want to use the reasoning framework

### Workflow

1. Start by entering a legal citation in the Citation Lookup tab
2. After processing, explore the citation network in the Precedent Network tab
3. View full opinions in the Opinion Analysis tab
4. Use the Reasoning Framework tab to analyze the legal reasoning