# 🤖 Project Status Prompt for AI Assistants

Use this prompt to explain the current state of ReportForge AI to Claude or other AI assistants:

---

## Project: ReportForge AI - Technical Report Generation Platform

**ReportForge AI** is a full-stack SaaS application that automatically generates professionally formatted technical reports from codebases using a multi-agent AI system.

### Tech Stack
- **Backend**: FastAPI (Python) + Celery + Redis + SQLite/PostgreSQL
- **Frontend**: React 18 + TypeScript + Vite + Zustand + Tailwind CSS
- **Real-time**: WebSocket (FastAPI) + Redis pub/sub
- **Agents**: 4 Python agents (Parser, Planner, Writer, Builder) that process reports

### Current Status: ✅ PRODUCTION READY

All core features are implemented and working:
- File upload (chunked and full)
- Real-time progress tracking via WebSocket
- 4-stage agent pipeline with granular progress (0-100% per agent)
- Modern UI with animations and live updates
- Error handling and task management

### Architecture Flow

1. **User uploads files** → FastAPI stores in `inputs/` directory
2. **User clicks generate** → Creates job in database, queues Celery task
3. **Celery worker processes** → Runs 4 agents sequentially:
   - **Parser** (0-25%): Analyzes project, parses guidelines PDF with LLM
   - **Planner** (25-40%): Generates report outline with LLM
   - **Writer** (40-75%): Writes content section-by-section with LLM
   - **Builder** (75-100%): Assembles DOCX document
4. **Real-time updates** → Celery → Redis pub/sub → FastAPI WebSocket → React frontend
5. **Completion** → Job status updated, user can download report

### Key Files
- **Backend Task**: `api/app/tasks/report_tasks.py` - Main Celery task with progress tracking
- **WebSocket**: `api/app/routers/websocket.py` - Real-time updates endpoint
- **Frontend Store**: `web/src/store/jobStore.ts` - Zustand state management
- **Processing Page**: `web/src/pages/ProcessingPage.tsx` - Real-time progress UI

### Important Constraints
- **DO NOT MODIFY**: `agents/`, `utils/`, `main.py` (core agent system)
- **CAN MODIFY**: `api/app/`, `web/src/` (backend/frontend logic)
- **Celery**: Uses `solo` pool on Windows, `max_retries=0` (no auto-retry)
- **Database**: SQLite default, PostgreSQL ready

### Recent Fixes
- ✅ Fixed Celery continuous execution (disabled retries, added duplicate prevention)
- ✅ Fixed progress bars getting stuck (granular tracking for all agents)
- ✅ Fixed timestamp display (UTC to local conversion)
- ✅ Fixed log noise (filtering important logs only)
- ✅ Fixed page scroll (scrolls to top on mount)

### How It Works
1. Each agent sends progress updates via `broadcast_progress_sync()` → Redis
2. FastAPI WebSocket subscribes to Redis channel `job_updates:{job_id}`
3. WebSocket sends messages to React frontend
4. Zustand store updates state, UI re-renders with new progress
5. Progress bars move smoothly, logs appear in real-time

### Development Setup
```powershell
# Backend
cd api
celery -A app.core.celery_app worker --loglevel=info --pool=solo  # Terminal 1
uvicorn app.main:app --reload --port 8000  # Terminal 2

# Frontend
cd web
npm run dev  # Terminal 3
```

### Current Behavior
- Tasks only run when user explicitly clicks "Generate Report"
- Each agent progresses 0-100% with detailed sub-steps
- Real-time updates appear in UI within < 200ms
- Logs show important milestones (completions, errors, key steps)
- Active agent is prominently displayed at top of page

---

**Use this context when working on the project to understand the architecture and current implementation.**

