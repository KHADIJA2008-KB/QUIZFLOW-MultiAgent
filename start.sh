#!/bin/bash

# QuizFlow Production Starter
echo "🚀 Starting QuizFlow Production System"
echo "======================================"

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: backend/.env not found"
    echo "   Copy backend/env.example to backend/.env and add your OpenAI API key"
    exit 1
fi

# Start backend
echo "🔧 Starting backend server..."
cd backend
source venv/bin/activate 2>/dev/null || {
    echo "❌ Virtual environment not found. Run: npm run setup"
    exit 1
}

python -m uvicorn src.quizflow.api:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Backend started successfully"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend server..."
cd ../frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ Frontend dependencies not installed. Run: npm run setup"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

npm run preview &
FRONTEND_PID=$!

# Wait for frontend
sleep 3

echo ""
echo "🎉 QuizFlow is now running!"
echo "=========================="
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT
wait
