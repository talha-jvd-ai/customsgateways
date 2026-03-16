# Technical Specification — Phase 1 Implementation
## CustomsGateways Data Optimization Pipeline
**Version:** 1.0 | **Date:** March 10, 2026

---

## 1. System Architecture

### 1.1 Overview

Single modular FastAPI application with pipeline orchestration. Each step is an internal Python module sharing the same database and vector store. The Next.js frontend (deployed on Vercel) communicates with the backend via REST APIs.

```
┌─────────────────────────────────────────────────────────┐
│  Next.js Frontend (Vercel)                              │
│  - File upload (FileUpload component)                   │
│  - Pipeline toggles (Navbar component)                  │
│  - Step cards (ProcessingCard → CardDetails renderer)   │
│  - Analytics (MainCards, MainCharts, FinancialImpact)   │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────────┐
│  FastAPI Backend (Docker)                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Pipeline Orchestrator                           │    │
│  │  - Manages run state, step sequencing, progress  │    │
│  │  - Calls step modules in order                   │    │
│  └───────┬─────────────┬─────────────┬─────────────┘    │
│    ┌─────▼───┐   ┌─────▼───┐   ┌─────▼───┐             │
│    │ Step 1  │   │ Step 2  │   │ Step 3  │             │
│    │Extract  │──▶│Enrich   │──▶│Classify │             │
│    │& Map    │   │(exists) │   │(exists) │             │
│    └─────────┘   └─────────┘   └─────────┘             │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │PostgreSQL│  │ Qdrant   │  │ OpenAI   │              │
│  │  16      │  │ Vector   │  │ GPT-4o   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Project Structure

```
customs-pipeline/
├── app/
│   ├── __init__.py
│   ├── main.py                         # FastAPI app, lifespan, CORS
│   ├── config.py                       # Pydantic settings (extends existing)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── pipeline.py                 # PipelineRun, StepResult, StepStatus
│   │   ├── extraction.py               # ExtractionRequest/Response, FieldMapping
│   │   ├── enrichment.py               # EnrichmentRequest/Response
│   │   ├── classification.py           # ClassificationRequest/Response (existing)
│   │   └── analytics.py                # KPI, BeforeAfter, NextAction models
│   ├── api/
│   │   ├── __init__.py
│   │   ├── pipeline_routes.py          # /upload, /execute, /status, /download
│   │   ├── step_routes.py              # /upload/{run_id}/{step}, per-step actions
│   │   ├── analytics_routes.py         # /analytics/{run_id}
│   │   └── classification_routes.py    # Existing standalone endpoints (kept)
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py             # Run manager, step sequencer, progress
│   │   └── state.py                    # Pipeline run state management
│   ├── services/
│   │   ├── __init__.py
│   │   ├── extraction.py               # Step 1: NEW
│   │   ├── enhancement.py              # Step 2: EXISTING (improved)
│   │   ├── classification.py           # Step 3: EXISTING (integrated)
│   │   ├── embedding.py                # EXISTING
│   │   ├── qdrant_service.py           # EXISTING
│   │   └── analytics.py                # Progressive KPI calculations
│   └── database/
│       ├── __init__.py
│       ├── connection.py               # Engine, session (from existing database.py)
│       ├── pipeline_db.py              # Pipeline run CRUD
│       └── classification_db.py        # Existing classification tables
├── scripts/
│   └── init_db.py                      # Extended for new tables
├── data/
│   └── field_mappings.json             # Known header → target field mappings
├── docker-compose.yml                  # Extended from existing
├── Dockerfile                          # Python app container
├── pyproject.toml
└── .env
```

---

## 2. Database Schema (New Tables)

### 2.1 pipeline_runs

```sql
CREATE TABLE pipeline_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename        VARCHAR(255) NOT NULL,
    original_name   VARCHAR(255),
    file_path       TEXT,
    total_rows      INTEGER DEFAULT 0,
    enabled_steps   JSONB NOT NULL DEFAULT '["P1","P2","P3"]',
    status          VARCHAR(20) DEFAULT 'pending',
        -- pending | processing | completed | failed | cancelled
    current_step    VARCHAR(10),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP
);
```

### 2.2 step_results

```sql
CREATE TABLE step_results (
    id              SERIAL PRIMARY KEY,
    run_id          UUID REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    step_id         VARCHAR(10) NOT NULL,      -- P1, P2, P3
    status          VARCHAR(20) DEFAULT 'pending',
        -- pending | processing | completed | failed | skipped
    progress        FLOAT DEFAULT 0,           -- 0-100
    sub_steps       JSONB,                     -- Step-specific status booleans
    kpis            JSONB,                     -- Step-specific KPI data
    result_path     TEXT,                      -- Path to output file
    error_message   TEXT,
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    UNIQUE(run_id, step_id)
);
```

### 2.3 field_mappings

```sql
CREATE TABLE field_mappings (
    id              SERIAL PRIMARY KEY,
    run_id          UUID REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    source_column   VARCHAR(255) NOT NULL,
    target_field    VARCHAR(255) NOT NULL,     -- One of 49 standard fields
    confidence      FLOAT DEFAULT 0,
    method          VARCHAR(50),               -- 'exact' | 'fuzzy' | 'ai'
    user_confirmed  BOOLEAN DEFAULT FALSE
);
```

### Existing tables remain unchanged:
- classifications, user_feedback, product_memory, batch_jobs, metrics

---

## 3. Backend API Specification

### 3.1 Pipeline Endpoints

#### POST /api/v1/pipeline/upload
Upload customer file for processing.

```
Request: multipart/form-data
  - file: File (CSV, XLSX, XLS)

Response 201:
{
    "run_id": "uuid",
    "filename": "original_name.csv",
    "total_rows": 1247,
    "detected_columns": ["TRACKING_NUMBER", "SHIPPER_NAME", ...],
    "status": "uploaded"
}
```

#### POST /api/v1/pipeline/execute
Trigger pipeline execution.

```
Request:
{
    "run_id": "uuid",
    "enabled_steps": ["P1", "P2", "P3"]  // from toggle state
}

Response 200:
{
    "run_id": "uuid",
    "status": "processing",
    "message": "Pipeline started with 3 steps enabled"
}
```

#### GET /api/v1/pipeline/status/{run_id}
Get progressive pipeline status. Frontend polls this endpoint.

```
Response 200:
{
    "run_id": "uuid",
    "status": "processing",
    "current_step": "P1",
    "steps": [
        {
            "step_id": "P1",
            "title": "Data Extraction & Harmonization",
            "status": "processing",
            "progress": 62,
            "details": [                     // Matches processingStepsData structure
                { "type": "progress", "label": "Progress", "percentage": 62 },
                { "type": "stepStatus", "title": "Step Status", "steps": [
                    { "name": "Extract Status", "value": true },
                    { "name": "Mapping Status", "value": true },
                    { "name": "Normalization Status", "value": false },
                    { "name": "Completeness Status", "value": false }
                ]},
                { "type": "kpi", "label": "Data Completeness KPI", "percentage": 74 },
                { "type": "info", "message": "Processing row 774 of 1,247" },
                { "type": "buttons", "buttons": [...] }
            ]
        },
        {
            "step_id": "P2",
            "title": "AI Enrichment",
            "status": "pending",
            "progress": 0,
            "details": []
        },
        ...
    ]
}
```

**Critical design decision:** The `details` array in each step response uses the EXACT same component type structure as `processingStepsData.js`. This means the frontend's `CardDetails` renderer works without modification — just replace static data with API data.

#### GET /api/v1/pipeline/download/{run_id}/{step_id}
Download step results as CSV/XLSX.

```
Response 200: File download (application/octet-stream)
Headers: Content-Disposition: attachment; filename="P1_result_uuid.csv"
```

#### POST /api/v1/pipeline/upload/{run_id}/{step_id}
Upload corrected data at any step.

```
Request: multipart/form-data
  - file: File (CSV, XLSX)

Response 200:
{
    "message": "Data uploaded for step P1",
    "rows_updated": 1247
}
```

### 3.2 Analytics Endpoint

#### GET /api/v1/pipeline/analytics/{run_id}
Progressive analytics — returns whatever data is available based on completed steps.

```
Response 200:
{
    "kpi_cards": [
        { "title": "Data Quality Change", "value": "94.2%", "trend": "18.7%", "direction": "up" },
        ...
    ],
    "before_after_charts": [
        {
            "title": "Data Quality - Before vs After",
            "categories": [
                { "name": "Product Info", "before": 68, "after": 94 },
                ...
            ]
        }
    ],
    "financial_impact": null,  // null until later phases
    "next_actions": [
        { "type": "Missing HS Code", "count": 142, "impact": "High", "fixability": "Easy" },
        ...
    ]
}
```

---

## 4. Step 1: AI-Powered Extraction & Mapping (NEW BUILD)

### 4.1 Architecture

```
Input File → File Reader → Column Detection → AI Mapping → Validation → Normalization → Output
```

### 4.2 File Reader Module

```python
# app/services/extraction.py

class FileReader:
    """Reads CSV/Excel files with auto-detection"""

    def read(self, file_path: str) -> pd.DataFrame:
        # 1. Detect file type from extension
        # 2. For CSV: auto-detect delimiter (comma, semicolon, tab, pipe)
        #    - Try multiple encodings: utf-8, iso-8859-1, cp1252
        #    - Skip separator declarations (e.g., "sep=;")
        # 3. For Excel: read all sheets, use the one with most columns
        # 4. Return DataFrame with original headers preserved
```

**Supported formats:**
- CSV: comma, semicolon, tab, pipe delimited
- Encodings: UTF-8, ISO-8859-1, CP1252 (auto-detected)
- Excel: .xlsx, .xls (single and multi-sheet)

### 4.3 AI Field Mapper

Three-tier mapping strategy (fast to slow):

**Tier 1 — Exact Match (instant)**
```python
KNOWN_MAPPINGS = {
    # Exact header → target field
    "Reference1": "Reference1",
    "Consignment Number": "Reference1",
    "TRACKING_NUMBER": "Reference1",
    "Delivery": "Reference1",
    "Shipper Name": "Shipper Name",
    "SHIPPER_NAME": "Shipper Name",
    "Shippers Name": "Shipper Name",
    "Sender Company": "Shipper Name",
    # ... comprehensive list built from all sample files
}
```

**Tier 2 — Fuzzy Match (fast)**
```python
# Normalize both source and target: lowercase, remove underscores/spaces/special chars
# Compare using token similarity
# Example: "Ship_Add_1" → "shipperadd1" ≈ "shipperaddress1" → "Shipper Address 1"
# Threshold: 85% similarity
```

**Tier 3 — AI Match (1 LLM call per file, not per column)**
```python
# Send unmapped columns + sample data to GPT-4o in a single prompt:

MAPPING_PROMPT = """
You are a customs data mapping expert. Map these source columns to the target fields.

Source columns (with 3 sample values each):
{source_columns_with_samples}

Target fields:
{list_of_49_target_fields}

Return JSON: {"source_column": "target_field", ...}
Only map columns you're confident about. Use null for uncertain mappings.
"""
```

**Output:** List of `FieldMapping` objects with confidence scores and method used.

### 4.4 Data Validation & Normalization

After mapping, apply these rules from the import template Notes sheet:

```python
class DataValidator:
    def validate_and_normalize(self, df: pd.DataFrame) -> ValidationResult:
        # 1. Data type checks
        #    - Country codes: 2-char ISO 3166-1 alpha-2
        #    - Currency: 3-char ISO 4217
        #    - Weight UOM: "KGS" or "LBS"
        #    - Incoterms: "DDP" etc.
        #    - TARIC code: 10 digits (validated later in Step 3)

        # 2. Mandatory field checks (bold fields in template)

        # 3. Max length enforcement (per Notes sheet)

        # 4. Weight/Value auto-calculation:
        #    Item Quantity * Item Weight = Line Weight
        #    Item Quantity * Item Value = Line Value
        #    Sum(Line Weight) = Total Weight
        #    Sum(Line Value) = Total Value

        # 5. Completeness KPI calculation:
        #    completeness = filled_mandatory_fields / total_mandatory_fields * 100
```

### 4.5 Sub-step Progress Tracking

Step 1 reports these sub-steps to match the frontend P1 card:

| Sub-step | Maps to frontend | When True |
|----------|-----------------|-----------|
| Extract Status | `stepStatus[0]` | File successfully parsed |
| Mapping Status | `stepStatus[1]` | All columns mapped (or confirmed) |
| Normalization Status | `stepStatus[2]` | Data types/formats validated |
| Completeness Status | `stepStatus[3]` | All mandatory fields populated |

---

## 5. Step 2: AI Description Enrichment (INTEGRATE + IMPROVE)

### 5.1 What Exists

Current `enhancement.py` has two functions:
- `assess_description_quality()` — 1 GPT-4o call, returns quality score 1-10
- `enhance_description()` — 1 GPT-4o call, returns enhanced description

**Problem:** 2 LLM calls per item = slow for batch processing (1000+ rows).

### 5.2 Optimization Strategy

**Batch assessment:** Instead of 1 call per item, send batches of 20-50 descriptions in a single prompt.

```python
BATCH_ASSESS_PROMPT = """
Assess these product descriptions for customs classification quality (1-10).
Return JSON array with quality_score and needs_enhancement (boolean).

Descriptions:
{batch_of_descriptions}
"""
```

**Selective enhancement:** Only enhance descriptions with quality < 7 (skip good ones).

**Batch enhancement:** Send low-quality descriptions in batches of 10-20.

**Expected improvement:** From ~2-3 items/sec to ~20-30 items/sec.

### 5.3 Integration

```python
# app/services/enhancement.py (modified)

class EnrichmentService:
    def process_batch(self, descriptions: List[dict], run_id: str) -> List[dict]:
        # 1. Batch assess all descriptions (batches of 50)
        # 2. Filter: only enhance where quality < 7
        # 3. Batch enhance filtered descriptions (batches of 20)
        # 4. Update progress after each batch
        # 5. Return enhanced descriptions with quality scores
```

### 5.4 Frontend Card Data (P2)

Step 2 returns data matching the P2 card in `processingStepsData.js`:

```json
{
    "type": "aiSuggestion",
    "title": "AI Suggestion",
    "description": "Enhanced 847 of 1,247 descriptions. Average quality improved from 4.2 to 7.8."
},
{
    "type": "confidenceBars",
    "bars": [
        { "value": "94%", "percentage": 94, "color": "#50CD89" },
        { "value": "Low", "percentage": 30, "color": "#DB0101" }
    ]
}
```

---

## 6. Step 3: TARIC Classification (INTEGRATE)

### 6.1 What Exists

Current `classification.py` pipeline:
1. `process_description()` → assess + enhance
2. `generate_embedding()` → text-embedding-3-small
3. `search_both_collections()` → Qdrant (corrections + training)
4. `rank_predictions()` → confidence scoring
5. Return top prediction or top-3 for user selection

### 6.2 Integration Changes

**Skip Step 2 internally:** Since Step 2 already enriched descriptions, Step 3 should use the enriched description directly without calling `process_description()` again.

```python
# app/services/classification.py (modified for pipeline)

class ClassificationService:
    def classify_batch(self, items: List[dict], run_id: str) -> List[dict]:
        for item in items:
            # Use already-enriched description from Step 2
            enhanced_desc = item["enhanced_description"]
            country = item["country_of_origin"]

            # Generate embedding
            embedding = generate_embedding(
                prepare_text_for_embedding(enhanced_desc, country)
            )

            # Search Qdrant
            results = search_both_collections(embedding, country)

            # Rank predictions
            predictions = rank_predictions(results["corrections"] + results["training"])

            # Store result
            item["taric_code"] = predictions[0].hs_code if predictions else None
            item["confidence_8"] = predictions[0].confidence_8_digit
            item["confidence_10"] = predictions[0].confidence_10_digit
            item["requires_review"] = predictions[0].confidence_8_digit < 80

            # Update progress
            update_step_progress(run_id, "P3", processed / total * 100)
```

### 6.3 Frontend Card Data (P3)

Matches the P3 card structure — items analyzed, confidence distribution (donut charts), review workload:

```json
{
    "type": "statDisplay",
    "label": "Items Analyzed",
    "value": "1,247"
},
{
    "type": "donutChartGrid",
    "charts": [
        {
            "title": "Confidence Distribution",
            "segments": [
                { "label": "High", "value": 72, "color": "#50CD89" },
                { "label": "Medium", "value": 18, "color": "#FE9A00" },
                { "label": "Low", "value": 10, "color": "#DB0101" }
            ]
        }
    ]
}
```

---

## 7. Pipeline Orchestrator

### 7.1 Core Logic

```python
# app/pipeline/orchestrator.py

class PipelineOrchestrator:
    STEP_SEQUENCE = ["P1", "P2", "P3"]
    STEP_SERVICES = {
        "P1": ExtractionService,
        "P2": EnrichmentService,
        "P3": ClassificationService,
    }

    async def execute(self, run_id: str, enabled_steps: List[str]):
        """Execute pipeline steps sequentially"""
        run = get_pipeline_run(run_id)
        current_data = None

        for step_id in self.STEP_SEQUENCE:
            if step_id not in enabled_steps:
                mark_step_skipped(run_id, step_id)
                continue

            mark_step_processing(run_id, step_id)

            try:
                service = self.STEP_SERVICES[step_id]()

                if step_id == "P1":
                    current_data = service.process(run.file_path)
                elif step_id == "P2":
                    current_data = service.process_batch(
                        current_data["descriptions"], run_id
                    )
                elif step_id == "P3":
                    current_data = service.classify_batch(
                        current_data["items"], run_id
                    )

                # Save intermediate result
                save_step_result(run_id, step_id, current_data)
                mark_step_completed(run_id, step_id)

            except Exception as e:
                mark_step_failed(run_id, step_id, str(e))
                break

        mark_pipeline_completed(run_id)
```

### 7.2 Background Execution

Pipeline runs as a FastAPI `BackgroundTask` (same pattern as existing batch processing):

```python
@router.post("/pipeline/execute")
async def execute_pipeline(request: ExecuteRequest, background_tasks: BackgroundTasks):
    orchestrator = PipelineOrchestrator()
    background_tasks.add_task(orchestrator.execute, request.run_id, request.enabled_steps)
    return {"run_id": request.run_id, "status": "processing"}
```

---

## 8. Frontend Integration Plan

### 8.1 New Files to Create

```
src/
├── services/
│   └── api.js                    # Centralized API client
├── context/
│   └── PipelineContext.jsx        # React context for pipeline state
```

### 8.2 API Service Layer

```javascript
// src/services/api.js
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const pipelineAPI = {
    upload: (file) => {
        const formData = new FormData();
        formData.append("file", file);
        return fetch(`${API_BASE}/pipeline/upload`, { method: "POST", body: formData });
    },
    execute: (runId, enabledSteps) =>
        fetch(`${API_BASE}/pipeline/execute`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ run_id: runId, enabled_steps: enabledSteps }),
        }),
    getStatus: (runId) => fetch(`${API_BASE}/pipeline/status/${runId}`),
    download: (runId, stepId) => fetch(`${API_BASE}/pipeline/download/${runId}/${stepId}`),
    uploadStepData: (runId, stepId, file) => { /* multipart upload */ },
    getAnalytics: (runId) => fetch(`${API_BASE}/pipeline/analytics/${runId}`),
};
```

### 8.3 Pipeline Context (State Management)

```javascript
// src/context/PipelineContext.jsx
"use client";
import { createContext, useContext, useState, useCallback, useRef } from "react";
import { pipelineAPI } from "@/services/api";

const PipelineContext = createContext();

export function PipelineProvider({ children }) {
    const [runId, setRunId] = useState(null);
    const [pipelineStatus, setPipelineStatus] = useState(null);
    const [analytics, setAnalytics] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const pollingRef = useRef(null);

    const uploadFile = async (file) => { /* call API, set runId */ };
    const startPipeline = async (enabledSteps) => { /* call API, start polling */ };
    const stopPolling = () => clearInterval(pollingRef.current);

    // Poll status every 2 seconds while processing
    const pollStatus = useCallback(async () => {
        if (!runId) return;
        const res = await pipelineAPI.getStatus(runId);
        const data = await res.json();
        setPipelineStatus(data);
        if (data.status === "completed" || data.status === "failed") {
            stopPolling();
            setIsProcessing(false);
            // Fetch final analytics
            const analyticsRes = await pipelineAPI.getAnalytics(runId);
            setAnalytics(await analyticsRes.json());
        }
    }, [runId]);

    return (
        <PipelineContext.Provider value={{
            runId, pipelineStatus, analytics, isProcessing,
            uploadFile, startPipeline, stopPolling
        }}>
            {children}
        </PipelineContext.Provider>
    );
}

export const usePipeline = () => useContext(PipelineContext);
```

### 8.4 Component Modifications

#### dashboard/page.jsx
- Wrap with `PipelineProvider`
- Replace `processingStepsData` import with `usePipeline().pipelineStatus.steps`
- Pass live analytics data to MainCards, MainCharts, etc.

#### navbar/page.jsx
- Fix step names to match backend (P4→Customs Value, P7→Duties & Taxes, etc.)
- Lift toggle state to PipelineContext so /execute can read enabled steps
- No other changes needed

#### fileUpload/page.jsx
- Connect `handleStartProcess` to `usePipeline().uploadFile()` then `startPipeline()`
- Add upload progress indicator
- Add loading/disabled state during processing
- Change button text to "Stop process" while running

#### processingCard/page.jsx + cardDetails/page.jsx
- No structural changes needed
- CardDetails already renders any `details` array dynamically
- Just pass API response data instead of static data

#### Analytics components (mainCards, mainCharts, financialImpactChart, nextActionsTable)
- Accept props instead of hardcoded data
- Receive data from `usePipeline().analytics`
- Show "Awaiting data..." placeholder when analytics is null

---

## 9. Docker Configuration

### 9.1 docker-compose.yml (Extended)

```yaml
services:
  pipeline-api:
    build: .
    container_name: cg-pipeline
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://hsuser:hspassword@postgres:5432/hsdb
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_started
    volumes:
      - upload_data:/app/uploads
      - result_data:/app/results

  postgres:
    image: postgres:16
    container_name: cg-postgres
    environment:
      POSTGRES_USER: hsuser
      POSTGRES_PASSWORD: hspassword
      POSTGRES_DB: hsdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hsuser -d hsdb"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    container_name: cg-qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  qdrant_data:
  upload_data:
  result_data:
```

---

## 10. Implementation Order

### Week 1: Backend Foundation + Step 1

| Day | Task |
|-----|------|
| 1 | Project scaffolding: FastAPI app, Docker setup, database schema, config |
| 2 | Pipeline orchestrator: run management, status tracking, background execution |
| 3 | Step 1 — File reader (CSV/Excel auto-detect, encoding handling) |
| 4 | Step 1 — AI field mapper (3-tier: exact → fuzzy → LLM) |
| 5 | Step 1 — Validation, normalization, weight/value calculations |
| 6 | API endpoints: upload, execute, status, download |
| 7 | Testing with all sample files (APC + 6 CSV samples) |

### Week 2: Steps 2-3 Integration + Frontend

| Day | Task |
|-----|------|
| 1 | Step 2 — Integrate enhancement.py, batch optimization |
| 2 | Step 3 — Integrate classification.py, skip duplicate enhancement |
| 3 | Progressive analytics endpoint, KPI calculations |
| 4 | Frontend: API service layer, PipelineContext, file upload wiring |
| 5 | Frontend: Pipeline status polling, step cards live data, analytics |
| 6 | End-to-end testing: upload → P1 → P2 → P3 → download |
| 7 | Bug fixes, edge cases, documentation |

---

## 11. Key Technical Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Execution model | BackgroundTasks | Simple, no external queue needed, matches existing pattern |
| Progress polling | REST polling (2s) | Simpler than WebSocket, sufficient for pipeline updates |
| AI mapping | Single LLM call per file | Cost-efficient vs. per-column calls |
| Batch enrichment | Batches of 20-50 | Balance between speed and token limits |
| Frontend state | React Context | Lightweight, no Redux overhead for this scope |
| API response format | Match processingStepsData structure | Zero frontend renderer changes needed |

---

## 12. Dependencies

### Backend (new additions to existing)
```
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pandas
openpyxl          # Excel reading
chardet           # Encoding detection
python-multipart  # File uploads
openai
qdrant-client
pydantic-settings
tenacity
```

### Frontend (no new dependencies)
Existing: next@16.1.6, react@19.2.3, recharts@3.7.0
