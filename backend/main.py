from typing import Any, Dict, List

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agents import cover_letter_generator, job_recommender, resume_analyzer

app = FastAPI(title="AI Agent Marketplace API")

# -------- MODELS --------

class LoginRequest(BaseModel):
    username: str

class AgentRequest(BaseModel):
    agent: str
    input: str

class PipelineRequest(BaseModel):
    input: str = Field(..., min_length=1)
    agents: List[str]

# -------- FAKE AUTH --------

fake_tokens = {}
agent_registry: Dict[str, Dict[str, Any]] = {
    "resume": {
        "id": "resume",
        "name": "Resume Analyzer",
        "description": "Reviews resume text, extracts strengths, and gives clear feedback.",
        "how_to_use_url": "agent-docs/resume-analyzer.html",
        "skills": ["Resume Scoring", "Skill Extraction", "Feedback Generation", "Impact Analysis"],
        "capabilities": [
            "Scores resume quality on a normalized 0-100 scale",
            "Extracts key skills from profile text",
            "Generates actionable summary and feedback",
            "Provides section-level breakdown for clarity",
        ],
    },
    "job": {
        "id": "job",
        "name": "Job Recommender",
        "description": "Suggests matching job roles based on skills or profile context.",
        "how_to_use_url": "agent-docs/job-recommender.html",
        "skills": ["Role Matching", "Skill Gap Detection", "Career Guidance", "Job Prioritization"],
        "capabilities": [
            "Returns 5 role recommendations with reasons",
            "Includes salary range, missing skills, and next steps",
            "Supports A2A chaining from resume output",
            "Uses fallback logic for stable recommendations",
        ],
    },
    "cover": {
        "id": "cover",
        "name": "Cover Letter Generator",
        "description": "Generates a concise, professional cover letter from provided context.",
        "how_to_use_url": "agent-docs/cover-letter-gen.html",
        "skills": ["Professional Writing", "Personalization", "Role Targeting", "Concise Formatting"],
        "capabilities": [
            "Creates short recruiter-friendly cover letters",
            "Uses resume or job context for personalization",
            "Maintains clean structure with greeting and sign-off",
            "Supports final copy-ready output in UI",
        ],
    },
}

@app.post("/login")
def login(data: LoginRequest):
    if not data.username.strip():
        raise HTTPException(status_code=400, detail="Username is required")

    token = f"token_{data.username}"
    fake_tokens[token] = data.username
    return {"token": token}

def require_auth(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    token = authorization.split(" ", 1)[1]
    username = fake_tokens.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return username

# -------- AGENT LIST --------

@app.get("/")
def home():
    return {"message": "AI Agent Marketplace API is running"}

@app.get("/agents")
def list_agents():
    return list(agent_registry.values())

# -------- RUN SINGLE AGENT --------

@app.post("/run-agent")
def run_agent(req: AgentRequest, authorization: str | None = Header(default=None)):
    require_auth(authorization)

    if req.agent == "resume":
        return {"output": resume_analyzer(req.input)}

    elif req.agent == "job":
        return {"output": job_recommender(req.input)}

    elif req.agent == "cover":
        return {"output": cover_letter_generator(req.input)}

    raise HTTPException(status_code=400, detail="Invalid agent")

# -------- A2A PIPELINE --------

@app.post("/run-pipeline")
def run_pipeline(req: PipelineRequest, authorization: str | None = Header(default=None)):
    require_auth(authorization)

    if len(req.agents) < 2:
        raise HTTPException(status_code=400, detail="A2A requires at least two agents")

    invalid_agents = [agent for agent in req.agents if agent not in agent_registry]
    if invalid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agents: {', '.join(invalid_agents)}",
        )

    current_output = req.input
    steps = []

    for agent in req.agents:
        if agent == "resume":
            current_output = resume_analyzer(current_output)
        elif agent == "job":
            current_output = job_recommender(current_output)
        elif agent == "cover":
            current_output = cover_letter_generator(current_output)

        steps.append({"agent": agent, "output": current_output})

    return {"steps": steps, "final_output": current_output}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (fine for assignment)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
