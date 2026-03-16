"""
Step 3: TARIC Classification (integrated into pipeline)

Preserved from existing project with pipeline adaptation:
- classify_item() unchanged for standalone use
- ClassificationService added for batch pipeline processing
- Pipeline mode skips internal enhancement (already done in Step 2)
"""

from typing import Dict, List, Tuple
import time

from app.services.embedding import generate_embedding, prepare_text_for_embedding
from app.services.enhancement import process_description
from app.services.qdrant_service import search_both_collections
from app.models import HSCodePrediction
from app.config import get_settings

settings = get_settings()


def calculate_confidence(similar_items: List[Dict], predicted_code: str) -> Tuple[float, float]:
    """Calculate confidence scores based on match frequency and similarity."""
    if not similar_items:
        return 0.0, 0.0

    predicted_8 = predicted_code[:8]
    predicted_10 = predicted_code

    matches_8 = sum(1 for item in similar_items if item["payload"]["hs_code_8digit"] == predicted_8)
    matches_10 = sum(1 for item in similar_items if item["payload"]["hs_code"] == predicted_10)

    base_conf_8 = (matches_8 / len(similar_items)) * 100
    base_conf_10 = (matches_10 / len(similar_items)) * 100

    top_similarity = similar_items[0]["score"]
    weight = 0.5 + (top_similarity * 0.5)

    return round(min(base_conf_8 * weight, 100), 2), round(min(base_conf_10 * weight, 100), 2)


def rank_predictions(results: List[Dict]) -> List[HSCodePrediction]:
    """Rank and score predictions from search results."""
    if not results:
        return []

    code_groups = {}
    for item in results:
        hs_code = item["payload"]["hs_code"]
        hs_code_8 = item["payload"]["hs_code_8digit"]
        score = item["score"]

        if hs_code not in code_groups:
            code_groups[hs_code] = {"hs_code": hs_code, "hs_code_8digit": hs_code_8,
                                     "scores": [], "similar_descriptions": []}

        code_groups[hs_code]["scores"].append(score)
        desc = item["payload"].get("description_enhanced") or item["payload"].get("description_original", "")
        if desc and desc not in code_groups[hs_code]["similar_descriptions"]:
            code_groups[hs_code]["similar_descriptions"].append(desc)

    predictions = []
    for data in code_groups.values():
        scores = data["scores"]
        avg_score = sum(scores) / len(scores)
        frequency = len(scores)
        base_confidence = avg_score * 100
        frequency_boost = min(frequency / 3, 1.0)
        combined = base_confidence * (1 + frequency_boost * 0.2)

        confidence_8, confidence_10 = calculate_confidence(
            [{"payload": {"hs_code_8digit": data["hs_code_8digit"], "hs_code": data["hs_code"]}, "score": s}
             for s in scores], data["hs_code"]
        )

        predictions.append(HSCodePrediction(
            hs_code=data["hs_code"], hs_code_8digit=data["hs_code_8digit"],
            confidence=round(combined, 2), confidence_8_digit=confidence_8,
            confidence_10_digit=confidence_10,
            similar_description=data["similar_descriptions"][0] if data["similar_descriptions"] else None
        ))

    predictions.sort(key=lambda x: x.confidence, reverse=True)
    return predictions


def classify_item(description: str, country: str) -> Dict:
    """Standalone classification pipeline (original, unchanged)."""
    start_time = time.time()

    processed = process_description(description, country)
    enhanced_description = processed["enhanced"]
    quality_score = processed["quality_score"]

    text_for_embedding = prepare_text_for_embedding(enhanced_description, country)
    embedding = generate_embedding(text_for_embedding)

    search_results = search_both_collections(embedding=embedding, country=country,
                                              limit_per_collection=settings.top_k_results)
    all_results = search_results["corrections"] + search_results["training"]
    predictions = rank_predictions(all_results)

    if not predictions:
        processing_time = int((time.time() - start_time) * 1000)
        return {"success": False, "error": "No similar items found",
                "enhanced_description": enhanced_description, "quality_score": quality_score,
                "processing_time_ms": processing_time}

    top_prediction = predictions[0]
    requires_selection = top_prediction.confidence_8_digit < settings.confidence_threshold
    processing_time = int((time.time() - start_time) * 1000)

    return {
        "success": True, "requires_selection": requires_selection,
        "predictions": predictions[:3], "top_prediction": top_prediction,
        "enhanced_description": enhanced_description,
        "enhancement_quality": quality_score,
        "processing_time_ms": processing_time,
        "needs_user_input": processed.get("needs_user_input", False),
        "missing_attributes": processed.get("missing_attributes", [])
    }


def validate_hs_code(hs_code: str) -> bool:
    if not hs_code:
        return False
    clean = hs_code.replace(".", "")
    return clean.isdigit() and 8 <= len(clean) <= 10


class ClassificationService:
    """Step 3: Batch classification for the pipeline."""

    def classify_batch(self, items: List[Dict], run_id: str = None, progress_callback=None) -> List[Dict]:
        """
        Classify a batch of items using already-enriched descriptions from Step 2.
        Each item should have: enhanced_description, country (or Item Country of origin)
        """
        total = len(items)
        classified = 0
        high_conf = 0
        med_conf = 0
        low_conf = 0

        for idx, item in enumerate(items):
            description = item.get("enhanced_description") or item.get("description", "")
            country = item.get("country") or item.get("Item Country of origin", "")
            country = str(country)[:2] if country else ""

            try:
                # Generate embedding directly (skip enhancement — already done in Step 2)
                text = prepare_text_for_embedding(description, country)
                embedding = generate_embedding(text)

                # Search Qdrant
                results = search_both_collections(embedding, country, settings.top_k_results)
                all_results = results["corrections"] + results["training"]
                predictions = rank_predictions(all_results)

                if predictions:
                    top = predictions[0]
                    item["taric_code"] = top.hs_code
                    item["confidence_8"] = top.confidence_8_digit
                    item["confidence_10"] = top.confidence_10_digit
                    item["requires_review"] = top.confidence_8_digit < settings.confidence_threshold
                    item["top_3_predictions"] = [
                        {"hs_code": p.hs_code, "confidence": p.confidence_8_digit}
                        for p in predictions[:3]
                    ]

                    if top.confidence_8_digit >= 80:
                        high_conf += 1
                    elif top.confidence_8_digit >= 50:
                        med_conf += 1
                    else:
                        low_conf += 1
                else:
                    item["taric_code"] = None
                    item["confidence_8"] = 0
                    item["confidence_10"] = 0
                    item["requires_review"] = True
                    item["top_3_predictions"] = []
                    low_conf += 1

            except Exception as e:
                item["taric_code"] = None
                item["confidence_8"] = 0
                item["requires_review"] = True
                item["classification_error"] = str(e)
                low_conf += 1

            classified += 1
            if progress_callback and classified % 5 == 0:
                progress_callback(int(classified / total * 100), None)

        if progress_callback:
            progress_callback(100, None)

        # Store distribution stats on the items list (accessible by orchestrator)
        return items
