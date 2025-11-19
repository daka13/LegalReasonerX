# 🚀 Quick Start Guide - LegalReasonerX Web Application

Get up and running with LegalReasonerX in less than 5 minutes!

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A CourtListener API token ([Get one free here](https://www.courtlistener.com/sign-in/))

## ⚡ Quick Start

### Option 1: Using the Start Script (Recommended)

**On Linux/Mac:**
```bash
./start.sh
```

**On Windows:**
```bash
start.bat
```

The script will:
1. Check if Python is installed
2. Install dependencies automatically
3. Start the server on http://localhost:8000

### Option 2: Manual Start

```bash
# 1. Install dependencies
pip install -r requirements-web.txt

# 2. Start the server
python -m uvicorn backend.main:app --reload
```

## 🌐 Access the Application

Once started, open your browser and navigate to:

**Main Application:** http://localhost:8000

**API Documentation:** http://localhost:8000/docs

## 🔑 Configure API Keys

1. Open http://localhost:8000 in your browser
2. Scroll to the "Configure Your API Keys" section
3. Enter your CourtListener API token (required)
4. Optionally, enter your OpenAI API key for AI features
5. Click "Save API Keys"

## 📖 Try It Out

### 1. Process a Citation

1. Navigate to **Citation Lookup** (in the navigation bar)
2. Try one of the example citations:
   - `179 U.S. 77`
   - `520 U.S. 17`
   - `347 U.S. 483`
3. Click **Process Citation**
4. View the extracted precedent cases

### 2. Visualize the Network

1. Click **Next Steps → Visualize Network**
2. Explore the interactive graph:
   - Drag nodes to rearrange
   - Zoom in/out
   - Hover over nodes to see details
   - Click nodes to highlight connections

### 3. Analyze Opinions

1. Go to **Opinions** in the navigation
2. Select a case from the dropdown
3. Read base and precedent opinions
4. Copy or export opinion text

### 4. AI Reasoning (Requires OpenAI API Key)

1. Go to **Reasoning** in the navigation
2. Select a case
3. Click **Run AI Analysis**
4. View the extracted legal argument and precedent analysis

## 🎨 Features Overview

### ✨ Micro-Interactions
The application features beautiful micro-interactions:
- Smooth animations when elements appear
- Hover effects on buttons and cards
- Loading spinners and progress bars
- Card shimmer effects
- Button ripple effects

### 📱 Responsive Design
- Works on desktop, tablet, and mobile
- Optimized for all screen sizes
- Touch-friendly interface

### 💾 Local Storage
- API keys stored securely in browser
- No server-side storage of credentials
- Data persists between sessions

## 🛠️ Troubleshooting

### Port Already in Use
If port 8000 is already in use, specify a different port:
```bash
python -m uvicorn backend.main:app --reload --port 8001
```

### Dependencies Not Installing
Try upgrading pip first:
```bash
pip install --upgrade pip
pip install -r requirements-web.txt
```

### API Errors
- Verify your CourtListener API token is correct
- Check your internet connection
- Ensure you're not hitting API rate limits

## 📚 Next Steps

- Read the full [WEB-README.md](WEB-README.md) for detailed documentation
- Explore the [API documentation](http://localhost:8000/docs)
- Check out the original Streamlit app with `streamlit run app.py`

## 🆘 Need Help?

- Check the [Issues](https://github.com/daka13/LegalReasonerX/issues) page
- Review the API documentation at `/docs`
- Read the full documentation in WEB-README.md

---

**Enjoy using LegalReasonerX! ⚖️**
