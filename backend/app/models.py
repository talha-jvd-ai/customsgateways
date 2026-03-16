from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


# ── Pipeline Models ──────────────────────────────────────────────────────────

class PipelineStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecuteRequest(BaseModel):
    run_id: str
    enabled_steps: List[str] = Field(default=["P1", "P2", "P3"])


class UploadResponse(BaseModel):
    run_id: str
    filename: str
    total_rows: int
    detected_columns: List[str]
    status: str = "uploaded"


class StepDetail(BaseModel):
    type: str
    label: Optional[str] = None
    title: Optional[str] = None
    percentage: Optional[float] = None
    value: Optional[str] = None
    message: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    bars: Optional[List[Dict[str, Any]]] = None
    charts: Optional[List[Dict[str, Any]]] = None
    stats: Optional[List[Dict[str, Any]]] = None
    segments: Optional[List[Dict[str, Any]]] = None
    items: Optional[List[Dict[str, Any]]] = None
    buttons: Optional[List[Dict[str, Any]]] = None
    assumptions: Optional[List[str]] = None
    # Catch-all for any extra fields the frontend components need
    model_config = {"extra": "allow"}


class StepResponse(BaseModel):
    step_id: str
    title: str
    description: str
    status: str
    progress: float = 0
    details: List[Dict[str, Any]] = []


class PipelineStatusResponse(BaseModel):
    run_id: str
    status: str
    current_step: Optional[str] = None
    steps: List[StepResponse] = []


class ExecuteResponse(BaseModel):
    run_id: str
    status: str
    message: str


# ── Analytics Models ─────────────────────────────────────────────────────────

class KPICard(BaseModel):
    title: str
    value: str
    trend: Optional[str] = None
    trend_direction: Optional[str] = None  # "up" or "down"


class BeforeAfterCategory(BaseModel):
    name: str
    before: float
    after: float


class BeforeAfterChart(BaseModel):
    title: str
    categories: List[BeforeAfterCategory]


class NextAction(BaseModel):
    type: str
    count: int
    impact: str
    impact_color: Optional[str] = None
    impact_text: Optional[str] = None
    fixability: str
    fixability_color: Optional[str] = None
    icon: Optional[str] = None


class AnalyticsResponse(BaseModel):
    kpi_cards: List[KPICard] = []
    before_after_charts: List[BeforeAfterChart] = []
    financial_impact: Optional[Dict[str, Any]] = None
    next_actions: List[NextAction] = []


# ── Classification Models (from existing project) ───────────────────────────

class ClassificationRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    country: str = Field(..., min_length=2, max_length=2)


class HSCodePrediction(BaseModel):
    hs_code: str
    hs_code_8digit: str
    confidence: float
    confidence_8_digit: float
    confidence_10_digit: float
    similar_description: Optional[str] = None


class ClassificationResponse(BaseModel):
    classification_id: int
    requires_selection: bool
    predicted_hs_code: Optional[str] = None
    confidence_8_digit: Optional[float] = None
    confidence_10_digit: Optional[float] = None
    options: Optional[List[HSCodePrediction]] = None
    enhanced_description: Optional[str] = None
    enhancement_quality: Optional[int] = None
    processing_time_ms: int


class FeedbackRequest(BaseModel):
    classification_id: int
    selected_hs_code: str = Field(..., min_length=8, max_length=10)


class FeedbackResponse(BaseModel):
    status: str
    message: str


class BatchJobResponse(BaseModel):
    batch_id: str
    status: str
    total_items: int
    message: str


class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    total_items: int
    processed_items: int
    progress_percent: float
    results: Optional[List[dict]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    qdrant_connected: bool
    postgres_connected: bool
    openai_configured: bool


# ── Extraction Models ────────────────────────────────────────────────────────

class FieldMapping(BaseModel):
    source_column: str
    target_field: str
    confidence: float
    method: str  # "exact", "fuzzy", "ai"


class ExtractionResult(BaseModel):
    total_rows: int
    mapped_fields: int
    total_fields: int
    completeness: float
    mappings: List[FieldMapping]
    unmapped_columns: List[str]
    validation_errors: List[Dict[str, Any]] = []
