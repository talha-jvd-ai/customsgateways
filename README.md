# CustomsGateways Data Optimization Pipeline

AI-powered customs data optimization pipeline that processes customer-uploaded trade data files through extraction, enrichment, and classification steps, producing standardized, enriched, and classified output.

## Architecture

```
┌──────────────────────────────────────────────┐
│  Next.js Frontend (Vercel / localhost:3000)   │
│  File upload → Pipeline toggles → Live status │
│  Step cards → Progressive analytics           │
└──────────────────┬───────────────────────────┘
                   │ REST API (polling every 2s)
┌──────────────────▼───────────────────────────┐
│  FastAPI Backend (Docker / localhost:8000)     │
│  ┌──────────────────────────────────────┐     │
│  │  Pipeline Orchestrator               │     │
│  │  Step 1 → Step 2 → Step 3           │     │
│  └──────────────────────────────────────┘     │
│  PostgreSQL 16 │ Qdrant Vector DB │ OpenAI    │
└──────────────────────────────────────────────┘
```

## Pipeline Steps (Phase 1)

| Step | Name | Type | Status |
|------|------|------|--------|
| P1 | Data Extraction & Harmonization | AI-powered | New build |
| P2 | AI Description Enrichment | AI-powered | Integrated from existing tool |
| P3 | Tariff Classification (TARIC) | AI + RAG | Integrated from existing tool |

### Step 1: AI-Powered File Extraction & Mapping
- Reads CSV, Excel files in any format, delimiter, encoding, or language
- Three-tier mapping: exact match (150+ aliases) → fuzzy match → AI match (single LLM call)
- Handles unstructured inputs: emails, invoices, OCR text, JSON, packing lists
- Validates and normalizes to 49-field standard format
- Auto-calculates weight/value fields

### Step 2: AI Description Enrichment
- Batch-optimized: 50 descriptions assessed per LLM call, 20 enhanced per call
- Selective: only enhances descriptions with quality score < 7
- ~10x faster than original single-item processing

### Step 3: TARIC Classification
- RAG-based classification using Qdrant vector database
- Skips duplicate enhancement (uses Step 2 output directly)
- Confidence distribution and review workload tracking

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Python 3.12+ (for local backend development)
- OpenAI API Key

### 1. Start Infrastructure
```bash
docker-compose up -d postgres qdrant pgadmin
```

### 2. Setup Backend
```bash
cd backend
cp .env.example .env
# Edit .env → add OPENAI_API_KEY

pip install -r requirements.txt
python scripts/init_db.py
uvicorn app.main:app --reload
```
Backend API: http://localhost:8000/docs

### 3. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend: http://localhost:3000

### 4. Full Docker Deployment
```bash
docker-compose up -d
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pipeline/upload` | POST | Upload customer file |
| `/api/v1/pipeline/execute` | POST | Start pipeline with selected steps |
| `/api/v1/pipeline/status/{run_id}` | GET | Get progressive status (polled) |
| `/api/v1/pipeline/download/{run_id}/{step_id}` | GET | Download step results |
| `/api/v1/pipeline/upload/{run_id}/{step_id}` | POST | Upload corrected data |
| `/api/v1/pipeline/analytics/{run_id}` | GET | Get progressive analytics |
| `/api/v1/health` | GET | Health check |
| `/api/v1/classify/single` | POST | Standalone classification |
| `/api/v1/classify/batch` | POST | Standalone batch classification |
| `/api/v1/feedback` | POST | Submit classification feedback |

## Project Structure

```
customs-pipeline/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application
│   │   ├── config.py                  # Settings (env vars)
│   │   ├── models.py                  # All Pydantic models
│   │   ├── database.py                # PostgreSQL CRUD
│   │   ├── api/
│   │   │   ├── pipeline_routes.py     # Pipeline endpoints
│   │   │   └── classification_routes.py # Standalone classifier
│   │   ├── pipeline/
│   │   │   └── orchestrator.py        # Step sequencing & progress
│   │   └── services/
│   │       ├── extraction.py          # Step 1: File reading & mapping
│   │       ├── enhancement.py         # Step 2: Batch enrichment
│   │       ├── classification.py      # Step 3: RAG classification
│   │       ├── embedding.py           # OpenAI embeddings
│   │       ├── qdrant_service.py      # Vector DB operations
│   │       └── field_definitions.py   # 49 fields, aliases, rules
│   ├── scripts/init_db.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── services/api.js            # Backend API client
│   │   ├── context/PipelineContext.jsx # Global state + polling
│   │   ├── app/
│   │   │   ├── layout.jsx             # Root layout with Provider
│   │   │   ├── dashboard/page.jsx     # Main dashboard (live data)
│   │   │   └── login/page.jsx         # Login page
│   │   ├── components/
│   │   │   ├── navbar/                # Pipeline toggles
│   │   │   ├── fileUpload/            # File upload + execute
│   │   │   ├── processingCard/        # Step cards
│   │   │   ├── cardDetails/           # Dynamic component renderer
│   │   │   ├── cardDetailComponents/  # 22 UI components
│   │   │   ├── mainCards/             # KPI cards
│   │   │   ├── mainCharts/            # Before/after charts
│   │   │   ├── financialImpactChart/  # Waterfall chart
│   │   │   └── nextActionsTable/      # Action items table
│   │   └── data/processingStepsData.js # Fallback static data
│   ├── package.json
│   └── next.config.mjs
├── docker-compose.yml
└── README.md
```

## Frontend Integration Details

The backend API response `details` array uses the exact same component type structure as the frontend's `CardDetails` renderer. This means the frontend renders backend data without any component changes. The mapping:

| API `type` field | Frontend Component |
|------------------|--------------------|
| `progress` | ProgressBar |
| `stepStatus` | StepStatus |
| `kpi` | KPICircle |
| `info` | InfoBox |
| `buttons` | ActionButtons |
| `aiSuggestion` | AISuggestion |
| `confidenceBars` | ConfidenceBars |
| `donutChartGrid` | DonutChartGrid |
| `statsGrid` | StatsGrid |
| `segmentedBar` | SegmentedBar |

## Data Flow

```
Customer File (CSV/Excel/Text)
    │
    ▼
Step 1: Extract & Map → 49-field standardized dataset
    │
    ▼
Step 2: Enrich Description column → enhanced descriptions
    │
    ▼
Step 3: Classify using enriched description → TARIC codes
    │
    ▼
Output: Complete file with all fields + TARIC codes + confidence
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.12+) |
| Frontend | Next.js 16, React 19 |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant |
| AI/LLM | OpenAI GPT-4o, text-embedding-3-small |
| Containerization | Docker & Docker Compose |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://hsuser:hspassword@localhost:5432/hsdb` |
| `QDRANT_HOST` | Qdrant host | `localhost` |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend | `http://localhost:8000/api/v1` |

## Future Phases

### Phase 2: Calculations & Routing
- P4: Customs value calculation (FX, uplift, coverage)
- P5: Receiver logic validation (normalization, consistency)
- P6: Hub comparison (BRU / AMS / LGG gateway optimization)
- P7: Duties & taxes simulation (per-hub fiscal comparison + KM distance)

### Phase 3: Compliance & Optimization
- P8: eCommerce eligibility (allow/review/deny)
- P9: Integrity & recovery (gap detection, optimization delta)
- Full deployment to STRATO DPS
- Advanced analytics (waterfall charts, financial impact)
- Authentication system

## Known Limitations (Phase 1)

- PDF/Word file support deferred (no customer examples available yet)
- Authentication is placeholder (localStorage-based)
- Financial impact chart shows placeholder data until Phase 2 steps are active
- Deployment configuration for STRATO DPS not included

## License

Proprietary — All rights reserved.
