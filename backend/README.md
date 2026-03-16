# CustomsGateways Pipeline Backend

AI-powered customs data optimization pipeline. Phase 1: Data Ingestion, Enrichment & Classification.

## Quick Start

### 1. Start infrastructure
```bash
# From project root
docker-compose up -d postgres qdrant pgadmin
```

### 2. Configure environment
```bash
cd backend
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize database
```bash
python scripts/init_db.py
```

### 5. Start API server
```bash
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Docker (Full Stack)
```bash
# From project root
docker-compose up -d
```

## Pipeline API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pipeline/upload` | POST | Upload customer file |
| `/api/v1/pipeline/execute` | POST | Start pipeline |
| `/api/v1/pipeline/status/{run_id}` | GET | Get progress |
| `/api/v1/pipeline/download/{run_id}/{step_id}` | GET | Download results |
| `/api/v1/pipeline/upload/{run_id}/{step_id}` | POST | Upload corrections |
| `/api/v1/pipeline/analytics/{run_id}` | GET | Get analytics |

## Pipeline Steps (Phase 1)

- **P1**: AI-Powered File Extraction & Mapping
- **P2**: AI Description Enrichment
- **P3**: TARIC Classification
