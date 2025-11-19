# 🌐 LegalReasonerX - Modern Web Application

A beautiful, modern web application for legal document analysis and precedent-driven reasoning. This is a complete transformation of the original Streamlit application into a professional, production-ready web platform.

![Legal Analysis](https://img.shields.io/badge/Legal-Analysis-blue)
![AI Powered](https://img.shields.io/badge/AI-Powered-green)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-teal)
![Modern UI](https://img.shields.io/badge/UI-Modern-purple)

## ✨ Features

### 🔍 Citation Lookup
- Verify legal citations using the CourtListener API
- Extract precedent cases automatically
- Process single or multiple citations at once
- Real-time validation and error handling

### 🕸️ Network Visualization
- Interactive force-directed graph visualization
- Drag, zoom, and explore citation networks
- Color-coded nodes by case type
- Network statistics and metrics

### 📄 Opinion Analysis
- Extract full text of legal opinions
- View base and precedent opinions side-by-side
- Copy, export, and share opinions
- Organized by case with easy navigation

### 🧠 AI-Powered Reasoning Framework
- Extract legal arguments using GPT-4
- Analyze how precedents support arguments
- Entity extraction and recognition
- Export analysis in multiple formats

## 🎨 Design Highlights

### Micro-Interactions
- ✅ Smooth animations and transitions
- ✅ Hover effects on all interactive elements
- ✅ Loading states with spinners and progress bars
- ✅ Card animations with shimmer effects
- ✅ Button ripple effects
- ✅ Scroll-based navbar effects
- ✅ Staggered list animations
- ✅ Modal and tooltip animations

### Modern UI/UX
- Professional color scheme
- Responsive design for all devices
- Intuitive navigation
- Accessibility-focused
- Clean, minimalist aesthetic

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- CourtListener API token (free from [courtlistener.com](https://www.courtlistener.com))
- OpenAI API key (optional, for AI reasoning features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/daka13/LegalReasonerX.git
   cd LegalReasonerX
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements-web.txt
   ```

3. **Run the application**
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

4. **Open your browser**
   Navigate to `http://localhost:8000`

### Alternative: Run with Docker (Coming Soon)
```bash
docker-compose up
```

## 📁 Project Structure

```
LegalReasonerX/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── api/                    # API endpoints
│   ├── services/               # Business logic
│   │   ├── precedent_service.py
│   │   ├── network_service.py
│   │   └── reasoning_service.py
│   └── utils/                  # Helper utilities
│       └── courtlistener.py
├── frontend/
│   ├── index.html              # Landing page
│   ├── citation-lookup.html    # Citation lookup page
│   ├── network-viz.html        # Network visualization
│   ├── opinion-analysis.html   # Opinion analysis
│   ├── reasoning.html          # AI reasoning framework
│   ├── css/
│   │   └── main.css           # Styles with micro-interactions
│   └── js/
│       └── utils.js           # Shared utilities
├── static/                     # Static assets
├── app.py                      # Original Streamlit app (preserved)
├── requirements.txt            # Streamlit app requirements
├── requirements-web.txt        # Web app requirements
└── README.md                   # Main documentation
```

## 🎯 Usage Guide

### 1. Configure API Keys
Visit the home page and enter your API keys:
- **CourtListener API Token** (Required): Get from [courtlistener.com](https://www.courtlistener.com/sign-in/)
- **OpenAI API Key** (Optional): Only needed for AI Reasoning features

Keys are stored securely in your browser's local storage.

### 2. Process a Citation
1. Navigate to **Citation Lookup**
2. Enter a legal citation (e.g., "520 U.S. 17")
3. Click **Process Citation**
4. View extracted precedent cases

### 3. Visualize the Network
1. After processing a citation, go to **Network Visualization**
2. Explore the interactive graph
3. Drag nodes to rearrange
4. Zoom and pan to navigate
5. Click nodes to highlight connections

### 4. Analyze Opinions
1. Navigate to **Opinion Analysis**
2. Select a case from the dropdown
3. Read base and precedent opinions
4. Copy or export opinion text

### 5. AI Reasoning Analysis
1. Go to **AI Reasoning Framework**
2. Select a case
3. Click **Run AI Analysis**
4. View extracted arguments and precedent analysis
5. Extract entities if needed
6. Export results in various formats

## 🔧 API Documentation

Once the application is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

### Key Endpoints

```
POST /api/process-citation      # Process legal citations
POST /api/generate-network      # Generate network visualization data
POST /api/extract-opinions      # Extract opinion texts
POST /api/analyze-reasoning     # AI-powered reasoning analysis
POST /api/extract-entities      # Extract legal entities
GET  /api/health               # Health check
```

## 🎨 Customization

### Styling
Edit `/frontend/css/main.css` to customize:
- Color palette (CSS variables in `:root`)
- Animations and transitions
- Component styles
- Responsive breakpoints

### Backend
- Add new endpoints in `/backend/main.py`
- Extend services in `/backend/services/`
- Add utilities in `/backend/utils/`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- CourtListener for providing the legal citations API
- OpenAI for GPT-4 API
- D3.js for interactive visualizations
- FastAPI for the excellent web framework

## 📧 Contact

**David Akinboro**
GitHub: [@daka13](https://github.com/daka13)
Project Link: [https://github.com/daka13/LegalReasonerX](https://github.com/daka13/LegalReasonerX)

## 🔄 Comparison: Streamlit vs Web Application

### Streamlit App (Original)
- ✅ Quick prototyping
- ✅ Easy to build
- ❌ Limited customization
- ❌ Basic UI
- ❌ Server-side only

### Web Application (New)
- ✅ Full control over UI/UX
- ✅ Modern, professional design
- ✅ Rich micro-interactions
- ✅ RESTful API
- ✅ Better performance
- ✅ Production-ready
- ✅ Mobile-responsive

---

**Note**: The original Streamlit application (`app.py`) is preserved and can still be run with `streamlit run app.py`.
