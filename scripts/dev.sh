#!/bin/bash

# Start all development services

echo "🚀 Starting ReportForge AI Development Environment"

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis is not running. Starting Redis..."
    redis-server --daemonize yes
fi

# Start Celery worker in background
echo "📦 Starting Celery worker..."
cd api
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info &
CELERY_PID=$!
cd ..

# Start FastAPI server
echo "🔌 Starting FastAPI server..."
cd api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
API_PID=$!
cd ..

# Start React dev server
echo "⚛️  Starting React dev server..."
cd web
npm run dev &
WEB_PID=$!
cd ..

echo "✅ All services started!"
echo "   - API: http://localhost:8000"
echo "   - Frontend: http://localhost:5173"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $CELERY_PID $API_PID $WEB_PID; exit" INT
wait

