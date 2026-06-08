# 🧠 MeetingMind — AI Meeting Intelligence

> A production-grade multi-agent AI system that turns meeting transcripts into structured action items. Record in **English or Amharic**, transcribe with Groq Whisper, and process through 3 specialized AI agents.

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-orange?style=flat-square)](https://langchain-ai.github.io/langgraph)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=flat-square&logo=docker)](https://docker.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-purple?style=flat-square)](https://console.groq.com)

---

## 🎯 What It Does

```
🎙️ Record Audio (English or Amharic)
        ↓
🤖 Groq Whisper → Transcript
        ↓
Agent 1 → Summarize key points and decisions
        ↓
Agent 2 → Extract tasks, owners, deadlines
        ↓
Agent 3 → Generate structured follow-up report
        ↓
💾 Save to SQLite database
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              Next.js Frontend                    │
│         localhost:3000 / Vercel                  │
└──────────────────┬──────────────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────────────┐
│              FastAPI Backend                     │
│         localhost:8000 / GCP Cloud Run           │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Agent 0  │  │ Agent 1  │  │ Agent 2  │       │
│  │Whisper   │  │Summarizer│  │Extractor │       │
│  │Groq API  │  │Groq API  │  │Groq API  │       │
│  └──────────┘  └──────────┘  └──────────┘       │
│                                    ↓             │
│                             ┌──────────┐         │
│                             │ Agent 3  │         │
│                             │ Tracker  │         │
│                             │  Python  │         │
│                             └──────────┘         │
│                                    ↓             │
│                          ┌─────────────────┐     │
│                          │  SQLite Database │     │
│                          └─────────────────┘     │
└─────────────────────────────────────────────────┘
```

---

## 🤖 The Three Agents

| Agent | Name | Model | Role |
|-------|------|-------|------|
| 0 | Transcriber | Groq Whisper Large V3 | Converts audio to text (EN/AM) |
| 1 | Summarizer | Groq LLaMA 3.3 70B | Extracts key points and decisions |
| 2 | Extractor | Groq LLaMA 3.3 70B | Identifies tasks, owners, deadlines |
| 3 | Tracker | Pure Python | Builds structured follow-up report |

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — REST API with automatic Swagger docs
- **LangGraph** — Multi-agent orchestration as a directed graph
- **Groq** — Ultra-fast AI inference (LLaMA 3.3 70B + Whisper)
- **SQLite** — Lightweight persistent database
- **Docker** — Containerized deployment

### Frontend
- **Next.js 14** — React framework with App Router
- **Tailwind CSS** — Utility-first styling
- **Web Audio API** — Real-time waveform visualization
- **MediaRecorder API** — Browser-native audio recording

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Groq API key — free at [console.groq.com](https://console.groq.com)
- Node.js 18+ (for frontend)

### 1. Clone the repositories

```bash
# Backend
git clone https://github.com/Yonatan8475/gemini-multi-agent.git
cd gemini-multi-agent

# Frontend (separate repo)
git clone https://github.com/Yonatan8475/meetingmind.git
cd meetingmind
```

### 2. Configure environment

Create a `.env` file in the backend folder:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

Update `docker-compose.yml`:
```yaml
environment:
  - GROQ_API_KEY=${GROQ_API_KEY}
```

### 3. Run the backend

```bash
cd gemini-multi-agent
docker compose up --build
```

Backend live at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 4. Run the frontend

```bash
cd meetingmind
npm install
npm run dev
```

Frontend live at: `http://localhost:3000`

---

## 📡 API Endpoints

### Pipeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/process-meeting` | Run full 3-agent pipeline |
| `POST` | `/api/transcribe` | Transcribe audio (EN/AM) |
| `POST` | `/api/transcribe-and-process` | Transcribe + pipeline in one call |

### Meetings
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/meetings` | List all meetings |
| `GET` | `/api/meetings/{id}` | Get single meeting with tasks |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks` | List all tasks |
| `PATCH` | `/api/tasks/{id}/status` | Update task status |

### Agents (individual)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/summarize` | Run Agent 1 only |
| `POST` | `/api/extract` | Run Agent 2 only |

---

## 📁 Project Structure

```
gemini-multi-agent/
│
├── agents/
│   ├── groq_client.py      ← Groq API connection
│   ├── transcriber.py      ← Agent 0: Whisper transcription
│   ├── summarizer.py       ← Agent 1: Meeting summarizer
│   ├── extractor.py        ← Agent 2: Task extractor
│   └── tracker.py          ← Agent 3: Report generator
│
├── api/
│   └── routes.py           ← All FastAPI endpoints
│
├── database/
│   └── db.py               ← SQLite operations
│
├── main.py                 ← LangGraph pipeline definition
├── server.py               ← FastAPI app entry point
├── state.py                ← Shared state TypedDict
├── Dockerfile              ← Container definition
├── docker-compose.yml      ← Multi-container setup
└── requirements.txt        ← Python dependencies
```

---

## 🌍 Bilingual Support

MeetingMind supports both **English** and **Amharic (አማርኛ)** via Groq Whisper Large V3.

| Language | Code | Use Case |
|----------|------|----------|
| English | `en` | International meetings |
| Amharic | `am` | Ethiopian business meetings |
| Auto-detect | `auto` | Unknown language |

This makes MeetingMind uniquely suited for Ethiopian businesses like **TruckGo** where meetings happen in Amharic.

---

## 🧪 Testing the API

Using the Swagger UI at `http://localhost:8000/docs`:

**Test the full pipeline:**
```json
POST /api/process-meeting
{
  "transcript": "John will build the API backend by Friday. Sarah will clean the dataset by Wednesday."
}
```

**Expected response:**
```json
{
  "meeting_id": 1,
  "summary": "Key Points:\n- John assigned to API backend...",
  "tasks": [
    {"task": "Build API backend", "owner": "John", "deadline": "Friday"},
    {"task": "Clean dataset", "owner": "Sarah", "deadline": "Wednesday"}
  ],
  "report": "FOLLOW-UP REPORT\n1. Build API backend → John → Due: Friday → Status: Pending\n2. Clean dataset → Sarah → Due: Wednesday → Status: Pending"
}
```

---

## 🐳 Docker Commands

```bash
# Build and start
docker compose up --build

# Run in background
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up --build
```

---

## 🚢 Deployment

### Backend → GCP Cloud Run
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/gemini-multi-agent

# Deploy to Cloud Run
gcloud run deploy gemini-multi-agent \
  --image gcr.io/PROJECT_ID/gemini-multi-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_key
```

### Frontend → Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL
# Enter your GCP Cloud Run URL
```

---

## 💡 Key Design Decisions

**Why Groq instead of OpenAI?**
Groq runs LLaMA 3.3 70B on custom LPU hardware — 10x faster than OpenAI at zero cost on the free tier. No 429 rate limit issues.

**Why LangGraph instead of plain function calls?**
LangGraph gives checkpointing, streaming, error recovery, and easy extensibility. Adding a new agent is just adding a new node.

**Why SQLite instead of PostgreSQL?**
SQLite is zero-config, file-based, and perfect for single-instance deployments. Easy to switch to PostgreSQL later for scaling.

**Why Agent 3 has no AI call?**
Formatting a list into a report doesn't need intelligence. Pure Python is faster, cheaper, and more reliable for deterministic formatting tasks.

---

## 📊 Sample Output

**Input transcript:**
```
TruckGo Ethiopia sprint meeting.
Yonatan will deploy the backend to GCP by Friday.
Meron will integrate Chapa payment gateway by Tuesday.
Tigist will build the mobile app in two weeks.
```

**Agent 1 — Summary:**
```
Key Points:
- TruckGo Ethiopia sprint planning meeting
- Three major deliverables assigned

Decisions Made:
- Backend deployment target: GCP Cloud Run
- Payment integration: Chapa gateway
- Mobile app: React Native

Deadlines: Friday, Tuesday, Two weeks
```

**Agent 2 — Tasks:**
```json
[
  {"task": "Deploy backend to GCP", "owner": "Yonatan", "deadline": "Friday"},
  {"task": "Integrate Chapa payment gateway", "owner": "Meron", "deadline": "Tuesday"},
  {"task": "Build mobile app", "owner": "Tigist", "deadline": "Two weeks"}
]
```

**Agent 3 — Report:**
```
FOLLOW-UP REPORT

1. Deploy backend to GCP → Yonatan → Due: Friday → Status: Pending
2. Integrate Chapa payment gateway → Meron → Due: Tuesday → Status: Pending
3. Build mobile app → Tigist → Due: Two weeks → Status: Pending
```

---

## 👨‍💻 Built By

**Yonatan Abebe**
Applied AI Solutions Development — George Brown College, Toronto 2025

- 🔗 GitHub: [github.com/Yonatan8475](https://github.com/Yonatan8475)


---

## 📄 License

MIT License — free to use, modify, and distribute.
