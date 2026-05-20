# 🚀 SYNC — Real-Time Multi-Agent Workflow Orchestration Platform

> **SYNC** is a full-stack web application that orchestrates multiple AI agents to execute complex workflows in real-time. Break down goals into tasks, watch AI agents work through them live, and see results stream to your browser via WebSocket.

---

## 🎯 What is SYNC?

SYNC is a production-ready orchestration platform that:

- **Plans workflows** using **Mistral** (The Thinker) to break down user goals into actionable tasks.
- **Executes tasks** with a fleet of specialized AI agents (Coder, Tester, Debugger, Reviewer) powered by **DeepSeek-Coder** (The Builder) and Mistral.
- **Streams everything live** via Redis Pub/Sub → WebSocket to React frontend, with real-time model health monitoring.
- **Persists data** in PostgreSQL with real-time log aggregation and performance stats.
- **Provides a polished UI** with 5 feature-rich pages: Orchestration Dashboard, Workflows Kanban, Workflow Details (with Agent Output Drawers), Agent Fleet Monitor, and Node Builder.

---

## 📋 Architecture Overview

### Tech Stack

**Backend:**
- FastAPI (async Python web framework)
- PostgreSQL (relational database)
- Redis (pub/sub messaging & caching)
- Ollama + Mistral (Thinker) & DeepSeek-Coder (Builder)
- SQLAlchemy (ORM)

**Frontend:**
- React 18 + TypeScript
- Zustand (state management)
- Axios (HTTP client)
- Vite (build tool)
- TailwindCSS (styling)

**Infrastructure:**
- Docker & Docker Compose
- Git for version control

### Data Flow

```
User creates workflow
         ↓
Frontend sends POST /api/workflows
         ↓
Backend saves to PostgreSQL
         ↓
WebSocket broadcasts "workflow_created" event
         ↓
Frontend updates UI in real-time
         ↓
User clicks "Execute"
         ↓
Ollama/Mistral plans tasks (or fallback tasks)
         ↓
Tasks saved to PostgreSQL
         ↓
Real agents (Coder, Tester, Debugger, Reviewer) execute an E2E pipeline
         ↓
Each status update & skill call → Redis → WebSocket → Frontend
         ↓
User sees live progress, agent outputs, and model health
```

---

## 🛠️ Prerequisites

Install these before running SYNC:

### Required
- **Docker** & **Docker Compose** ([download](https://www.docker.com/products/docker-desktop))
- **Python 3.11+** ([download](https://www.python.org/downloads/))
- **Node.js 18+** ([download](https://nodejs.org/))
- **Git** ([download](https://git-scm.com/))

### Required AI Engine
- **Ollama** ([download](https://ollama.ai)) — required for running the local agents.
- Run `ollama pull mistral:latest` and `ollama pull deepseek-coder:6.7b` before starting execution.

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Indrapal-70/Sync.git
cd Sync
```

### 2. Start Infrastructure (PostgreSQL, Redis, Ollama)

```bash
cd infra
docker compose up -d
```

**What this starts:**
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`
- Ollama on `localhost:11434` (with Mistral and DeepSeek-Coder models)

Verify all services are running:
```bash
docker compose ps
```

### 3. Set Up Backend

```bash
cd ../backend
```

**Create virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Create `.env` file in `backend/` directory:**
```env
DATABASE_URL=postgresql://sync_user:sync_pass@localhost:5432/sync_db
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
APP_ENV=development
SECRET_KEY=your-secret-key-change-this
```

**Start backend server:**
```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
[SYNC] Starting up...
[SYNC] Database tables verified
[SYNC] Redis broadcaster started
Uvicorn running on http://0.0.0.0:8000
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) to see interactive API documentation.

### 4. Set Up Frontend

```bash
cd ../frontend
```

**Create `.env` file in `frontend/` directory:**
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

**Install dependencies:**
```bash
npm install
```

**Start development server:**
```bash
npm run dev
```

Frontend will be running at [http://localhost:5173](http://localhost:5173).

---

## 🎬 Quick Start Guide

### 1. Open the Frontend

Navigate to [http://localhost:5173](http://localhost:5173)

You should see:
- ✅ Green "Connected" indicator in sidebar (WebSocket live)
- Dashboard with workflow statistics
- Navigation menu with 5 pages

### 2. Create a Workflow

- Click **"+ New Workflow"** button
- Enter a name: `"Build REST API with Authentication"`
- Enter a description: `"Create a secure REST API with JWT auth, user management, and role-based access control"`
- Click **Create**

### 3. Execute the Workflow

- Click the **"Execute"** button on the workflow card
- Watch the magic:
  - ✨ Ollama/Mistral plans tasks from your description
  - 📋 Tasks appear in the Kanban board
  - 🔄 Real LLM agents execute a full Coder → Tester → Debugger → Reviewer pipeline
  - 📊 DAG canvas shows real-time progress and live model health indicators
  - 📝 Logs stream live to the log panel

### 4. Monitor Execution

- **Orchestration Page**: See system-wide stats and health
- **Workflows Kanban**: Drag and drop tasks between columns
- **Workflow Details**: View DAG graph and detailed logs
- **Agent Fleet**: See which agents are running and what they're working on
- **Node Builder**: Build custom workflows visually

### 5. View Results

Once execution completes:
- Workflow status changes to `completed` or `failed`
- Task output data is stored and displayed
- Final logs show execution summary
- Workflow can be archived or re-executed

---

## 🏗️ Project Structure

```
SYNC/
├── backend/                    # FastAPI server
│   ├── app/
│   │   ├── core/              # Configuration & settings
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── agents/            # AI agent implementations
│   │   ├── websocket/         # WebSocket connection manager
│   │   └── database/          # DB session & initialization
│   ├── main.py               # FastAPI app entry point
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables
│   └── venv/                  # Python virtual environment
│
├── frontend/                   # React + TypeScript app
│   ├── src/
│   │   ├── pages/             # Feature pages (5 main pages)
│   │   ├── components/        # Reusable React components
│   │   ├── services/          # API & WebSocket services
│   │   ├── store/             # Zustand state management
│   │   ├── websocket/         # WebSocket hook
│   │   ├── types/             # TypeScript interfaces
│   │   ├── hooks/             # Custom React hooks
│   │   └── lib/               # Utilities & helpers
│   ├── index.html             # HTML entry point
│   ├── package.json           # Node dependencies
│   ├── .env                   # Environment variables
│   └── vite.config.ts         # Vite configuration
│
├── infra/                      # Docker infrastructure
│   └── docker-compose.yml     # PostgreSQL, Redis, Ollama
│
└── README.md                   # This file
```

---

## 🔌 API Endpoints

### Workflows

```
POST   /api/workflows              # Create workflow
GET    /api/workflows              # List all workflows
GET    /api/workflows/{id}         # Get workflow details
PATCH  /api/workflows/{id}         # Update workflow
DELETE /api/workflows/{id}         # Delete workflow
POST   /api/workflows/{id}/execute # Execute workflow (start agent loop)
```

### Tasks

```
POST   /api/tasks                  # Create task
GET    /api/tasks                  # List tasks (filter by workflow_id)
GET    /api/tasks/{id}             # Get task details
PATCH  /api/tasks/{id}             # Update task status
DELETE /api/tasks/{id}             # Delete task
```

### Logs

```
GET    /api/logs                   # List logs (filter by workflow_id, limit)
POST   /api/logs                   # Create log entry
```

### WebSocket

```
WS     /ws/{client_id}             # Real-time event stream
```

---

## 📡 Real-Time Event System

SYNC uses Redis Pub/Sub to broadcast events to all connected clients:

### Event Types

- **`workflow_created`** — New workflow created
- **`workflow_updated`** — Workflow status changed (pending → running → completed/failed)
- **`workflow_deleted`** — Workflow removed
- **`task_created`** — New task in workflow
- **`task_updated`** — Task status changed (pending → running → completed/failed)
- **`task_deleted`** — Task removed
- **`log_created`** — New log entry
- **`agent_status_changed`** — Agent state update

Each event has:
```json
{
  "event": "workflow_updated",
  "payload": { "id": "...", "status": "running" },
  "timestamp": "2026-05-17T10:30:00.000Z"
}
```

---

## 🧪 Testing & Verification

### Test 1: API Connectivity

```bash
# Terminal with backend running

# Create workflow via curl
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Workflow","description":"Testing SYNC"}'

# Should return workflow JSON with status="pending"
```

### Test 2: WebSocket Real-Time

1. Open [http://localhost:5173](http://localhost:5173)
2. Open browser DevTools (F12)
3. Go to Console
4. Should see: `[WS] Connected`
5. Create a workflow in the UI
6. Console should log incoming WebSocket event

### Test 3: Full Execution Loop

1. Create workflow: **"Build a Python CLI tool for file processing"**
2. Execute it
3. Watch:
   - ✅ Tasks appear (3-6 generated by Mistral)
   - ✅ Each task progresses through running → completed/failed
   - ✅ Logs fill with real-time entries
   - ✅ DAG canvas updates without page refresh
   - ✅ Final status shows when complete

### Test 4: Ollama Planner (LLM Integration)

1. Ensure Ollama is running: `docker compose ps`
2. Create workflow with detailed description
3. Execute
4. Check if tasks are intelligent (from Mistral) or fallback (generic 3 tasks)

---

## 🚨 Common Issues & Solutions

### Issue: Docker containers not starting

**Solution:**
```bash
docker compose down
docker compose up -d
docker compose logs
```

### Issue: PostgreSQL connection error

**Solution:** Verify `.env` has correct `DATABASE_URL`:
```
DATABASE_URL=postgresql://sync_user:sync_pass@localhost:5432/sync_db
```

Wait 10 seconds after `docker compose up` (DB needs to initialize).

### Issue: WebSocket not connecting

**Solution:**
1. Verify backend is running on port 8000
2. Check frontend `.env` has `VITE_WS_URL=ws://localhost:8000`
3. Refresh browser

### Issue: Tasks not being created when executing

**Solution:**
1. Check Ollama is running: `curl http://localhost:11434/api/tags`
2. If Ollama fails, fallback tasks should still be created (3 default tasks)
3. Check backend logs for errors

---

## 📊 Database Schema

### Workflows Table
```
id (UUID)           Primary key
name (String)       Workflow name
description (Text)  Optional description
status (String)     pending | running | completed | failed
created_at (Time)   Timestamp
updated_at (Time)   Timestamp
```

### Tasks Table
```
id (UUID)           Primary key
workflow_id (UUID)  Foreign key to workflows
name (String)       Task name
description (Text)  Task description
status (String)     pending | running | completed | failed
agent_name (String) Which agent handles this task
input_data (JSON)   Task input parameters
output_data (JSON)  Task result/output
created_at (Time)   Timestamp
updated_at (Time)   Timestamp
```

### WorkflowLogs Table
```
id (UUID)           Primary key
workflow_id (UUID)  Foreign key to workflows
task_id (UUID)      Optional task reference
level (String)      info | warning | error | debug
message (Text)      Log message
created_at (Time)   Timestamp
```

---

## 🎨 Frontend Pages

### 1. **Orchestration Dashboard**
   - System health overview
   - Workflow statistics (count by status)
   - Recent alerts and warnings
   - Quick-start workflow creation

### 2. **Workflows Kanban**
   - Kanban board with columns: Pending → Running → Completed → Failed
   - Drag-and-drop tasks between columns
   - Execute button on each workflow card
   - Real-time status updates

### 3. **Workflow Details**
   - Directed Acyclic Graph (DAG) of tasks
   - Live progress visualization
   - Node Builder UI and Detailed Task Information Drawer (with specific Agent outputs and model usage summary)
   - Real-time log stream with filtering

### 4. **Agent Fleet Monitor**
   - View active agents running tasks
   - CPU/RAM usage per agent
   - Current task assignment
   - Agent type badges (programmer, tester, researcher, etc.)

### 5. **Node Builder** (Visual Workflow Designer)
   - React Flow canvas for building workflows
   - Add/remove task nodes
   - Connect tasks with edges
   - Preview execution flow

---

## 🔄 Workflow Execution Flow

```
1. User creates workflow with description
   ↓
2. Workflow saved to DB (status="pending")
   ↓
3. User clicks Execute
   ↓
4. Backend calls Ollama/Mistral to plan tasks
   ↓
5. Tasks created in DB (status="pending")
   ↓
6. Pipeline Orchestrator routes task to the Coder Agent
   ↓
7. For each task:
   a. Status changes to "running"
   b. Agent Pipeline Executes: Coder → Tester → (if failed) Debugger → Reviewer
   c. Real Python code generation, execution, and review via local LLMs
   d. Status changes to "completed" or "failed"
   e. Agent outputs and model usage summaries stored
   ↓
8. All task updates stream via WebSocket
   ↓
9. Frontend updates in real-time (no refresh needed)
   ↓
10. Workflow completes (all tasks done)
    ↓
11. Final status: "completed" or "failed"
```

---

## 🚀 Deployment (Production)

For production deployment:

1. **Environment variables:**
   ```env
   APP_ENV=production
   SECRET_KEY=<generate-strong-random-key>
   DATABASE_URL=<production-db-url>
   REDIS_URL=<production-redis-url>
   ```

2. **Build frontend:**
   ```bash
   cd frontend
   npm run build
   ```

3. **Run backend with Gunicorn:**
   ```bash
   pip install gunicorn
   gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

4. **Use nginx** as reverse proxy for frontend static files

5. **Enable HTTPS** with Let's Encrypt SSL certificate

---

## 📚 Development Workflow

### Running Tests

```bash
cd backend
pytest tests/
```

### Code Formatting

```bash
# Backend
black app/
flake8 app/

# Frontend
npm run lint
npm run format
```

### Building for Production

```bash
# Frontend
npm run build

# Backend
# Use gunicorn (see Deployment section)
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test locally
4. Commit: `git commit -m "feat: add amazing feature"`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License — see `LICENSE` file for details.

---

## 💬 Support & Questions

- 📖 **Full API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (when backend is running)
- 🐛 **Report Issues:** [GitHub Issues](https://github.com/Indrapal-70/Sync/issues)
- 💡 **Feature Requests:** [GitHub Discussions](https://github.com/Indrapal-70/Sync/discussions)

---

## 🎉 Features Implemented

- ✅ Real AI agent pipeline (Coder, Tester, Debugger, Reviewer) using Dual-Model architecture (Mistral & DeepSeek-Coder).
- ✅ Real-time WebSocket model health and active skill routing visualization.
- ✅ E2E Pipeline Orchestrator with skill-based model routing.
- ✅ Custom visual design, including new Node Detail drawers with real agent outputs.

## 🔜 What's Next?

- Add workflow templating and presets
- Implement task retry logic with exponential backoff
- Add workflow scheduling (cron jobs)
- Multi-user support with authentication


 SYNC v1.0.0 — Real-Time Multi-Agent Orchestration
```
