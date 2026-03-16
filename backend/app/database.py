from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import uuid

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize all database tables"""
    with engine.connect() as conn:
        # ── Pipeline tables ──────────────────────────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id VARCHAR(36) PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                original_name VARCHAR(255),
                file_path TEXT,
                total_rows INTEGER DEFAULT 0,
                enabled_steps JSONB NOT NULL DEFAULT '["P1","P2","P3"]',
                status VARCHAR(20) DEFAULT 'pending',
                current_step VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS step_results (
                id SERIAL PRIMARY KEY,
                run_id VARCHAR(36) REFERENCES pipeline_runs(id) ON DELETE CASCADE,
                step_id VARCHAR(10) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                progress FLOAT DEFAULT 0,
                sub_steps JSONB,
                kpis JSONB,
                result_path TEXT,
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                UNIQUE(run_id, step_id)
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS field_mappings (
                id SERIAL PRIMARY KEY,
                run_id VARCHAR(36) REFERENCES pipeline_runs(id) ON DELETE CASCADE,
                source_column VARCHAR(255) NOT NULL,
                target_field VARCHAR(255) NOT NULL,
                confidence FLOAT DEFAULT 0,
                method VARCHAR(50),
                user_confirmed BOOLEAN DEFAULT FALSE
            )
        """))

        # ── Existing classification tables ───────────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS classifications (
                id SERIAL PRIMARY KEY,
                input_description TEXT NOT NULL,
                enhanced_description TEXT,
                enhancement_quality INTEGER,
                country VARCHAR(2),
                predicted_hs_code VARCHAR(10),
                confidence_8_digit FLOAT,
                confidence_10_digit FLOAT,
                user_selected_code VARCHAR(10),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                feedback_timestamp TIMESTAMP,
                processing_time_ms INTEGER,
                requires_selection BOOLEAN DEFAULT FALSE
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                id SERIAL PRIMARY KEY,
                classification_id INTEGER REFERENCES classifications(id),
                shown_options JSONB,
                selected_code VARCHAR(10),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS batch_jobs (
                id VARCHAR(36) PRIMARY KEY,
                filename VARCHAR(255),
                total_items INTEGER,
                processed_items INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'processing',
                results JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product_memory (
                description_hash VARCHAR(64) PRIMARY KEY,
                original_description TEXT,
                country VARCHAR(2),
                confirmed_hs_code VARCHAR(10),
                confidence FLOAT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.commit()
        print("✅ All database tables initialized")


@contextmanager
def get_db():
    """Get database session context manager"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Pipeline CRUD ────────────────────────────────────────────────────────────

def create_pipeline_run(
    db: Session, run_id: str, filename: str, original_name: str,
    file_path: str, total_rows: int
) -> str:
    db.execute(text("""
        INSERT INTO pipeline_runs (id, filename, original_name, file_path, total_rows, status)
        VALUES (:id, :filename, :original, :path, :rows, 'pending')
    """), {
        "id": run_id, "filename": filename, "original": original_name,
        "path": file_path, "rows": total_rows
    })
    db.commit()
    return run_id


def get_pipeline_run(db: Session, run_id: str) -> Optional[Dict]:
    result = db.execute(text("""
        SELECT id, filename, original_name, file_path, total_rows,
               enabled_steps, status, current_step, created_at, completed_at
        FROM pipeline_runs WHERE id = :id
    """), {"id": run_id})
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0], "filename": row[1], "original_name": row[2],
        "file_path": row[3], "total_rows": row[4],
        "enabled_steps": row[5] if isinstance(row[5], list) else json.loads(row[5]) if row[5] else [],
        "status": row[6], "current_step": row[7],
        "created_at": row[8], "completed_at": row[9]
    }


def update_pipeline_status(db: Session, run_id: str, status: str, current_step: str = None):
    params = {"id": run_id, "status": status}
    if current_step is not None:
        db.execute(text("""
            UPDATE pipeline_runs SET status = :status, current_step = :step WHERE id = :id
        """), {**params, "step": current_step})
    else:
        db.execute(text("""
            UPDATE pipeline_runs SET status = :status WHERE id = :id
        """), params)
    db.commit()


def update_pipeline_enabled_steps(db: Session, run_id: str, enabled_steps: List[str]):
    db.execute(text("""
        UPDATE pipeline_runs SET enabled_steps = :steps WHERE id = :id
    """), {"id": run_id, "steps": json.dumps(enabled_steps)})
    db.commit()


def complete_pipeline(db: Session, run_id: str, status: str = "completed"):
    db.execute(text("""
        UPDATE pipeline_runs SET status = :status, completed_at = CURRENT_TIMESTAMP WHERE id = :id
    """), {"id": run_id, "status": status})
    db.commit()


# ── Step Results CRUD ────────────────────────────────────────────────────────

def create_step_result(db: Session, run_id: str, step_id: str):
    db.execute(text("""
        INSERT INTO step_results (run_id, step_id, status) VALUES (:run_id, :step_id, 'pending')
        ON CONFLICT (run_id, step_id) DO UPDATE SET status = 'pending', progress = 0
    """), {"run_id": run_id, "step_id": step_id})
    db.commit()


def update_step_status(
    db: Session, run_id: str, step_id: str, status: str,
    progress: float = None, sub_steps: dict = None, kpis: dict = None,
    result_path: str = None, error_message: str = None
):
    updates = ["status = :status"]
    params = {"run_id": run_id, "step_id": step_id, "status": status}

    if progress is not None:
        updates.append("progress = :progress")
        params["progress"] = progress
    if sub_steps is not None:
        updates.append("sub_steps = :sub_steps")
        params["sub_steps"] = json.dumps(sub_steps)
    if kpis is not None:
        updates.append("kpis = :kpis")
        params["kpis"] = json.dumps(kpis)
    if result_path is not None:
        updates.append("result_path = :result_path")
        params["result_path"] = result_path
    if error_message is not None:
        updates.append("error_message = :error_message")
        params["error_message"] = error_message
    if status == "processing":
        updates.append("started_at = CURRENT_TIMESTAMP")
    if status in ("completed", "failed"):
        updates.append("completed_at = CURRENT_TIMESTAMP")

    sql = f"UPDATE step_results SET {', '.join(updates)} WHERE run_id = :run_id AND step_id = :step_id"
    db.execute(text(sql), params)
    db.commit()


def get_step_results(db: Session, run_id: str) -> List[Dict]:
    result = db.execute(text("""
        SELECT step_id, status, progress, sub_steps, kpis, result_path, error_message,
               started_at, completed_at
        FROM step_results WHERE run_id = :run_id ORDER BY step_id
    """), {"run_id": run_id})
    rows = result.fetchall()
    return [{
        "step_id": r[0], "status": r[1], "progress": r[2] or 0,
        "sub_steps": r[3] if isinstance(r[3], dict) else json.loads(r[3]) if r[3] else {},
        "kpis": r[4] if isinstance(r[4], dict) else json.loads(r[4]) if r[4] else {},
        "result_path": r[5], "error_message": r[6],
        "started_at": r[7], "completed_at": r[8]
    } for r in rows]


def get_step_result(db: Session, run_id: str, step_id: str) -> Optional[Dict]:
    result = db.execute(text("""
        SELECT step_id, status, progress, sub_steps, kpis, result_path, error_message
        FROM step_results WHERE run_id = :run_id AND step_id = :step_id
    """), {"run_id": run_id, "step_id": step_id})
    row = result.fetchone()
    if not row:
        return None
    return {
        "step_id": row[0], "status": row[1], "progress": row[2] or 0,
        "sub_steps": row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {},
        "kpis": row[4] if isinstance(row[4], dict) else json.loads(row[4]) if row[4] else {},
        "result_path": row[5], "error_message": row[6]
    }


# ── Field Mappings CRUD ──────────────────────────────────────────────────────

def store_field_mappings(db: Session, run_id: str, mappings: List[Dict]):
    for m in mappings:
        db.execute(text("""
            INSERT INTO field_mappings (run_id, source_column, target_field, confidence, method)
            VALUES (:run_id, :source, :target, :conf, :method)
        """), {
            "run_id": run_id, "source": m["source_column"],
            "target": m["target_field"], "conf": m["confidence"],
            "method": m["method"]
        })
    db.commit()


# ── Existing Classification CRUD (preserved from original) ──────────────────

def store_classification(
    db: Session, input_description: str, enhanced_description: str,
    enhancement_quality: int, country: str, predicted_hs_code: str,
    confidence_8: float, confidence_10: float, processing_time_ms: int,
    requires_selection: bool
) -> int:
    result = db.execute(text("""
        INSERT INTO classifications
        (input_description, enhanced_description, enhancement_quality, country,
         predicted_hs_code, confidence_8_digit, confidence_10_digit,
         processing_time_ms, requires_selection)
        VALUES (:desc, :enhanced, :quality, :country, :code, :conf8, :conf10, :time, :req_sel)
        RETURNING id
    """), {
        "desc": input_description, "enhanced": enhanced_description,
        "quality": enhancement_quality, "country": country,
        "code": predicted_hs_code, "conf8": confidence_8, "conf10": confidence_10,
        "time": processing_time_ms, "req_sel": requires_selection
    })
    db.commit()
    return result.scalar()


def store_feedback(db: Session, classification_id: int, shown_options: List[Dict], selected_code: str):
    db.execute(text("""
        UPDATE classifications SET user_selected_code = :code, feedback_timestamp = CURRENT_TIMESTAMP WHERE id = :id
    """), {"code": selected_code, "id": classification_id})
    db.execute(text("""
        INSERT INTO user_feedback (classification_id, shown_options, selected_code, timestamp)
        VALUES (:id, :options, :code, CURRENT_TIMESTAMP)
    """), {"id": classification_id, "options": json.dumps(shown_options), "code": selected_code})
    db.commit()


def check_product_memory(db: Session, description: str, country: str) -> Optional[Dict]:
    import hashlib
    desc_hash = hashlib.sha256(f"{description.lower()}_{country}".encode()).hexdigest()
    result = db.execute(text(
        "SELECT confirmed_hs_code, confidence FROM product_memory WHERE description_hash = :hash"
    ), {"hash": desc_hash})
    row = result.fetchone()
    return {"hs_code": row[0], "confidence": row[1]} if row else None


def save_to_product_memory(db: Session, description: str, country: str, hs_code: str, confidence: float):
    import hashlib
    desc_hash = hashlib.sha256(f"{description.lower()}_{country}".encode()).hexdigest()
    db.execute(text("""
        INSERT INTO product_memory (description_hash, original_description, country, confirmed_hs_code, confidence, last_updated)
        VALUES (:hash, :desc, :country, :code, :conf, CURRENT_TIMESTAMP)
        ON CONFLICT (description_hash) DO UPDATE SET
            confirmed_hs_code = :code, confidence = :conf, last_updated = CURRENT_TIMESTAMP
    """), {"hash": desc_hash, "desc": description, "country": country, "code": hs_code, "conf": confidence})
    db.commit()


def create_batch_job(db: Session, filename: str, total_items: int) -> str:
    batch_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO batch_jobs (id, filename, total_items, status, created_at)
        VALUES (:id, :filename, :total, 'processing', CURRENT_TIMESTAMP)
    """), {"id": batch_id, "filename": filename, "total": total_items})
    db.commit()
    return batch_id


def update_batch_progress(db: Session, batch_id: str, processed_items: int):
    db.execute(text("UPDATE batch_jobs SET processed_items = :p WHERE id = :id"), {"p": processed_items, "id": batch_id})
    db.commit()


def complete_batch_job(db: Session, batch_id: str, results: List[Dict]):
    db.execute(text("""
        UPDATE batch_jobs SET status = 'completed', results = :results, completed_at = CURRENT_TIMESTAMP WHERE id = :id
    """), {"results": json.dumps(results), "id": batch_id})
    db.commit()


def get_batch_status(db: Session, batch_id: str) -> Optional[Dict]:
    result = db.execute(text("""
        SELECT id, status, total_items, processed_items, results, created_at, completed_at FROM batch_jobs WHERE id = :id
    """), {"id": batch_id})
    row = result.fetchone()
    if not row:
        return None
    return {
        "batch_id": row[0], "status": row[1], "total_items": row[2],
        "processed_items": row[3], "results": json.loads(row[4]) if row[4] else None,
        "created_at": row[5], "completed_at": row[6]
    }


def test_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
