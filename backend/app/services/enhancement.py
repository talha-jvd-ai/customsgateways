"""
Step 2: AI Description Enrichment (Improved with batch processing)

Optimizations over original:
- Batch assessment: 50 descriptions per LLM call instead of 1
- Selective enhancement: Only enhance descriptions with quality < 7
- Batch enhancement: 20 descriptions per LLM call instead of 1
- Expected improvement: ~2-3 items/sec → ~20-30 items/sec
"""

from openai import OpenAI
from typing import Dict, List
import json
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)


# ── Single-item functions (preserved for standalone classification) ───────────

def assess_description_quality(description: str) -> Dict:
    """Assess quality of a single description. Used by standalone classifier."""
    prompt = f"""Analyze this customs product description: "{description}"

For customs classification, assess what information is present and missing.

Required attributes: Material/composition, Purpose/function, Type/category, Physical properties

Return ONLY JSON: {{"quality_score": <1-10>, "missing": ["list"], "present": ["list"]}}

Score: 9-10=Complete, 7-8=Good, 4-6=Basic, 1-3=Very incomplete. Be strict."""

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1, max_tokens=200
        )
        result_text = response.choices[0].message.content.strip()
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        return json.loads(result_text)
    except Exception as e:
        print(f"Quality assessment failed: {e}")
        return {"quality_score": 5, "missing": ["material", "purpose"], "present": []}


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=5))
def enhance_description(description: str, country: str) -> Dict:
    """Enhance a single description. Used by standalone classifier."""
    prompt = f"""You are a customs classification assistant. Enhance this product description for HS code classification.

Original: "{description}" | Country: {country}

Rules: DO NOT invent details. DO add general category/type if obvious. Keep it factual.
Example: "JACKET" → "JACKET, textile outerwear garment"

Return ONLY JSON: {{"enhanced_description": "...", "changes_made": "..."}}"""

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2, max_tokens=150
        )
        result_text = response.choices[0].message.content.strip()
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(result_text)
        return {"enhanced_description": result["enhanced_description"],
                "changes_made": result.get("changes_made", "")}
    except Exception as e:
        print(f"Enhancement failed: {e}")
        return {"enhanced_description": description, "changes_made": "Enhancement failed"}


def process_description(description: str, country: str) -> Dict:
    """Single-item description pipeline (used by standalone classification)."""
    assessment = assess_description_quality(description)
    quality_score = assessment["quality_score"]

    if quality_score >= 7:
        return {"original": description, "enhanced": description,
                "quality_score": quality_score, "needs_user_input": False,
                "missing_attributes": assessment.get("missing", [])}
    else:
        enhancement = enhance_description(description, country)
        return {"original": description, "enhanced": enhancement["enhanced_description"],
                "quality_score": quality_score,
                "needs_user_input": quality_score < 4,
                "missing_attributes": assessment.get("missing", []),
                "changes_made": enhancement.get("changes_made", ""),
                "warning": "Description quality is low." if quality_score < 4 else None}


# ── Batch functions (new, for pipeline processing) ───────────────────────────

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
def batch_assess_quality(descriptions: List[str]) -> List[Dict]:
    """Assess quality of multiple descriptions in a single LLM call."""
    numbered = "\n".join(f"{i+1}. \"{d[:100]}\"" for i, d in enumerate(descriptions))

    prompt = f"""Assess these customs product descriptions for classification quality (1-10 scale).
Be strict - short descriptions should score 3-5.

Descriptions:
{numbered}

Return ONLY a JSON array with one object per description:
[{{"index": 1, "quality_score": <1-10>, "needs_enhancement": true/false}}, ...]

needs_enhancement = true if quality_score < 7."""

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1, max_tokens=len(descriptions) * 50
    )
    result_text = response.choices[0].message.content.strip()
    result_text = result_text.replace("```json", "").replace("```", "").strip()

    try:
        results = json.loads(result_text)
        if isinstance(results, list):
            return results
    except json.JSONDecodeError:
        pass

    # Fallback: assume all need enhancement
    return [{"index": i + 1, "quality_score": 5, "needs_enhancement": True} for i in range(len(descriptions))]


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
def batch_enhance_descriptions(descriptions: List[Dict]) -> List[Dict]:
    """Enhance multiple descriptions in a single LLM call."""
    numbered = "\n".join(
        f"{i+1}. \"{d['description'][:100]}\" (country: {d.get('country', 'unknown')})"
        for i, d in enumerate(descriptions)
    )

    prompt = f"""You are a customs classification assistant. Enhance these product descriptions.

Rules: DO NOT invent details. Add general category/type if obvious. Keep factual.

Descriptions:
{numbered}

Return ONLY JSON array:
[{{"index": 1, "enhanced": "enhanced description here"}}, ...]"""

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2, max_tokens=len(descriptions) * 100
    )
    result_text = response.choices[0].message.content.strip()
    result_text = result_text.replace("```json", "").replace("```", "").strip()

    try:
        results = json.loads(result_text)
        if isinstance(results, list):
            return results
    except json.JSONDecodeError:
        pass

    # Fallback
    return [{"index": i + 1, "enhanced": d["description"]} for i, d in enumerate(descriptions)]


class EnrichmentService:
    """Step 2: Batch description enrichment for the pipeline."""

    def process_batch(self, items: List[Dict], run_id: str = None, progress_callback=None) -> List[Dict]:
        """
        Process a batch of items through enrichment.
        Each item should have: {"description": str, "country": str, "row_index": int, ...}
        Returns items with added: enhanced_description, quality_score
        """
        total = len(items)
        if total == 0:
            return items

        # Phase 1: Batch assess quality
        descriptions = [item.get("description", "") or "" for item in items]
        batch_size = settings.batch_size_assessment
        all_assessments = []

        for i in range(0, total, batch_size):
            batch = descriptions[i:i + batch_size]
            try:
                assessments = batch_assess_quality(batch)
                all_assessments.extend(assessments)
            except Exception:
                all_assessments.extend([{"quality_score": 5, "needs_enhancement": True}] * len(batch))

            if progress_callback:
                pct = min(40, int((i + len(batch)) / total * 40))
                progress_callback(pct, None)

        # Assign quality scores
        for idx, item in enumerate(items):
            assessment = all_assessments[idx] if idx < len(all_assessments) else {"quality_score": 5, "needs_enhancement": True}
            item["quality_score"] = assessment.get("quality_score", 5)
            item["needs_enhancement"] = assessment.get("needs_enhancement", True)

        # Phase 2: Batch enhance only those that need it
        to_enhance = [(idx, item) for idx, item in enumerate(items) if item.get("needs_enhancement", True)]
        enhanced_count = 0
        enhance_batch_size = settings.batch_size_enrichment

        for i in range(0, len(to_enhance), enhance_batch_size):
            batch = to_enhance[i:i + enhance_batch_size]
            batch_input = [{"description": items[idx].get("description", ""),
                            "country": items[idx].get("country", "")}
                           for idx, _ in batch]

            try:
                results = batch_enhance_descriptions(batch_input)
                for j, (idx, _) in enumerate(batch):
                    if j < len(results):
                        items[idx]["enhanced_description"] = results[j].get("enhanced", items[idx].get("description", ""))
                        enhanced_count += 1
                    else:
                        items[idx]["enhanced_description"] = items[idx].get("description", "")
            except Exception:
                for idx, _ in batch:
                    items[idx]["enhanced_description"] = items[idx].get("description", "")

            if progress_callback:
                pct = 40 + min(60, int((i + len(batch)) / max(len(to_enhance), 1) * 60))
                progress_callback(pct, None)

        # Items that don't need enhancement keep original
        for item in items:
            if "enhanced_description" not in item:
                item["enhanced_description"] = item.get("description", "")

        if progress_callback:
            progress_callback(100, None)

        return items
