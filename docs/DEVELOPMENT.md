# Development Guide

## Local Development Setup

### Step 1: Clone and Setup

```bash
git clone <repository>
cd report_generator_ai
```

### Step 2: Backend Setup

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb reportforge  # PostgreSQL command

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Step 3: Frontend Setup

```bash
cd web

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with API URL
```

### Step 4: Start Services

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - PostgreSQL:**
```bash
# Already running as service
```

**Terminal 3 - Celery Worker:**
```bash
cd api
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

**Terminal 4 - FastAPI Server:**
```bash
cd api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 5 - React Dev Server:**
```bash
cd web
npm run dev
```

## Development Workflow

1. Make changes to backend or frontend
2. Hot reload is enabled for both
3. Check API docs at http://localhost:8000/docs
4. Test WebSocket connections in browser console

## Debugging

### Backend
- Check FastAPI logs in terminal
- Check Celery worker logs
- Use FastAPI's `/docs` endpoint for API testing

### Frontend
- Use React DevTools
- Check browser console for WebSocket messages
- Network tab for API calls

## Common Issues

### Database Connection Error
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database exists: `createdb reportforge`

### Redis Connection Error
- Ensure Redis is running: `redis-server`
- Check REDIS_URL in .env

### WebSocket Connection Failed
- Ensure backend is running on port 8000
- Check CORS_ORIGINS includes frontend URL
- Verify WebSocket endpoint: `/ws/{job_id}`

### Celery Tasks Not Running
- Ensure Celery worker is started
- Check Redis connection
- Verify task imports in `app/tasks/report_tasks.py`

## Code Organization

### Backend Structure
```
api/app/
├── main.py          # FastAPI app entry
├── config.py        # Settings
├── database.py      # DB connection
├── models.py        # SQLAlchemy models
├── routers/         # API endpoints
├── services/        # Business logic
├── tasks/           # Celery tasks
└── schemas/         # Pydantic models
```

### Frontend Structure
```
web/src/
├── pages/           # Route pages
├── components/      # Reusable components
├── store/           # Zustand stores
├── services/        # API clients
├── hooks/           # Custom hooks
└── utils/           # Utilities
```

## Testing

```bash
# Backend
cd api
pytest tests/

# Frontend
cd web
npm test
```

## Building for Production

```bash
# Backend
cd api
# No build needed, just deploy

# Frontend
cd web
npm run build
# Output in dist/
```

