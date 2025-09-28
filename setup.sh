#!/bin/bash

# QuizFlow Setup Script
echo "🚀 Setting up QuizFlow - AI-Powered Quiz Platform"
echo "================================================"

# Check if Python 3.10+ is available
python_version=$(python3 --version 2>&1 | grep -o "3\.[0-9]\+" | head -1)
if [[ $(echo "$python_version >= 3.10" | bc -l) -eq 0 ]]; then
    echo "❌ Python 3.10+ is required. Current version: $python_version"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

node_version=$(node --version | grep -o "v[0-9]\+" | grep -o "[0-9]\+")
if [[ $node_version -lt 18 ]]; then
    echo "❌ Node.js 18+ is required. Current version: v$node_version"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup backend
echo ""
echo "📦 Setting up backend..."
cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -e .

if [ $? -eq 0 ]; then
    echo "✅ Backend setup completed"
else
    echo "❌ Backend setup failed"
    exit 1
fi

# Setup frontend
echo ""
echo "🎨 Setting up frontend..."
cd ../frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Frontend setup completed"
else
    echo "❌ Frontend setup failed"
    exit 1
fi

# Create necessary directories
echo ""
echo "📁 Creating data directories..."
mkdir -p ../backend/data
echo "✅ Data directories created"

# Setup environment file
echo ""
echo "⚙️  Setting up environment..."
cd ../backend

if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# API Keys (add your own)
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here  
# GOOGLE_API_KEY=your_google_key_here

# Optional: Model configuration
# LITELLM_MODEL=gpt-3.5-turbo

# Debug mode
# QUIZFLOW_DEBUG=false
EOL
    echo "⚠️  Please add your API key to backend/.env file"
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
echo ""
echo "🔧 Making scripts executable..."
chmod +x ../run.sh
chmod +x ../setup.sh

echo ""
echo "🎉 QuizFlow setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Add your API key to backend/.env file"
echo "2. Run './run.sh' to start both backend and frontend"
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "🔗 Useful commands:"
echo "  ./run.sh          - Start both backend and frontend"
echo "  ./run.sh backend   - Start only backend"
echo "  ./run.sh frontend  - Start only frontend" 
echo ""
echo "📚 For more information, see README.md"
