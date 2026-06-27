Agentic Research Framework

An async multi-agent research orchestrator that autonomously searches the web, scrapes content (including YouTube transcripts), and consolidates findings into a structured executive report — all driven by a pipeline of specialized AI agents with a human-in-the-loop editing step.


The Problem It Solves

Deep research takes time: opening tabs, filtering ads, reading long articles, and synthesizing information across sources. This framework delegates the entire process to a coordinated agent pipeline. You provide a query, review and refine the search plan, and receive a formatted Markdown report with real citations.


Architecture

The workflow is divided into three specialized agents operating asynchronously:

User Query
    │
    ▼
┌─────────────────────────────────────┐
│           Planner Agent             │  Breaks query into focused sub-topics
│  (LLaMA 3.3 70B via Groq)          │  Returns structured research plan
└──────────────┬──────────────────────┘
               │
               ▼  ← Human-in-the-Loop pause
        ┌─────────────┐
        │ Editor UI   │  User refines, reorders, adds or removes topics
        │ (browser)   │  before any web search begins
        └──────┬──────┘
               │  POST /api/research/{job_id}/approve
               ▼
┌─────────────────────────────────────┐
│          Researcher Agent           │  Searches DuckDuckGo per sub-topic
│  (async, per sub-topic)            │  Scrapes page content (BeautifulSoup)
│                                    │  Fetches YouTube transcripts when relevant
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│           Writer Agent              │  Synthesizes all findings
│  (LLaMA 3.3 70B via Groq)          │  Produces structured Markdown report
└──────────────┬──────────────────────┘
               │
               ▼
       Executive Report
       (Markdown + sources)

Job state, real-time terminal logs, and report content are all persisted in a local SQLite database, enabling the polling endpoint to stream live progress to the browser UI.


Key Engineering Decisions

1. Multi-Agent Pipeline with Phase Isolation

Each agent has a single, bounded responsibility. The Planner never searches; the Researcher never writes prose. This isolation keeps LLM context windows lean, reduces hallucination surface, and makes each phase independently debuggable. Agents communicate through job state stored in SQLite, not in-memory shared state — which means the pipeline is restartable.

2. Human-in-the-Loop (Interactive Editor)

The pipeline deliberately pauses after planning. An interactive browser UI opens, showing the generated sub-topics as editable nodes. The user can rename, reorder, delete, or add topics before approving. Only after POST /api/research/{job_id}/approve do the web searches begin. This prevents wasted API calls on a plan the user would have changed anyway.

3. Hot-Reload of .env Configuration

The .env file is re-read on every new API call — not only at server startup. This means you can rotate or correct your GROQ_API_KEY mid-session without restarting the backend. Useful during development and when working with API key quotas across multiple accounts.

4. Async Researcher Parallelism

Each approved sub-topic spawns an independent async research task. DuckDuckGo searches, HTTP scraping (BeautifulSoup), and YouTube transcript fetching run concurrently via asyncio, not sequentially. For a 5-topic research plan, this reduces total wall-clock time proportionally to the slowest single topic rather than the sum of all.

5. SQLite for Live Log Streaming

Instead of holding logs in memory or using a message broker, each agent appends log entries to a logs table in SQLite as it runs. The polling endpoint (GET /api/research/{job_id}) reads from this table and streams entries to the browser UI in real time. This keeps the stack dependency-free (no Redis, no Kafka) while still delivering live progress.


Stack

LayerTechnologyAPI & orchestrationFastAPI (Python)LLM inferenceGroq — LLaMA 3.3 70BWeb searchDuckDuckGo Search APIContent scrapingBeautifulSoup4Video transcriptsyoutube-transcript-apiJob state & logsSQLiteFrontendVanilla JS (served by FastAPI)


API Endpoints

MethodRouteDescriptionPOST/api/researchRuns the Planner agent, returns job_id and initial topic planPOST/api/research/{job_id}/approveAccepts the (optionally edited) topic list, triggers async Researcher + WriterGET/api/research/{job_id}Returns real-time logs, current status, and final report when complete

Example Flow

Step 1 — Submit a query:

bashcurl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Evolution of Slack'\''s business model over the last five years"}'

json{
  "job_id": "c22fa968-3469-4100-85e7-4656ab9d9774",
  "status": "PENDING",
  "topics": [
    "Slack's pivot from freemium to enterprise",
    "Salesforce acquisition impact on pricing",
    "Slack Connect and B2B network effects",
    "Slack vs Microsoft Teams market share 2020–2024"
  ]
}

Step 2 — Approve (after editing in the UI):

bashcurl -X POST http://localhost:8000/api/research/c22fa968.../approve \
  -H "Content-Type: application/json" \
  -d '{"topics": ["Slack pivot to enterprise", "Salesforce acquisition", "Slack vs Teams"]}'

Step 3 — Poll for results:

bashcurl http://localhost:8000/api/research/c22fa968...

json{
  "status": "COMPLETED",
  "logs": ["[Researcher] Searching: Slack pivot to enterprise", "..."],
  "report": "# Slack Business Model Evolution\n\n## Executive Summary\n..."
}


How to Run

Prerequisites: Python 3.10+, a Groq API key (free tier available).

bash# 1. Clone and install
git clone https://github.com/leonardo-albrecht/agentic-research-framework
cd agentic-research-framework
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 3. Start
python -m uvicorn app.main:app --port 8000

Open http://localhost:8000 in your browser.


The .env file hot-reloads on every request — no restart needed when rotating API keys.




Screenshots


Note: Add screenshots to docs/screenshots/ and uncomment the lines below.



<!--
![Planning Editor](docs/screenshots/01_editor.png)
*Human-in-the-loop topic editor — refine the research plan before searches begin*

![Live Logs](docs/screenshots/02_logs.png)
*Real-time terminal log stream — each agent appends progress as it runs*

![Final Report](docs/screenshots/03_report.png)
*Executive Markdown report with consolidated findings and sources*
-->

Roadmap


 Vector database integration for querying past research sessions
 PDF export of final report
 Automatic translation of non-English YouTube transcripts
 Docker Compose packaging for one-command setup
