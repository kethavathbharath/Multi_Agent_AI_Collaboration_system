# Multi-Agent AI Collaboration System

A production-grade, state-graph orchestrator where multiple specialized AI agents collaborate dynamically to solve complex, multi-step user tasks.

---

## 🌟 Architecture & Flow

The system follows a multi-agent Directed Acyclic Graph (DAG) architecture built on **LangGraph**:

```
[User Input (Streamlit UI)]
         │
         ▼
 [FastAPI Backend] ── (REST API & Streaming)
         │
         ▼
[LangGraph Orchestration Graph]
  ├── 👔 Manager Agent    ── Task Decomposition into subtasks
  ├── 🔍 Research Agent   ── Factual data & background gathering
  ├── 📊 Analysis Agent   ── Synthesis & strategic evaluation
  ├── ✍️ Writer Agent     ── Final Markdown report generation
  └── 🛡️ Reviewer Agent   ── Audit feedback loop & quality scoring
         │
         ▼
 [Shared State Container] ◄──► [SQLite History & Execution Persistence]
```

---

## 🛠️ Technology Stack

- **Framework**: LangGraph & LangChain (`langgraph`, `langchain-core`, `langchain-community`)
- **Backend API**: FastAPI + Uvicorn
- **Frontend Dashboard**: Streamlit (with Glassmorphism CSS styling and agent activity trackers)
- **Database**: SQLite (built-in task & log persistence)
- **LLM Support**: OpenAI GPT-4o / Gemini / Configurable Mock LLM
- **Testing**: `pytest` test suite

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Virtual Environment Setup
Ensure Python 3.10+ is installed.

```bash
# Clone repository and navigate to root directory
cd Multi_Agent_AI_Collaboration_system

# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to configure your preferred LLM provider (`openai`, `google`, or `mock`):
```env
DEFAULT_LLM_PROVIDER=mock
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
MAX_REVIEW_ITERATIONS=2
```

---

## 💻 Running the Application

### Option A: Run FastAPI Backend
Launch the API server on `http://127.0.0.1:8000`:
```bash
.\.venv\Scripts\uvicorn backend.main:app --reload --port 8000
```
- Interactive API Docs (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Option B: Run Streamlit Frontend
Launch the interactive dashboard on `http://localhost:8501`:
```bash
.\.venv\Scripts\streamlit run frontend/app.py
```

---

## 🧪 Running Automated Tests

Run the complete pytest suite to verify all agent nodes, workflow transitions, and API endpoints:
```bash
.\.venv\Scripts\pytest.exe
```

Expected Output:
```text
============================= test session starts =============================
collected 6 items

tests\test_agents.py ...                                                 [ 50%]
tests\test_api.py ..                                                     [ 83%]
tests\test_workflow.py .                                                 [100%]

============================== 6 passed in 0.83s ==============================
```

---

## 📁 Repository Directory Structure

```text
Multi_Agent_AI_Collaboration_system/
├── backend/                # FastAPI application & SQLite persistence
│   ├── db.py               # Database schemas & CRUD operations
│   ├── main.py             # FastAPI REST endpoints & SSE streaming
│   └── schemas.py          # Pydantic API payload schemas
├── config/                 # Application configuration & Pydantic settings
│   └── settings.py
├── core/                   # LangGraph multi-agent logic
│   ├── agents/             # Individual agent implementations
│   │   ├── manager.py      # Manager Agent (Decomposition)
│   │   ├── research.py     # Research Agent (Fact Gathering)
│   │   ├── analysis.py     # Analysis Agent (Evaluation)
│   │   ├── writer.py       # Writer Agent (Report Generation)
│   │   └── reviewer.py     # Reviewer Agent (Quality Audit)
│   ├── llm.py              # Provider LLM abstraction & Mock fallback
│   ├── state.py            # Shared AgentState TypedDict schema
│   └── workflow.py         # Compiled LangGraph StateGraph
├── docs/                   # Product & Technical Requirements Documents
├── frontend/               # Streamlit web UI application
│   └── app.py
├── tests/                  # Pytest test suite
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_workflow.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```
