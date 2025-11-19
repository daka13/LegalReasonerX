#!/bin/bash

# LegalReasonerX Web Application Startup Script

echo "🚀 Starting LegalReasonerX Web Application..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements-web.txt
    echo "✅ Dependencies installed!"
    echo ""
fi

# Start the application
echo "🌐 Starting server on http://localhost:8000"
echo "📚 API documentation available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
