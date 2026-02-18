#!/bin/bash

# Protocol Animator - Setup Script

echo "🔬 Protocol Animator Setup"
echo "======================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

echo "✅ Python dependencies installed"

# Install Node dependencies
echo ""
echo "📦 Installing Node.js dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi

echo "✅ Node.js dependencies installed"

# Create output directory
mkdir -p backend/output

echo ""
echo "✨ Setup complete!"
echo ""
echo "To run the application:"
echo "  1. Backend:  cd backend && uvicorn main:app --reload --port 8000"
echo "  2. Frontend: npm run dev"
echo ""
echo "Or use npm scripts:"
echo "  - npm run server (backend)"
echo "  - npm run dev (frontend)"
echo ""
echo "Access the app at: http://localhost:3000"
