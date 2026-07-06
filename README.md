# AI Agent Marketplace

A small full-stack demo for browsing AI agents, running them one at a time, or chaining them into an A2A-style pipeline.

The project has:

- A FastAPI backend with three agent endpoints
- A static frontend built with HTML, CSS, and vanilla JavaScript
- Optional local LLM support through Ollama
- Deterministic fallback behavior so the app still responds if the model is unavailable

## What It Does

- Lets a user "log in" with a username and receive a fake bearer token
- Lists three available agents:
  - Resume Analyzer
  - Job Recommender
  - Cover Letter Generator
- Runs a single agent against pasted text
- Chains multiple agents together in sequence
- Shows structured output in the UI and lets you copy the result
- Includes sample inputs and per-agent documentation pages

## Project Goal

This project was built to explore how AI agents can be exposed through simple APIs and connected through an agent-to-agent protocol style workflow.

The idea behind it was not just to make a demo UI, but to show how:

- Individual agents can be wrapped behind clean API endpoints
- Multiple agents can be chained together in a workflow
- Structured outputs can move from one agent to the next
- A frontend can act as a lightweight marketplace for selecting and combining agents

## Why It Matters

An agent marketplace is useful because it turns AI behavior into something modular and reusable.

Instead of one large assistant doing everything, this design makes it possible to:

- Separate responsibilities across specialized agents
- Reuse the same backend services across different workflows
- Plug agents into pipelines for resume review, job matching, and letter generation
- Keep the system easier to extend later with more APIs and more agents

This is the main reason the A2A flow matters: it shows how one agent's output can become the next agent's input.

## What I Implemented

- A FastAPI backend with authentication, agent listing, and agent execution endpoints
- A frontend marketplace UI with login, agent cards, sample inputs, and output rendering
- Three agents:
  - Resume Analyzer
  - Job Recommender
  - Cover Letter Generator
- An agent-to-agent style pipeline where multiple agents run sequentially
- Local LLM integration through Ollama
- Safe fallback logic so the app still works if the LLM response is missing or malformed
- Copy-to-clipboard support and raw JSON view in the frontend
- Per-agent documentation pages explaining each agent's purpose

## Project Layout

- `backend/main.py` - FastAPI app, auth, agent registry, and API routes
- `backend/agents.py` - Prompting, parsing, and fallback logic for each agent
- `backend/llm.py` - Ollama client used by the backend
- `backend/requirements.txt` - Python dependencies
- `frontend/index.html` - Main UI
- `frontend/script.js` - Frontend behavior and API calls
- `frontend/style.css` - App styling
- `frontend/agent-docs/` - Agent-specific documentation pages
- `.gitignore` - Ignores virtualenv and Python cache files

## How The App Works

1. The frontend sends a login request with a username.
2. The backend returns a fake token and the frontend stores it in memory.
3. The frontend fetches the agent list from `/agents`.
4. When you run an agent, the frontend sends your input to `/run-agent`.
5. The backend tries to use Ollama at `http://localhost:11434/api/generate`.
6. If Ollama output is missing or malformed, the backend falls back to deterministic logic.

## Requirements

- Python 3.10+ recommended
- `pip`
- Ollama installed locally if you want live LLM responses
- A local model named `llama3`

## Setup

### 1) Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

### 2) Install backend dependencies

```powershell
pip install -r backend\requirements.txt
```

### 3) Start Ollama

In a separate terminal:

```powershell
ollama serve
```

If you do not already have the model, install it once:

```powershell
ollama pull llama3
```

### 4) Start the backend

From the project root:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 5) Start the frontend

In another terminal:

```powershell
cd frontend
python -m http.server 5500
```

Open the app in your browser:

```text
http://127.0.0.1:5500
```

## Using The App

1. Enter any username and click **Login**.
2. Paste a resume, profile, or other text into the input box.
3. Select one or more agents.
4. Run a single agent or chain multiple agents with A2A.
5. Copy the response or switch to raw view if you want the JSON payload.

The UI also includes sample inputs for:

- Frontend profile
- Backend profile
- Fresher profile
- Full-stack A2A flow
- Senior/lead profile

## API Endpoints

- `POST /login`
  - Body: `{ "username": "your-name" }`
  - Returns: fake bearer token

- `GET /agents`
  - Returns: the available agent cards shown in the UI

- `POST /run-agent`
  - Body: `{ "agent": "resume" | "job" | "cover", "input": "text" }`
  - Requires: `Authorization: Bearer <token>`

- `POST /run-pipeline`
  - Body: `{ "input": "text", "agents": ["resume", "job", "cover"] }`
  - Requires: `Authorization: Bearer <token>`

- `GET /`
  - Health check message from the API

## Agent Behavior

### Resume Analyzer

- Scores resume quality on a 0-100 scale
- Extracts visible skills
- Produces summary, feedback, and breakdown fields

### Job Recommender

- Returns 5 role recommendations
- Includes fit reasons, salary ranges, missing skills, next steps, and confidence
- Falls back to deterministic recommendations if the model output is unusable

### Cover Letter Generator

- Produces a short professional cover letter
- Uses the provided context or falls back to a template

## Notes

- Authentication is intentionally fake and only exists to gate the demo UI.
- The frontend is hard-coded to `http://127.0.0.1:8000`.
- CORS is open for local development.
- The app is designed to still produce usable output even without a live model response.

## Troubleshooting

- If the frontend says the backend is unreachable, make sure `uvicorn` is running on port `8000`.
- If outputs are generic, check that Ollama is running and `llama3` is installed.
- If PowerShell refuses to run the venv activation script, set the execution policy for the current process as shown above.
