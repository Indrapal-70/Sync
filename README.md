# Sync — Autonomous Multi-Agent Software Engineer

> Turn a single sentence into a fully built, tested, and reviewed codebase — automatically.

---

## 🚀 Overview

**Sync** is an autonomous multi-agent system that transforms a simple project idea into production-ready code.

Give it:

> *"Build a REST API for a book library"*

It delivers:

* Structured architecture
* Complete source code
* Automated test suite
* Debugged implementation
* Final quality review report

All without manual intervention.

---

## ⚙️ How It Works

Sync operates as a **sequential agent pipeline**, where each agent specializes in one stage of software development:

```
Idea → Planner → Coder → Tester → Debugger → Reviewer → Output
```

### 🔁 Execution Flow

1. **Planner** → Converts idea into structured tasks
2. **Coder** → Generates full codebase from tasks
3. **Tester** → Writes & executes test cases (pytest)
4. **Debugger** → Fixes failing tests automatically
5. **Reviewer** → Evaluates code quality and suggests improvements

If tests fail:

* Debugger patches the code
* Tester re-runs tests
* Loop continues (max 3 iterations)

---

## 🤖 Agents

| Agent        | Model                    | Responsibility              |
| ------------ | ------------------------ | --------------------------- |
| **Planner**  | `kimi-k2.5:cloud`        | Task decomposition          |
| **Coder**    | `qwen3-coder-next:cloud` | Code generation             |
| **Tester**   | `qwen3.5:cloud`          | Test generation & execution |
| **Debugger** | `minimax-m2.7:cloud`     | Error fixing & retries      |
| **Reviewer** | `qwen3.5:cloud`          | Code evaluation             |

---

## 🧠 Key Design Principles

* **Deterministic Pipeline** — No parallel execution, no race conditions
* **Self-healing Loop** — Automatic debug → retest cycle
* **Structured I/O** — JSON contracts between agents
* **Stateless Agents, Stateful System** — Redis handles execution state
* **Zero Local LLM Load** — Runs entirely on cloud models via Ollama

---

## 🏗️ Tech Stack

| Layer         | Technology                          |
| ------------- | ----------------------------------- |
| LLM Runtime   | Ollama (cloud models)               |
| Agents        | Python 3.11                         |
| Backend       | FastAPI                             |
| Orchestration | Celery + Redis                      |
| Automation    | OpenClaw                            |
| Frontend      | React + Vite + Tailwind             |
| Database      | SQLite (logs), Redis (state)        |
| Deployment    | Render (backend), Vercel (frontend) |
| CI/CD         | GitHub Actions                      |

---

## 📁 Project Structure

```
Sync/
├── agents/
│   ├── planner.py
│   ├── coder.py
│   ├── tester.py
│   ├── debugger.py
│   └── reviewer.py
│
├── backend/
│   ├── main.py
│   ├── orchestrator/
│   │   ├── pipeline.py
│   │   └── state.py
│   ├── models/
│   │   └── ollama_client.py
│   ├── schemas/
│   │   └── agent_io.py
│   └── db/
│       └── logger.py
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ProjectInput.jsx
```

---

## 🔥 Why Sync?

* Eliminates repetitive dev workflows
* Bridges idea → execution instantly
* Enforces testing and quality by design
* Scales into a fully autonomous engineering system

---

## 🧪 Example Use Cases

* MVP generation
* API scaffolding
* Internal tooling
* Rapid prototyping
* AI-assisted code audits

---

## 📌 Future Roadmap

* Parallel agent execution with dependency graph
* Multi-language support
* GitHub PR auto-generation
* Live execution dashboard
* Plug-in agent ecosystem

---

## 🧩 Philosophy

> Software development is a relay race.
> Sync doesn’t replace developers — it *runs the race for them.*

---

## ⚡ Getting Started

```bash
git clone <repo>
cd Sync
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

---

## 📄 License

MIT License
