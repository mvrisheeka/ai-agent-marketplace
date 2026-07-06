const BASE_URL = "http://127.0.0.1:8000";
let authToken = "";
let agents = [];
let lastOutputText = "Ready.";
let lastFinalCoverText = "";
const SAMPLE_INPUTS = {
  frontend: "I am a Frontend developer with 3+ years of experience building scalable and high-performance web applications. Skilled in React, TypeScript, JavaScript (ES6+), HTML5, CSS3, Redux Toolkit, and REST APIs. Developed 2 production dashboards used by 10k+ daily users, improved page load speed by 35% using code splitting and lazy loading, and reduced unnecessary re-renders by 25%. Built analytics dashboards with charts and real-time updates. Experienced in responsive UI design, cross-browser compatibility, Git workflows, Agile development, and performance debugging using Chrome DevTools.",

  backend: "I am aBackend engineer with strong experience in building scalable APIs and distributed systems. Skilled in Python, FastAPI, Django, PostgreSQL, Docker, AWS, and REST API design. Designed and maintained APIs serving 50k+ monthly active users, reduced API latency by 40% through query optimization and caching, and implemented JWT-based authentication systems. Improved test coverage using Pytest and integration testing. Built microservices-based backend systems and deployed using Docker and AWS EC2. Familiar with database indexing, CI/CD pipelines, and monitoring tools.",

  fresher: "I am a BTech Computer Science graduate with hands-on project experience in full-stack development. Skilled in Java, Spring Boot, MySQL, React, JavaScript, HTML, and CSS. Built an e-commerce application with cart and checkout functionality, a real-time chat app using WebSocket, and a resume screening tool using basic NLP techniques. Participated in coding contests and developed multiple academic projects. Strong foundation in data structures and problem solving. Familiar with Git and collaborative development. Seeking entry-level software engineer roles.",

  fullstack: "I am a Full stack software engineer with 3 years of experience building end-to-end applications. Skilled in React, TypeScript, Node.js, Express, FastAPI, PostgreSQL, Docker, AWS, and Git. Reduced page load time by 35% through frontend optimization, built and deployed APIs serving 50k+ users, and increased test coverage from 40% to 78%. Designed RESTful services, handled database schema design, and implemented authentication systems. Built SaaS platforms with dashboards and analytics. Experienced in CI/CD pipelines, cloud deployments, and system design basics. Targeting product-based companies.",

  leadership: "I am a Senior frontend engineer with 6+ years of experience leading UI architecture and engineering teams. Skilled in React, TypeScript, Next.js, GraphQL, Storybook, CI/CD, and cloud deployment. Led development of enterprise dashboards used by 100k+ users, mentored 4 junior developers, and improved application performance by 40%. Built reusable design systems using Storybook and optimized frontend architecture for scalability. Collaborated with product managers and backend teams for feature planning. Strong experience in Agile leadership, sprint planning, and code reviews. Seeking senior roles with leadership and system design responsibilities."
};
function fillSampleInput(key) {
  const input = document.getElementById("userInput");
  input.value = SAMPLE_INPUTS[key] || "";
  input.focus();
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function prettyJsonToHtml(obj) {
  const rows = Object.entries(obj).map(([key, value]) => {
    if (Array.isArray(value)) {
      const items = value.map((item) => `<li>${escapeHtml(String(item))}</li>`).join("");
      return `<div class="json-row"><h4>${escapeHtml(key)}</h4><ul>${items}</ul></div>`;
    }
    if (value && typeof value === "object") {
      return `<div class="json-row"><h4>${escapeHtml(key)}</h4><pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre></div>`;
    }
    return `<div class="json-row"><h4>${escapeHtml(key)}</h4><p>${escapeHtml(String(value))}</p></div>`;
  });
  return rows.join("");
}

function parseJsonLoose(text) {
  if (!text || typeof text !== "string") {
    return null;
  }

  const cleaned = text.replace("```json", "").replace("```", "").trim();
  try {
    return JSON.parse(cleaned);
  } catch {
    const start = cleaned.indexOf("{");
    const end = cleaned.lastIndexOf("}");
    if (start === -1 || end === -1 || end <= start) {
      return null;
    }
    try {
      return JSON.parse(cleaned.slice(start, end + 1));
    } catch {
      return null;
    }
  }
}

function extractValue(text, key) {
  const parsed = parseJsonLoose(text);
  if (!parsed || typeof parsed !== "object") {
    return "N/A";
  }
  const value = parsed[key];
  if (value === undefined || value === null || value === "") {
    return "N/A";
  }
  return String(value);
}

function extractArray(text, key) {
  const parsed = parseJsonLoose(text);
  if (!parsed || !Array.isArray(parsed[key])) {
    return "N/A";
  }
  const values = parsed[key].map((item) => String(item)).filter(Boolean);
  return values.length ? values.join(", ") : "N/A";
}

function extractJobs(text) {
  const parsed = parseJsonLoose(text);
  if (!parsed || !Array.isArray(parsed.jobs)) {
    return [];
  }
  return parsed.jobs;
}

function renderStructuredOutput(stepResults, finalOutput) {
  const output = document.getElementById("output");
  const rawOutput = document.getElementById("rawOutput");
  const rawPayload = { steps: stepResults, final_output: finalOutput };

  output.classList.remove("output-error");
  lastOutputText = JSON.stringify(rawPayload, null, 2);
  rawOutput.innerText = lastOutputText;

  const sections = [];

  const resumeStep = stepResults.find((step) => step.agent === "resume");
  if (resumeStep) {
    sections.push(`
      <section class="result-section">
        <h4>Resume Analysis</h4>
        <article class="result-card">
          <p><strong>Score:</strong> ${escapeHtml(extractValue(resumeStep.output, "score"))}</p>
          <p><strong>Skills:</strong> ${escapeHtml(extractArray(resumeStep.output, "skills"))}</p>
          <p><strong>Feedback:</strong> ${escapeHtml(extractValue(resumeStep.output, "feedback"))}</p>
        </article>
      </section>
    `);
  }

  const jobStep = stepResults.find((step) => step.agent === "job");
  if (jobStep) {
    const jobs = extractJobs(jobStep.output);
    const jobCards = jobs.length
      ? jobs.map((job) => `
          <article class="result-card">
            <h5>${escapeHtml(String(job.title || "Recommended Role"))}</h5>
            <p><strong>Why:</strong> ${escapeHtml(String(job.fit_reason || "N/A"))}</p>
            <p><strong>Salary:</strong> ${escapeHtml(String(job.salary_range_usd || "N/A"))}</p>
            <p><strong>Missing Skills:</strong> ${escapeHtml(Array.isArray(job.missing_skills) ? job.missing_skills.join(", ") : "N/A")}</p>
            <p><strong>Next Step:</strong> ${escapeHtml(String(job.next_step || "N/A"))}</p>
            <p><strong>Confidence:</strong> ${escapeHtml(String(job.confidence || "N/A"))}</p>
          </article>
        `).join("")
      : `
        <article class="result-card">
          <p>${escapeHtml(jobStep.output || "No job output.")}</p>
        </article>
      `;

    sections.push(`
      <section class="result-section">
        <h4>Job Recommendations</h4>
        <div class="job-grid">${jobCards}</div>
      </section>
    `);
  }

  const coverStep = stepResults.find((step) => step.agent === "cover");
  if (coverStep) {
    sections.push(`
      <section class="result-section">
        <h4>Cover Letter</h4>
        <article class="result-card">
          <p>${escapeHtml(coverStep.output || "No cover letter output.").replaceAll("\n", "<br>")}</p>
        </article>
      </section>
    `);
  }

  // Fallback for non-resume/job/cover flows.
  if (!sections.length) {
    const generic = stepResults.map((step, index) => `
      <section class="result-section">
        <h4>Step ${index + 1}: ${escapeHtml(getAgentName(step.agent))}</h4>
        <article class="result-card">
          <p>${escapeHtml(step.output || "No output").replaceAll("\n", "<br>")}</p>
        </article>
      </section>
    `).join("");
    output.innerHTML = generic || "<p>Ready.</p>";
    return;
  }

  output.innerHTML = sections.join("");
}

function setOutput(content, isError = false) {
  const output = document.getElementById("output");
  const rawOutput = document.getElementById("rawOutput");
  const normalized = typeof content === "string" ? content : JSON.stringify(content, null, 2);
  lastOutputText = normalized;

  output.classList.toggle("output-error", isError);
  rawOutput.innerText = normalized;

  let parsed;
  try {
    parsed = JSON.parse(normalized);
  } catch {
    parsed = null;
  }

  if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
    output.innerHTML = prettyJsonToHtml(parsed);
    return;
  }

  const paragraphs = normalized
    .split(/\n{2,}/)
    .map((block) => `<p>${escapeHtml(block).replaceAll("\n", "<br>")}</p>`)
    .join("");
  output.innerHTML = paragraphs || "<p>Ready.</p>";
}

function toggleRawView() {
  const toggle = document.getElementById("rawViewToggle");
  const output = document.getElementById("output");
  const rawOutput = document.getElementById("rawOutput");
  const showRaw = toggle.checked;

  output.classList.toggle("hidden", showRaw);
  rawOutput.classList.toggle("hidden", !showRaw);
}

async function copyOutput() {
  const copyBtn = document.getElementById("copyOutputBtn");
  try {
    await navigator.clipboard.writeText(lastOutputText);
    copyBtn.innerText = "Copied";
    setTimeout(() => {
      copyBtn.innerText = "Copy Response";
    }, 1200);
  } catch (error) {
    copyBtn.innerText = "Copy failed";
    setTimeout(() => {
      copyBtn.innerText = "Copy Response";
    }, 1200);
  }
}

function setFinalCoverOutput(text, showButton) {
  const finalBtn = document.getElementById("copyFinalBtn");
  lastFinalCoverText = showButton ? text : "";
  finalBtn.classList.toggle("hidden", !showButton);
}

async function copyFinalOutput() {
  const copyBtn = document.getElementById("copyFinalBtn");
  if (!lastFinalCoverText) {
    copyBtn.innerText = "No cover output";
    setTimeout(() => {
      copyBtn.innerText = "Copy Final Cover Letter";
    }, 1200);
    return;
  }

  try {
    await navigator.clipboard.writeText(lastFinalCoverText);
    copyBtn.innerText = "Copied";
    setTimeout(() => {
      copyBtn.innerText = "Copy Final Cover Letter";
    }, 1200);
  } catch (error) {
    copyBtn.innerText = "Copy failed";
    setTimeout(() => {
      copyBtn.innerText = "Copy Final Cover Letter";
    }, 1200);
  }
}

function setLoading(isLoading, message = "Processing...") {
  const loadingBar = document.getElementById("loadingBar");
  const loadingText = document.getElementById("loadingText");
  const buttons = document.querySelectorAll("button");

  loadingText.innerText = message;
  loadingBar.classList.toggle("hidden", !isLoading);
  buttons.forEach((button) => {
    button.disabled = isLoading;
  });
}

function getAuthHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${authToken}`
  };
}

function getAgentName(agentId) {
  const found = agents.find((agent) => agent.id === agentId);
  return found ? found.name : agentId;
}

function renderStepTracker(agentIds) {
  const tracker = document.getElementById("stepTracker");
  tracker.innerHTML = "";

  agentIds.forEach((agentId, index) => {
    const step = document.createElement("article");
    step.className = "step-card";
    step.id = `step-${index}`;
    step.innerHTML = `
      <div class="step-title">
        <strong>Step ${index + 1}: ${getAgentName(agentId)}</strong>
        <span id="step-status-${index}" class="step-status status-queued">Queued</span>
      </div>
      <div id="step-body-${index}" class="step-body">Waiting for execution...</div>
    `;
    tracker.appendChild(step);
  });
}

function updateStep(index, status, body) {
  const statusEl = document.getElementById(`step-status-${index}`);
  const bodyEl = document.getElementById(`step-body-${index}`);

  if (!statusEl || !bodyEl) {
    return;
  }

  statusEl.className = `step-status status-${status}`;
  statusEl.innerText = status.charAt(0).toUpperCase() + status.slice(1);
  bodyEl.innerText = body;
}

function renderAgents() {
  const grid = document.getElementById("agentsGrid");
  grid.innerHTML = "";

  agents.forEach((agent) => {
    const skills = Array.isArray(agent.skills) ? agent.skills : [];
    const capabilities = Array.isArray(agent.capabilities) ? agent.capabilities : [];
    const skillsHtml = skills.map((skill) => `<span class="skill-chip">${escapeHtml(String(skill))}</span>`).join("");
    const capHtml = capabilities.map((cap) => `<li>${escapeHtml(String(cap))}</li>`).join("");

    const card = document.createElement("article");
    card.className = "agent-card";
    card.innerHTML = `
      <div>
        <h3>${agent.name}</h3>
        <p>${agent.description}</p>
        <div class="agent-meta">
          <p class="meta-title">Skills</p>
          <div class="skills-row">${skillsHtml || "<span class='skill-chip'>N/A</span>"}</div>
          <p class="meta-title">Capabilities</p>
          <ul class="capability-list">${capHtml || "<li>N/A</li>"}</ul>
        </div>
      </div>
      <div class="card-actions">
        <label>
          <input type="checkbox" class="agent-checkbox" value="${agent.id}" />
          Select for A2A
        </label>
        <a href="${agent.how_to_use_url}" target="_blank" rel="noopener noreferrer">How to use</a>
        <button data-agent-id="${agent.id}">Run This Agent</button>
      </div>
    `;

    const button = card.querySelector("button");
    button.addEventListener("click", () => useAgent(agent.id));
    grid.appendChild(card);
  });
}

async function login() {
  const username = document.getElementById("username").value.trim();
  if (!username) {
    document.getElementById("authStatus").innerText = "Username is required";
    return;
  }

  setLoading(true, "Logging in...");
  try {
    const res = await fetch(`${BASE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username })
    });

    if (!res.ok) {
      document.getElementById("authStatus").innerText = "Login failed";
      return;
    }

    const data = await res.json();
    authToken = data.token;

    setLoading(true, "Loading marketplace agents...");
    const agentsRes = await fetch(`${BASE_URL}/agents`);
    agents = await agentsRes.json();

    document.getElementById("authStatus").innerText = `Logged in as ${username}`;
    document.getElementById("app").classList.remove("hidden");
    renderAgents();
  } catch (error) {
    document.getElementById("authStatus").innerText = "Login error. Check backend.";
  } finally {
    setLoading(false);
  }
}

async function useAgent(agentId) {
  const input = document.getElementById("userInput").value;
  renderStepTracker([agentId]);
  updateStep(0, "running", "Sending request to backend...");
  setLoading(true, `Running ${agentId} agent...`);
  try {
    const res = await fetch(`${BASE_URL}/run-agent`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        agent: agentId,
        input: input
      })
    });

    const data = await res.json();
    if (!res.ok) {
      updateStep(0, "error", data.detail || "Request failed");
      setOutput(data.detail || "Request failed", true);
      setFinalCoverOutput("", false);
      return;
    }

    updateStep(0, "done", data.output || "No output");
    setOutput(data.output || "No output");
    setFinalCoverOutput(data.output || "No output", agentId === "cover");
  } catch (error) {
    updateStep(0, "error", "Request error. Check backend.");
    setOutput("Request error. Check backend.", true);
    setFinalCoverOutput("", false);
  } finally {
    setLoading(false);
  }
}

async function runA2A() {
  const selected = Array.from(document.querySelectorAll(".agent-checkbox:checked"))
    .map((el) => el.value);

  if (selected.length < 2) {
    setOutput("Select at least two agents for A2A.", true);
    setFinalCoverOutput("", false);
    return;
  }

  const input = document.getElementById("userInput").value.trim();
  if (!input) {
    setOutput("Input is required.", true);
    setFinalCoverOutput("", false);
    return;
  }

  renderStepTracker(selected);
  setLoading(true, "Running A2A pipeline...");
  try {
    let currentInput = input;
    const stepResults = [];

    for (let i = 0; i < selected.length; i += 1) {
      const agentId = selected[i];
      updateStep(i, "running", "Processing...");
      setLoading(true, `Running step ${i + 1}/${selected.length}: ${getAgentName(agentId)}`);

      const res = await fetch(`${BASE_URL}/run-agent`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          agent: agentId,
          input: currentInput
        })
      });

      const data = await res.json();
      if (!res.ok) {
        const errorText = data.detail || "A2A step failed";
        updateStep(i, "error", errorText);
        setOutput(errorText, true);
        setFinalCoverOutput("", false);
        return;
      }

      const stepOutput = data.output || "No output";
      updateStep(i, "done", stepOutput);
      stepResults.push({ step: i + 1, agent: agentId, output: stepOutput });
      currentInput = stepOutput;
    }

    renderStructuredOutput(stepResults, currentInput);
    setFinalCoverOutput(currentInput, selected[selected.length - 1] === "cover");
  } catch (error) {
    setOutput("A2A request error. Check backend.", true);
    setFinalCoverOutput("", false);
  } finally {
    setLoading(false);
  }
}
