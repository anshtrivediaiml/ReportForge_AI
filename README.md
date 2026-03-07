# ReportForge AI - Production-Ready Report Generation Platform

A cutting-edge, portfolio-worthy SaaS platform that transforms codebases into professionally formatted technical documentation using AI agents.

## 🎯 Features

- **AI-Powered Analysis**: 5 specialized agents (Parser, Planner, Writer, Builder) work together
- **Real-Time Updates**: WebSocket-based live progress tracking with animated UI
- **Professional Formatting**: IEEE, ACM, or custom formatting guidelines
- **Modern UI**: Stunning dark theme with glassmorphism effects and smooth animations
- **Production Ready**: FastAPI backend, React frontend, PostgreSQL, Celery, Redis

## 🏗️ Architecture

```
report_generator_ai/
├── agents/              # Existing Python agents (DO NOT MODIFY)
├── utils/               # Existing utilities (DO NOT MODIFY)
├── main.py             # Existing report generator (DO NOT MODIFY)
│
├── api/                 # FastAPI Backend
│   ├── app/
│   │   ├── main.py     # FastAPI application
│   │   ├── routers/    # API endpoints
│   │   ├── services/   # Business logic
│   │   ├── tasks/      # Celery tasks
│   │   └── models.py   # Database models
│   └── requirements.txt
│
└── web/                 # React Frontend
    ├── src/
    │   ├── pages/      # Page components
    │   ├── components/ # UI components
    │   ├── store/      # State management
    │   └── services/   # API clients
    └── package.json
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### Backend Setup

```bash
# Navigate to API directory
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your database and Redis URLs
# DATABASE_URL=postgresql://user:password@localhost:5432/reportforge
# REDIS_URL=redis://localhost:6379/0

# Run database migrations (if using Alembic)
# alembic upgrade head

# Start Celery worker (in separate terminal)
celery -A app.core.celery_app worker --loglevel=info

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
# Navigate to web directory
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📚 Documentation

- [API Documentation](docs/API.md) - Complete API reference
- [Architecture Guide](docs/ARCHITECTURE.md) - System design and architecture
- [Development Guide](docs/DEVELOPMENT.md) - Local development setup
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment

## 🎨 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM
- **Celery** - Distributed task queue
- **Redis** - Message broker and cache
- **WebSockets** - Real-time communication

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Zustand** - State management
- **Axios** - HTTP client

## 🔧 Configuration

### Environment Variables

**Backend (`api/.env`):**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/reportforge
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=104857600
```

**Frontend (`web/.env`):**
```env
VITE_API_URL=http://localhost:8000
```

## 📝 Usage

1. **Upload Files**: Go to `/upload` and upload your guidelines PDF and project ZIP
2. **Monitor Progress**: Watch real-time updates on the processing page
3. **Download Report**: Once complete, download your professionally formatted report

## 🧪 Testing

```bash
# Backend tests
cd api
pytest

# Frontend tests
cd web
npm test
```

## 📦 Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions for:
- Railway.app
- Render.com
- Docker
- Self-hosted

## 🤝 Contributing

This is a portfolio project. Feel free to fork and customize for your needs!

## 📄 License

MIT License - feel free to use this in your portfolio!

## 🎯 Project Status

✅ Backend API complete
✅ Frontend UI complete
✅ Real-time updates working
✅ File upload implemented
✅ Report generation integrated
✅ Production-ready structure

---

Built with ❤️ for showcasing modern full-stack development skills
