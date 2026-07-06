import json
import re

from .llm import call_llm

def resume_analyzer(resume_text: str):
    prompt = f"""
You are a strict resume evaluator for entry-level software engineers.

SCORING RUBRIC:

skills_depth (0–10):
- 0–3: basic or vague skills
- 4–6: relevant but limited stack
- 7–10: strong modern stack (React, APIs, cloud, etc.)

impact_proof (0–10):
- 0–3: no measurable impact
- 4–6: some projects but vague results
- 7–10: clear metrics (%, users, scale)

clarity (0–10):
- 0–3: unclear or messy
- 4–6: understandable
- 7–10: clean, concise, structured

FINAL SCORE:
score = (skills_depth + impact_proof + clarity) / 3

STRICT RULES:
- If strong skills + measurable impact → score must be >= 7
- Do NOT give random low scores
- Return ONLY JSON

Format:
{{
  "score": 0,
  "summary": "",
  "skills": [],
  "feedback": "",
  "breakdown": {{
    "skills_depth": 0,
    "impact_proof": 0,
    "clarity": 0
  }}
}}

Resume:
{resume_text}
"""
    llm_output = call_llm(prompt)
    parsed = _extract_json_object(llm_output)
    return json.dumps(_normalize_resume_analysis(parsed, resume_text), indent=2)


def job_recommender(skills_text: str):
    prompt = f"""
You are a career assistant.
Generate practical and personalized job recommendations.

STRICT RULE:
Return ONLY valid JSON. No explanation. No markdown.

JSON schema:
{{
  "jobs": [
    {{
      "title": "",
      "fit_reason": "",
      "salary_range_usd": "",
      "missing_skills": [],
      "next_step": "",
      "confidence": ""
    }}
  ]
}}

Requirements:
- Give exactly 5 jobs.
- Keep each fit_reason under 25 words.
- Salary should be realistic US ranges like "90k-120k".
- next_step must be a concrete action the user can do this week.

Candidate profile:
{skills_text}
"""
    llm_output = call_llm(prompt)

    # Validate the model output. If it is malformed, return reliable fallback jobs.
    validated = _extract_json_object(llm_output)
    if isinstance(validated, dict):
        jobs = validated.get("jobs")
        if isinstance(jobs, list) and jobs:
            return json.dumps(validated, indent=2)

    # Some models may return a raw list instead of {"jobs": [...]}
    if isinstance(validated, list) and validated:
        return json.dumps({"jobs": validated}, indent=2)

    return json.dumps(_fallback_jobs(skills_text), indent=2)


def _extract_json_object(raw: str):
    if not raw:
        return None

    cleaned = raw.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _extract_skills(profile_text: str):
    parsed = _extract_json_object(profile_text)
    if parsed and isinstance(parsed.get("skills"), list):
        return [str(skill).lower() for skill in parsed["skills"]]

    tokens = re.findall(r"[a-zA-Z\+\#\.]{2,}", profile_text.lower())
    return list(dict.fromkeys(tokens))


def _extract_resume_skills(text: str):
    known_skills = [
        "react", "typescript", "javascript", "html", "css", "redux", "node", "express",
        "fastapi", "django", "python", "java", "spring", "postgresql", "mysql", "docker",
        "aws", "git", "kubernetes", "rest", "api", "pytest", "jest", "testing",
    ]
    lower = text.lower()
    return [skill for skill in known_skills if skill in lower]


def _extract_score(raw_score):
    if isinstance(raw_score, (int, float)):
        return int(raw_score)

    if isinstance(raw_score, str):
        match = re.search(r"\d{1,3}", raw_score)
        if match:
            return int(match.group(0))

    return None


def _fallback_resume_analysis(resume_text: str):
    skills = _extract_resume_skills(resume_text)
    metric_hits = len(re.findall(r"(\d+%|\d+\s?k\+?|\d+\s?users?|\d+\s?years?)", resume_text.lower()))
    impact_words = len(re.findall(r"\b(built|improved|reduced|designed|led|optimized|shipped)\b", resume_text.lower()))
    tool_hits = len(re.findall(r"\b(docker|aws|git|test|testing|ci|cd|api|postgresql|mysql)\b", resume_text.lower()))

    skills_depth = min(30, 8 + len(skills) * 2)
    impact_proof = min(40, 8 + metric_hits * 10 + min(impact_words, 3) * 3)
    clarity = min(30, 12 + min(tool_hits, 6) * 3)

    score = max(45, min(98, skills_depth + impact_proof + clarity))

    feedback = (
        "Strong technical stack and measurable achievements. "
        "To improve further, add role-specific keywords, link 1-2 flagship projects, "
        "and quantify business impact for each major bullet."
    )

    return {
        "score": score,
        "summary": "Good resume with strong impact signals and modern engineering stack.",
        "skills": [s.title() for s in skills],
        "feedback": feedback,
        "breakdown": {
            "skills_depth": skills_depth,
            "impact_proof": impact_proof,
            "clarity": clarity,
        },
    }


def _normalize_resume_analysis(parsed, resume_text: str):
    fallback = _fallback_resume_analysis(resume_text)
    if not isinstance(parsed, dict):
        return fallback

    score = _extract_score(parsed.get("score"))
    if score is None:
        score = fallback["score"]
    # Guard against clearly unrealistic low scores from model glitches.
    if score < 20 and fallback["score"] >= 60:
        score = fallback["score"]
    score = max(0, min(100, score))

    skills = parsed.get("skills")
    if not isinstance(skills, list) or not skills:
        skills = fallback["skills"]
    else:
        skills = [str(s).strip() for s in skills if str(s).strip()]
        if not skills:
            skills = fallback["skills"]

    feedback = parsed.get("feedback")
    if not isinstance(feedback, str) or not feedback.strip():
        feedback = fallback["feedback"]

    summary = parsed.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        summary = fallback["summary"]

    breakdown = parsed.get("breakdown")
    if not isinstance(breakdown, dict):
        breakdown = fallback["breakdown"]
    else:
        breakdown = {
            "skills_depth": int(breakdown.get("skills_depth", fallback["breakdown"]["skills_depth"])),
            "impact_proof": int(breakdown.get("impact_proof", fallback["breakdown"]["impact_proof"])),
            "clarity": int(breakdown.get("clarity", fallback["breakdown"]["clarity"])),
        }

    return {
        "score": score,
        "summary": summary,
        "skills": skills,
        "feedback": feedback,
        "breakdown": breakdown,
    }


def _fallback_jobs(profile_text: str):
    skills = _extract_skills(profile_text)
    profile_lower = profile_text.lower()

    def has(*items):
        return any(item.lower() in skills or item.lower() in profile_lower for item in items)

    recommendations = []

    if has("react", "javascript", "typescript", "html", "css"):
        recommendations.append(
            {
                "title": "Frontend Developer",
                "fit_reason": "Strong match with modern UI stack and component-based development.",
                "salary_range_usd": "90k-130k",
                "missing_skills": ["performance profiling", "accessibility audits"],
                "next_step": "Build a polished portfolio project and add Lighthouse and a11y metrics.",
                "confidence": "high",
            }
        )

    if has("python", "fastapi", "django", "api", "postgresql"):
        recommendations.append(
            {
                "title": "Backend Engineer",
                "fit_reason": "Good alignment with API design, Python services, and relational databases.",
                "salary_range_usd": "100k-145k",
                "missing_skills": ["system design", "distributed caching"],
                "next_step": "Publish one API case study covering latency, scaling, and testing strategy.",
                "confidence": "high",
            }
        )

    if has("aws", "docker", "kubernetes", "devops", "ci", "cd"):
        recommendations.append(
            {
                "title": "Platform/DevOps Engineer",
                "fit_reason": "Cloud and deployment tooling suggest strong infra execution potential.",
                "salary_range_usd": "110k-155k",
                "missing_skills": ["terraform", "observability stack ownership"],
                "next_step": "Create an IaC demo with monitoring dashboards and incident runbook.",
                "confidence": "medium",
            }
        )

    if has("sql", "postgresql", "mysql", "pandas", "excel", "analytics"):
        recommendations.append(
            {
                "title": "Data Analyst",
                "fit_reason": "Skill profile supports analysis, reporting, and business insights work.",
                "salary_range_usd": "75k-110k",
                "missing_skills": ["experiment design", "dashboard storytelling"],
                "next_step": "Ship a public dashboard with one actionable business recommendation.",
                "confidence": "medium",
            }
        )

    if has("java", "spring", "spring boot", "microservices"):
        recommendations.append(
            {
                "title": "Java Software Engineer",
                "fit_reason": "Java ecosystem experience maps well to enterprise backend teams.",
                "salary_range_usd": "95k-140k",
                "missing_skills": ["messaging systems", "resilience patterns"],
                "next_step": "Implement a microservice with retries, circuit breaker, and integration tests.",
                "confidence": "medium",
            }
        )

    # Ensure exactly 5 recommendations for consistent UI behavior.
    defaults = [
        {
            "title": "Full Stack Developer",
            "fit_reason": "Balanced profile can support end-to-end feature ownership.",
            "salary_range_usd": "95k-140k",
            "missing_skills": ["architecture communication", "production incident handling"],
            "next_step": "Create one end-to-end app and document tradeoffs in a short design note.",
            "confidence": "medium",
        },
        {
            "title": "QA Automation Engineer",
            "fit_reason": "Engineering background can translate into reliable test automation.",
            "salary_range_usd": "80k-120k",
            "missing_skills": ["testing framework depth", "test data strategy"],
            "next_step": "Automate API and UI tests for one public demo app.",
            "confidence": "low",
        },
        {
            "title": "Technical Support Engineer",
            "fit_reason": "Technical troubleshooting skills are valuable for customer-facing systems.",
            "salary_range_usd": "70k-105k",
            "missing_skills": ["incident communication", "ticket triage metrics"],
            "next_step": "Practice writing concise issue triage reports for common failure scenarios.",
            "confidence": "low",
        },
    ]

    for item in defaults:
        if len(recommendations) >= 5:
            break
        recommendations.append(item)

    return {"jobs": recommendations[:5]}


def cover_letter_generator(context: str):
    prompt = f"""
You are an expert career writer.

Task:
Write a professional short cover letter based on the candidate context.

STRICT REQUIREMENTS:
- Keep it concise (170-230 words).
- Use this structure exactly:
  1) Greeting: "Dear Hiring Manager,"
  2) Strong opening interest sentence
  3) 1 short paragraph on relevant skills/impact
  4) 1 short paragraph connecting to target roles/opportunities
  5) 1 short paragraph with clear next-step intent
  6) Closing + "Sincerely," + "[Your Name]"
- Tone must be confident, polite, and practical.
- Do not use markdown.

Candidate + role context:
{context}
"""
    llm_output = call_llm(prompt).strip()
    if _looks_like_cover_letter(llm_output):
        return llm_output

    return _fallback_cover_letter(context)


def _looks_like_cover_letter(text: str):
    lower = text.lower()
    return "dear hiring manager" in lower and "sincerely" in lower and len(text) > 280


def _extract_job_titles_from_context(context: str):
    parsed = _extract_json_object(context)
    if not parsed:
        return []

    jobs = parsed.get("jobs")
    if not isinstance(jobs, list):
        return []

    titles = []
    for job in jobs:
        if isinstance(job, dict) and job.get("title"):
            titles.append(str(job["title"]))
    return titles


def _fallback_cover_letter(context: str):
    titles = _extract_job_titles_from_context(context)
    primary_role = titles[0] if len(titles) >= 1 else "Frontend Developer"
    secondary_role = titles[1] if len(titles) >= 2 else "Full Stack Developer"

    return (
        "Dear Hiring Manager,\n\n"
        "I am excited to apply for opportunities that align with my experience in building reliable, user-focused software products. "
        "I am especially interested in roles where I can contribute quickly while continuing to grow in a strong engineering environment.\n\n"
        "Across recent projects, I have worked on modern web and API development, improved performance, and collaborated closely with cross-functional teams "
        "to ship production-ready features. I focus on clean implementation, practical problem-solving, and measurable product impact.\n\n"
        f"I am particularly drawn to {primary_role} opportunities, and I am also interested in {secondary_role} roles where I can contribute to architecture, "
        "delivery quality, and team collaboration.\n\n"
        "I would welcome the chance to discuss how my skills can support your team’s goals. Thank you for your time and consideration.\n\n"
        "Sincerely,\n"
        "[Your Name]"
    )
