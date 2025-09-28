#!/bin/bash

# QuizFlow Runner Script
echo "🚀 Starting QuizFlow - AI-Powered Quiz Platform"

# Function to start backend
start_backend() {
    echo "🔧 Starting backend server..."
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "❌ Virtual environment not found. Please run setup.sh first."
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        echo "⚠️  No .env file found. Creating basic template..."
        echo "OPENAI_API_KEY=your_api_key_here" > .env
        echo "Please add your API key to backend/.env file"
    fi
    
    # Start the API server
    echo "Starting FastAPI server on http://localhost:8000"
    quizflow-api &
    BACKEND_PID=$!
    
    # Wait for server to start (with better health check)
    echo "Waiting for server to start..."
    sleep 2
    
    # Try health check multiple times
    for i in {1..10}; do
        if curl -s --max-time 2 http://localhost:8000/ > /dev/null 2>&1; then
            echo "✅ Backend server started successfully"
            break
        elif [ $i -eq 10 ]; then
            echo "⚠️  Health check failed, but server may still be starting..."
            echo "Check server logs above for any errors"
            break
        else
            echo "  Attempt $i/10 - waiting..."
            sleep 1
        fi
    done
    
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting frontend server..."
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "❌ Node modules not found. Please run setup.sh first."
        exit 1
    fi
    
    # Start the development server
    echo "Starting React development server on http://localhost:3000"
    npm run dev &
    FRONTEND_PID=$!
    
    # Wait a moment for server to start
    sleep 5
    
    echo "✅ Frontend server started successfully"
    
    cd ..
}

# Function to stop all processes
cleanup() {
    echo ""
    echo "🛑 Stopping QuizFlow..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend server stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend server stopped"
    fi
    
    # Kill any remaining processes
    pkill -f "quizflow-api" 2>/dev/null
    pkill -f "npm run dev" 2>/dev/null
    
    echo "👋 QuizFlow stopped successfully"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Parse command line arguments
case "$1" in
    "backend")
        start_backend
        echo "Backend running. Press Ctrl+C to stop."
        wait $BACKEND_PID
        ;;
    "frontend")
        start_frontend
        echo "Frontend running. Press Ctrl+C to stop."
        wait $FRONTEND_PID
        ;;
    *)
        # Start both backend and frontend
        start_backend
        start_frontend
        
        echo ""
        echo "🎉 QuizFlow is now running!"
        echo "📱 Frontend: http://localhost:3000"
        echo "🔧 Backend API: http://localhost:8000"
        echo "📚 API Docs: http://localhost:8000/docs"
        echo ""
        echo "Press Ctrl+C to stop all services"
        
        # Wait for both processes
        wait
        ;;
esac
