# IT Helpdesk Deflection Agent

A production-ready RAG-grounded IT support agent that answers employee IT questions from a knowledge base, escalates to human engineers when confidence is low, and provides full security guardrails + observability.

---

## Architecture

```
Employee Chat UI
      │
      ▼
FastAPI Backend
  ├── Input Guard      ← Rate limit, injection (15 patterns), OOD, PII
  ├── Azure AI Search  ← Hybrid KB retrieval
  ├── Confidence Gate  ← Answer or escalate
  ├── GPT-4o-mini      ← Hardened RAG generation
  └── Output Guard     ← PII scan, XSS strip
      │
      ├── Prometheus + Grafana  (metrics)
      └── Escalation Store      (JSON → CosmosDB in prod)
```

---

## Quick Start (Local, Mock Mode)

No Azure credentials needed — runs entirely locally.

### Prerequisites
- Python 3.12+
- Docker Desktop (optional, for full stack)

### Option A: Python directly

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Create .env from template
Copy-Item .env.example .env
# Edit .env → set MOCK_MODE=true (already default)

# Run
uvicorn app.main:app --reload --port 8000
```

Open `frontend/index.html` in your browser.

### Option B: Docker Compose (full stack with Grafana)

```powershell
docker compose up --build
```

| Service    | URL                            |
|------------|-------------------------------|
| Chat UI    | http://localhost:3000          |
| API Docs   | http://localhost:8000/docs     |
| Prometheus | http://localhost:9090          |
| Grafana    | http://localhost:3001          |

Grafana default credentials: `admin` / `helpdesk-admin`

---

## Running Tests

```powershell
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Test coverage targets

| Module | Tests |
|--------|-------|
| Input Guard | 15 injection patterns, 10 clean queries, rate limit, OOD, size |
| Output Guard | 5 high-risk PII types, phone redaction, XSS strip, HTML escape |
| Confidence Gate | score bounds, coverage, disclaimer thresholds |
| Escalation Service | category/urgency classification, ticket CRUD |
| Chat endpoint | schema, injection rejection, escalation flow |
| Metrics | all counters increment, Prometheus registry output |

---

## Ingesting the Knowledge Base

```powershell
cd backend
# Dry run (local only, no Azure):
python scripts/ingest_kb.py --kb-path ../kb --dry-run

# Production (requires Azure AI Search credentials in .env):
python scripts/ingest_kb.py --kb-path ../kb
```

---

## Security Guardrails

| Layer | Mechanism |
|-------|-----------|
| Rate Limiting | 20 req / 60s per session + 50 req / 60s per IP |
| Prompt Injection | 15 regex patterns (INJ_01 to INJ_15) |
| OOD Classification | keyword signals — non-IT topics rejected |
| Input Size | 2,000 character hard cap |
| System Prompt | Frozen Jinja2 template — user input never in system |
| User Input Delimiters | `<user_input>` tags prevent history injection |
| Output PII Scan | 8 entity types — high-risk blocks, moderate redacts |
| XSS Stripping | Script/iframe/JS protocol removed from output |
| Audit Log | Append-only JSONL with hashed IP addresses |
| Security Headers | CSP, X-Frame-Options, X-Content-Type-Options |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_MODE` | `true` | Use local KB search instead of Azure |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `AZURE_OPENAI_ENDPOINT` | — | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | — | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o-mini` | Deployment name |
| `AZURE_SEARCH_ENDPOINT` | — | Azure AI Search endpoint |
| `AZURE_SEARCH_API_KEY` | — | Azure AI Search key |
| `CONFIDENCE_THRESHOLD` | `0.70` | Below → escalate |
| `LOW_CONFIDENCE_THRESHOLD` | `0.85` | Below → add disclaimer |
| `RATE_LIMIT_PER_SESSION` | `20` | Requests per 60s per session |

See `.env.example` for the full list.

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app factory
│   │   ├── config.py             # Pydantic settings
│   │   ├── models.py             # Data schemas
│   │   ├── routers/              # chat, escalation, health
│   │   ├── services/             # retrieval, generation, confidence, escalation
│   │   ├── security/             # input_guard, output_guard, rate_limiter, audit_log
│   │   ├── monitoring/           # metrics, middleware, health_checks, log_schema
│   │   └── utils/                # logging, chunker
│   ├── scripts/
│   │   └── ingest_kb.py          # KB ingestion with poison detection
│   ├── tests/                    # Full test suite
│   ├── Dockerfile                # Multi-stage build
│   └── requirements.txt
├── frontend/
│   ├── index.html                # Employee chat UI
│   ├── admin.html                # IT team ticket queue
│   ├── monitor.html              # Live metrics dashboard
│   ├── css/style.css             # Design system
│   └── js/                      # chat.js, admin.js, monitor.js
├── kb/                           # 12+ markdown KB articles
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
├── .github/workflows/
│   ├── ci.yml                    # pytest + ruff + bandit
│   └── cd.yml                    # Docker → ACR → Azure Container Apps
├── docker-compose.yml
└── nginx.conf
```

---

## Deployment (Azure)

1. Create resources: Azure Container Registry, Container Apps, AI Search, OpenAI, Static Web Apps
2. Set GitHub Secrets: `AZURE_CREDENTIALS`, `AZURE_CONTAINER_REGISTRY`, `SWA_DEPLOY_TOKEN`
3. Push to `main` — CI runs tests, CD deploys automatically
4. Ingest KB: `python scripts/ingest_kb.py --kb-path kb/`
5. Configure Grafana dashboards pointing to your Container App metrics endpoint

---

## Key Metrics (Prometheus)

| Metric | Type | Description |
|--------|------|-------------|
| `helpdesk_requests_total` | Counter | All requests by outcome |
| `helpdesk_deflections_total` | Counter | Successful agent answers |
| `helpdesk_escalations_total` | Counter | Tickets raised (by category/urgency) |
| `helpdesk_deflection_rate` | Gauge | Rolling deflection % |
| `rag_confidence_score` | Histogram | Answer confidence distribution |
| `rag_retrieval_latency_seconds` | Histogram | Azure Search latency |
| `llm_request_latency_seconds` | Histogram | GPT-4o-mini latency |
| `llm_tokens_total` | Counter | Prompt + completion tokens |
| `security_blocked_requests_total` | Counter | Blocked by threat type |
| `security_injection_detections_total` | Counter | By pattern ID |
| `security_pii_detections_total` | Counter | By entity type |
| `service_health_status` | Gauge | Per dependency (1=healthy) |
