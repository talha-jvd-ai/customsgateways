"""Standalone classification routes — preserved from existing project."""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
import pandas as pd
import io
from sqlalchemy import text

from app.models import (
    ClassificationRequest, ClassificationResponse, FeedbackRequest, FeedbackResponse,
    BatchJobResponse, BatchStatusResponse, HealthResponse, HSCodePrediction
)
from app.services.classification import classify_item, validate_hs_code
from app.services.embedding import generate_embedding, prepare_text_for_embedding, test_openai_connection
from app.services.qdrant_service import insert_correction, test_connection as test_qdrant
from app.database import (
    get_db, store_classification, store_feedback, check_product_memory,
    save_to_product_memory, create_batch_job, update_batch_progress,
    complete_batch_job, get_batch_status, test_connection as test_postgres
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        qdrant_connected=test_qdrant(),
        postgres_connected=test_postgres(),
        openai_configured=test_openai_connection()
    )


@router.post("/classify/single", response_model=ClassificationResponse)
async def classify_single_item(request: ClassificationRequest):
    try:
        with get_db() as db:
            cached = check_product_memory(db, request.description, request.country)
            if cached:
                return ClassificationResponse(
                    classification_id=0, requires_selection=False,
                    predicted_hs_code=cached["hs_code"],
                    confidence_8_digit=cached["confidence"],
                    confidence_10_digit=cached["confidence"],
                    enhanced_description=request.description,
                    enhancement_quality=10, processing_time_ms=5
                )

        result = classify_item(request.description, request.country)
        if not result["success"]:
            raise HTTPException(500, result["error"])

        with get_db() as db:
            classification_id = store_classification(
                db=db, input_description=request.description,
                enhanced_description=result["enhanced_description"],
                enhancement_quality=result["enhancement_quality"],
                country=request.country,
                predicted_hs_code=result["top_prediction"].hs_code,
                confidence_8=result["top_prediction"].confidence_8_digit,
                confidence_10=result["top_prediction"].confidence_10_digit,
                processing_time_ms=result["processing_time_ms"],
                requires_selection=result["requires_selection"]
            )

        if result["requires_selection"]:
            return ClassificationResponse(
                classification_id=classification_id, requires_selection=True,
                options=result["predictions"],
                enhanced_description=result["enhanced_description"],
                enhancement_quality=result["enhancement_quality"],
                processing_time_ms=result["processing_time_ms"]
            )
        else:
            return ClassificationResponse(
                classification_id=classification_id, requires_selection=False,
                predicted_hs_code=result["top_prediction"].hs_code,
                confidence_8_digit=result["top_prediction"].confidence_8_digit,
                confidence_10_digit=result["top_prediction"].confidence_10_digit,
                enhanced_description=result["enhanced_description"],
                enhancement_quality=result["enhancement_quality"],
                processing_time_ms=result["processing_time_ms"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Classification failed: {str(e)}")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    try:
        if not validate_hs_code(request.selected_hs_code):
            raise HTTPException(400, "Invalid HS code format")

        with get_db() as db:
            result = db.execute(text(
                "SELECT input_description, enhanced_description, country FROM classifications WHERE id = :id"
            ), {"id": request.classification_id})
            row = result.fetchone()
            if not row:
                raise HTTPException(404, "Classification not found")

            input_desc, enhanced_desc, country = row
            store_feedback(db, request.classification_id, [], request.selected_hs_code)
            save_to_product_memory(db, input_desc, country, request.selected_hs_code, 95.0)

            text_for_embed = prepare_text_for_embedding(enhanced_desc, country)
            embedding = generate_embedding(text_for_embed)
            insert_correction(enhanced_desc, request.selected_hs_code, country, embedding, 95.0)

        return FeedbackResponse(status="success", message="Feedback recorded and system updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Feedback failed: {str(e)}")


async def process_batch_async(batch_id: str, df: pd.DataFrame):
    results = []
    with get_db() as db:
        for idx, row in df.iterrows():
            try:
                description = str(row.get("Item Description", ""))
                country = str(row.get("Item Country Of Origin", "CN"))[:2]
                result = classify_item(description, country)
                if result["success"]:
                    results.append({
                        "row": idx, "description": description, "country": country,
                        "predicted_hs_code": result["top_prediction"].hs_code,
                        "confidence_8_digit": result["top_prediction"].confidence_8_digit,
                        "requires_selection": result["requires_selection"]
                    })
                else:
                    results.append({"row": idx, "description": description, "error": result.get("error")})
                update_batch_progress(db, batch_id, idx + 1)
            except Exception as e:
                results.append({"row": idx, "error": str(e)})
        complete_batch_job(db, batch_id, results)


@router.post("/classify/batch", response_model=BatchJobResponse)
async def classify_batch(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(400, "File must be CSV or Excel")

        if "Item Description" not in df.columns:
            raise HTTPException(400, "Missing 'Item Description' column")

        with get_db() as db:
            batch_id = create_batch_job(db, file.filename, len(df))
        background_tasks.add_task(process_batch_async, batch_id, df)

        return BatchJobResponse(batch_id=batch_id, status="processing",
                                 total_items=len(df), message=f"Processing {len(df)} items.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Batch upload failed: {str(e)}")


@router.get("/status/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_job_status(batch_id: str):
    with get_db() as db:
        status = get_batch_status(db, batch_id)
        if not status:
            raise HTTPException(404, "Batch job not found")
        progress = (status["processed_items"] / status["total_items"] * 100) if status["total_items"] > 0 else 0
        return BatchStatusResponse(
            batch_id=status["batch_id"], status=status["status"],
            total_items=status["total_items"], processed_items=status["processed_items"],
            progress_percent=round(progress, 2), results=status["results"],
            created_at=status["created_at"], completed_at=status["completed_at"]
        )
