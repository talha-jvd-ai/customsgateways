"""Pipeline API routes — upload, execute, status, download, analytics."""

import os
import uuid
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.config import get_settings
from app.database import (
    get_db, create_pipeline_run, get_pipeline_run, update_pipeline_enabled_steps,
    get_step_results, get_step_result
)
from app.pipeline.orchestrator import PipelineOrchestrator, build_step_details, STEP_SEQUENCE
from app.services.field_definitions import STEP_DEFINITIONS
from app.models import (
    UploadResponse, ExecuteRequest, ExecuteResponse,
    PipelineStatusResponse, StepResponse, AnalyticsResponse,
    KPICard, NextAction
)

settings = get_settings()
router = APIRouter()


@router.post("/pipeline/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a customer file for processing."""
    # Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.supported_file_types:
        raise HTTPException(400, f"Unsupported file type: {ext}. Supported: {settings.supported_file_types}")

    # Save file
    os.makedirs(settings.upload_dir, exist_ok=True)
    run_id = str(uuid.uuid4())
    safe_name = f"{run_id}{ext}"
    file_path = os.path.join(settings.upload_dir, safe_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Quick read to get row count and columns
    try:
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path, nrows=0)
        else:
            df = pd.read_csv(file_path, nrows=0, on_bad_lines="skip")
        columns = list(df.columns)
        # Count rows (fast)
        if ext in (".xlsx", ".xls"):
            df_full = pd.read_excel(file_path)
        else:
            df_full = pd.read_csv(file_path, on_bad_lines="skip")
        total_rows = len(df_full)
    except Exception:
        columns = []
        total_rows = 0

    # Store in database
    with get_db() as db:
        create_pipeline_run(db, run_id, safe_name, file.filename, file_path, total_rows)

    return UploadResponse(
        run_id=run_id,
        filename=file.filename,
        total_rows=total_rows,
        detected_columns=columns[:50],  # Cap at 50 columns
        status="uploaded"
    )


@router.post("/pipeline/execute", response_model=ExecuteResponse)
async def execute_pipeline(request: ExecuteRequest, background_tasks: BackgroundTasks):
    """Trigger pipeline execution."""
    with get_db() as db:
        run = get_pipeline_run(db, request.run_id)
        if not run:
            raise HTTPException(404, "Pipeline run not found")
        if run["status"] == "processing":
            raise HTTPException(409, "Pipeline is already running")

        update_pipeline_enabled_steps(db, request.run_id, request.enabled_steps)

    orchestrator = PipelineOrchestrator()
    background_tasks.add_task(orchestrator.execute, request.run_id, request.enabled_steps)

    return ExecuteResponse(
        run_id=request.run_id,
        status="processing",
        message=f"Pipeline started with {len(request.enabled_steps)} steps enabled"
    )


@router.get("/pipeline/status/{run_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(run_id: str):
    """Get progressive pipeline status. Frontend polls this endpoint."""
    with get_db() as db:
        run = get_pipeline_run(db, run_id)
        if not run:
            raise HTTPException(404, "Pipeline run not found")

        step_results = get_step_results(db, run_id)
        step_lookup = {s["step_id"]: s for s in step_results}

        steps = []
        enabled = run.get("enabled_steps", STEP_SEQUENCE)

        for step_id in STEP_SEQUENCE:
            definition = STEP_DEFINITIONS.get(step_id, {"title": step_id, "description": ""})
            step_data = step_lookup.get(step_id, {"status": "pending", "progress": 0, "sub_steps": {}, "kpis": {}})

            if step_id not in enabled:
                step_data["status"] = "skipped"

            details = build_step_details(step_id, step_data)

            steps.append(StepResponse(
                step_id=step_id,
                title=definition["title"],
                description=definition["description"],
                status=step_data["status"],
                progress=step_data.get("progress", 0),
                details=details
            ))

        return PipelineStatusResponse(
            run_id=run_id,
            status=run["status"],
            current_step=run.get("current_step"),
            steps=steps
        )


@router.get("/pipeline/download/{run_id}/{step_id}")
async def download_step_result(run_id: str, step_id: str):
    """Download step results as CSV."""
    with get_db() as db:
        step = get_step_result(db, run_id, step_id)
        if not step:
            raise HTTPException(404, "Step result not found")
        if not step.get("result_path"):
            raise HTTPException(404, "No results available for this step")

        path = step["result_path"]
        if not os.path.exists(path):
            raise HTTPException(404, "Result file not found")

        return FileResponse(
            path=path,
            media_type="text/csv",
            filename=f"{step_id}_result_{run_id[:8]}.csv"
        )


@router.post("/pipeline/upload/{run_id}/{step_id}")
async def upload_step_data(run_id: str, step_id: str, file: UploadFile = File(...)):
    """Upload corrected data at any step."""
    with get_db() as db:
        run = get_pipeline_run(db, run_id)
        if not run:
            raise HTTPException(404, "Pipeline run not found")

    # Save uploaded correction
    os.makedirs(settings.results_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    path = os.path.join(settings.results_dir, f"{run_id}_{step_id}_result{ext}")

    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    # Update step result path
    with get_db() as db:
        from app.database import update_step_status
        update_step_status(db, run_id, step_id, "completed", result_path=path)

    try:
        df = pd.read_csv(path) if ext == ".csv" else pd.read_excel(path)
        rows = len(df)
    except Exception:
        rows = 0

    return {"message": f"Data uploaded for step {step_id}", "rows_updated": rows}


@router.get("/pipeline/analytics/{run_id}", response_model=AnalyticsResponse)
async def get_analytics(run_id: str):
    """Progressive analytics — returns data based on completed steps."""
    with get_db() as db:
        run = get_pipeline_run(db, run_id)
        if not run:
            raise HTTPException(404, "Pipeline run not found")

        step_results = get_step_results(db, run_id)
        step_lookup = {s["step_id"]: s for s in step_results}

    kpi_cards = []
    next_actions = []
    before_after_charts = []

    # Build KPIs from completed steps
    p1 = step_lookup.get("P1", {})
    p2 = step_lookup.get("P2", {})
    p3 = step_lookup.get("P3", {})

    if p1.get("status") == "completed":
        completeness = p1.get("kpis", {}).get("completeness", 0)
        kpi_cards.append(KPICard(
            title="Data Quality Change", value=f"{completeness}%",
            trend="", trend_direction="up"
        ))

    if p3.get("status") == "completed":
        kpis = p3.get("kpis", {})
        high_pct = kpis.get("high_confidence_pct", 0)
        review = kpis.get("review_needed", 0)
        kpi_cards.append(KPICard(
            title="Classification Confidence", value=f"{high_pct}%",
            trend="", trend_direction="up"
        ))
        kpi_cards.append(KPICard(
            title="Manual Review Required", value=str(review),
            trend="", trend_direction="down"
        ))

    # Build before/after from P1 completeness
    if p1.get("status") == "completed":
        before_after_charts.append({
            "title": "Data Quality - Before vs After",
            "categories": [
                {"name": "Completeness", "before": 45, "after": p1.get("kpis", {}).get("completeness", 0)},
                {"name": "Mapped Fields", "before": 30, "after": min(p1.get("kpis", {}).get("mapped_fields", 0) / 49 * 100, 100)},
            ]
        })

    # Build next actions from validation errors and review items
    if p1.get("status") == "completed":
        errors = p1.get("kpis", {}).get("validation_errors", 0)
        if errors > 0:
            next_actions.append(NextAction(
                type="Validation Errors", count=errors,
                impact="Medium", fixability="Easy", icon="warning",
                impact_color="#FEF3C7", impact_text="#D97706", fixability_color="#50CD89"
            ))

    if p3.get("status") == "completed":
        review = p3.get("kpis", {}).get("review_needed", 0)
        if review > 0:
            next_actions.append(NextAction(
                type="Classification Review Needed", count=review,
                impact="High", fixability="Medium", icon="warning",
                impact_color="#FEE2E2", impact_text="#DC2626", fixability_color="#FE9A00"
            ))

    return AnalyticsResponse(
        kpi_cards=kpi_cards,
        before_after_charts=before_after_charts,
        next_actions=next_actions
    )
