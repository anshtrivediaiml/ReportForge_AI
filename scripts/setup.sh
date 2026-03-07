#!/bin/bash

echo "🔧 Setting up ReportForge AI..."

# Backend setup
echo "📦 Setting up backend..."
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
echo "✅ Backend setup complete"
cd ..

# Frontend setup
echo "⚛️  Setting up frontend..."
cd web
npm install
cp .env.example .env
echo "✅ Frontend setup complete"
cd ..

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure .env files in api/ and web/"
echo "2. Start PostgreSQL and Redis"
echo "3. Run: ./scripts/dev.sh"

