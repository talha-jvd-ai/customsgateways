"""
Step 1: AI-Powered File Extraction & Mapping

Handles two modes:
- Mode A: Structured files (CSV/Excel) → column mapping to 49-field format
- Mode B: Unstructured text (emails, invoices, OCR) → AI extraction

Three-tier mapping for structured files:
1. Exact match via HEADER_ALIASES
2. Fuzzy match via normalized token comparison
3. AI match via single LLM call for remaining unmapped columns
"""

import pandas as pd
import io
import re
import json
import os
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.services.field_definitions import TARGET_FIELDS, HEADER_ALIASES, VALIDATION_RULES

settings = get_settings()
llm_client = OpenAI(api_key=settings.openai_api_key)


# ── File Reading ─────────────────────────────────────────────────────────────

def read_file(file_path: str) -> Tuple[pd.DataFrame, Dict]:
    """Read CSV or Excel file with auto-detection of format, delimiter, encoding."""
    ext = os.path.splitext(file_path)[1].lower()
    metadata = {"file_type": ext, "encoding": None, "delimiter": None, "sheet": None}

    if ext in (".xlsx", ".xls"):
        return _read_excel(file_path, metadata)
    elif ext == ".csv":
        return _read_csv(file_path, metadata)
    elif ext == ".txt":
        return _read_text_as_unstructured(file_path, metadata)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _read_excel(file_path: str, metadata: Dict) -> Tuple[pd.DataFrame, Dict]:
    """Read Excel file, pick sheet with most columns."""
    xls = pd.ExcelFile(file_path)
    best_sheet = None
    best_cols = 0
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, nrows=5)
        if len(df.columns) > best_cols:
            best_cols = len(df.columns)
            best_sheet = sheet
    metadata["sheet"] = best_sheet
    df = pd.read_excel(xls, sheet_name=best_sheet, dtype=str)
    df = df.dropna(how="all")
    return df, metadata


def _read_csv(file_path: str, metadata: Dict) -> Tuple[pd.DataFrame, Dict]:
    """Read CSV with auto-detection of encoding and delimiter."""
    encodings = ["utf-8", "utf-8-sig", "iso-8859-1", "cp1252"]
    raw_bytes = open(file_path, "rb").read()

    for enc in encodings:
        try:
            text = raw_bytes.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        text = raw_bytes.decode("utf-8", errors="replace")
        enc = "utf-8"
    metadata["encoding"] = enc

    lines = text.split("\n")

    # Skip leading blank lines
    start_line = 0
    while start_line < len(lines) and lines[start_line].strip() == "":
        start_line += 1

    # Skip separator declaration line (e.g., "sep=;")
    if start_line < len(lines) and lines[start_line].strip().lower().startswith("sep="):
        declared_sep = lines[start_line].strip().split("=", 1)[1].strip()
        metadata["delimiter"] = declared_sep
        start_line += 1

    text = "\n".join(lines[start_line:])

    # Auto-detect delimiter from first non-empty line
    if metadata["delimiter"] is None:
        first_line = lines[start_line] if start_line < len(lines) else ""
        delimiters = {";": first_line.count(";"), ",": first_line.count(","),
                      "\t": first_line.count("\t"), "|": first_line.count("|")}
        metadata["delimiter"] = max(delimiters, key=delimiters.get) if max(delimiters.values()) > 0 else ","

    df = pd.read_csv(io.StringIO(text), sep=metadata["delimiter"], dtype=str, on_bad_lines="skip")
    df = df.dropna(how="all")
    # Drop any unnamed trailing columns
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    return df, metadata


def _read_text_as_unstructured(file_path: str, metadata: Dict) -> Tuple[pd.DataFrame, Dict]:
    """Read a text file as a single unstructured record."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    metadata["file_type"] = "unstructured"
    df = pd.DataFrame([{"Raw Input": content}])
    return df, metadata


def detect_input_mode(df: pd.DataFrame) -> str:
    """Determine if file is structured (has column headers) or unstructured."""
    if len(df.columns) <= 3 and any("raw" in str(c).lower() or "input" in str(c).lower() for c in df.columns):
        return "unstructured"
    if len(df.columns) >= 5:
        return "structured"
    first_val = str(df.iloc[0, 0]) if len(df) > 0 else ""
    if len(first_val) > 200 or "\n" in first_val:
        return "unstructured"
    return "structured"


# ── Tier 1: Exact Match ──────────────────────────────────────────────────────

def exact_match(source_columns: List[str]) -> Dict[str, str]:
    """Map columns using exact match against known aliases."""
    mappings = {}
    alias_lookup = {k.lower().strip(): v for k, v in HEADER_ALIASES.items()}

    for col in source_columns:
        normalized = col.lower().strip()
        # Remove surrounding quotes if present
        normalized = normalized.strip('"').strip("'")
        # Direct match
        if normalized in alias_lookup:
            mappings[col] = alias_lookup[normalized]
            continue
        # Try with underscores replaced by spaces and vice versa
        alt1 = normalized.replace("_", " ")
        alt2 = normalized.replace(" ", "_")
        if alt1 in alias_lookup:
            mappings[col] = alias_lookup[alt1]
        elif alt2 in alias_lookup:
            mappings[col] = alias_lookup[alt2]

    return mappings


# ── Tier 2: Fuzzy Match ──────────────────────────────────────────────────────

def _normalize_for_fuzzy(text: str) -> str:
    """Normalize text for fuzzy comparison."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def fuzzy_match(unmapped_columns: List[str], already_mapped_targets: set, threshold: float = 0.80) -> Dict[str, str]:
    """Fuzzy match remaining columns against target fields."""
    mappings = {}
    target_normalized = {_normalize_for_fuzzy(t): t for t in TARGET_FIELDS}

    for col in unmapped_columns:
        col_norm = _normalize_for_fuzzy(col)
        if not col_norm:
            continue
        best_score = 0
        best_target = None

        for target_norm, target_original in target_normalized.items():
            if target_original in already_mapped_targets:
                continue
            score = SequenceMatcher(None, col_norm, target_norm).ratio()
            if score > best_score:
                best_score = score
                best_target = target_original

        if best_score >= threshold and best_target:
            mappings[col] = best_target

    return mappings


# ── Tier 3: AI Match ─────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
def ai_match(unmapped_columns: List[str], sample_data: Dict[str, List[str]], already_mapped_targets: set) -> Dict[str, str]:
    """Use LLM to map remaining unmapped columns. Single call per file."""
    if not unmapped_columns:
        return {}

    available_targets = [t for t in TARGET_FIELDS if t not in already_mapped_targets]

    column_info = []
    for col in unmapped_columns[:30]:  # Cap at 30 to avoid token limits
        samples = sample_data.get(col, [])[:3]
        samples_str = " | ".join(str(s) for s in samples if pd.notna(s))
        column_info.append(f'  - "{col}" → samples: [{samples_str}]')

    prompt = f"""You are a customs/logistics data expert. Map these source columns to the correct target field.

Source columns (with sample values):
{chr(10).join(column_info)}

Available target fields:
{json.dumps(available_targets)}

Rules:
- Only map if you are confident (>80% sure)
- Use null for columns you cannot map
- Each target field can only be used once

Return ONLY valid JSON object: {{"source_column": "target_field_or_null", ...}}"""

    response = llm_client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000
    )
    result_text = response.choices[0].message.content.strip()
    result_text = result_text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(result_text)
        return {k: v for k, v in result.items() if v and v in TARGET_FIELDS}
    except json.JSONDecodeError:
        return {}


# ── Unstructured Document Extraction ─────────────────────────────────────────

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
def extract_from_unstructured(raw_text: str) -> Dict[str, str]:
    """Extract 49-field data from unstructured text (email, invoice, OCR, etc.)."""
    prompt = f"""You are an expert customs data extraction system. Extract shipping/trade data from this document and map it to the target fields.

Document:
---
{raw_text[:3000]}
---

Target fields to extract:
{json.dumps(TARGET_FIELDS)}

Rules:
- Extract ONLY information explicitly present in the document
- For country codes, use ISO 3166-1 alpha-2 (2 letters)
- For currency, use ISO 4217 (3 letters)
- Normalize weight units to KG or LBS
- If a value is not present, use null
- Calculate: Line Weight = Item Quantity * Item Weight, Line Value = Item Quantity * Item Value

Return ONLY valid JSON: {{"field_name": "extracted_value", ...}}"""

    response = llm_client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000
    )
    result_text = response.choices[0].message.content.strip()
    result_text = result_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {}


def extract_batch_unstructured(raw_texts: List[Dict]) -> pd.DataFrame:
    """Extract data from multiple unstructured text records."""
    rows = []
    for item in raw_texts:
        text = item.get("Raw Input", item.get("raw_input", str(item)))
        extracted = extract_from_unstructured(str(text))
        row = {f: extracted.get(f, None) for f in TARGET_FIELDS}
        rows.append(row)
    return pd.DataFrame(rows)


# ── Validation & Normalization ───────────────────────────────────────────────

def _safe_get_scalar(df, idx, field):
    """Safely get a scalar value from a DataFrame, handling duplicates."""
    try:
        val = df.at[idx, field]
        # If val is a Series (duplicate columns), take first value
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        return val
    except (KeyError, IndexError):
        return None


def _safe_float(val):
    """Safely convert a value to float."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if pd.isna(val):
            return None
        return float(val)
    val_str = str(val).strip()
    if val_str == "" or val_str.lower() == "nan" or val_str.lower() == "none":
        return None
    try:
        cleaned = val_str.replace(",", ".").replace(" ", "")
        cleaned = re.sub(r"[^\d.\-]", "", cleaned)
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None


def validate_and_normalize(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict], Dict]:
    """Validate and normalize data according to template rules."""
    errors = []
    stats = {"total_rows": len(df), "valid_rows": 0, "errors": 0}

    for idx in df.index:
        row_errors = []

        # Country code validation & normalization
        for field in ["Shipper Country Code", "Consignee Country Code", "Item Country of origin"]:
            if field not in df.columns:
                continue
            val = _safe_get_scalar(df, idx, field)
            val_str = str(val).strip().upper() if val is not None and str(val).strip() not in ["", "nan", "None"] else ""
            if val_str:
                # Handle full country names by taking just the code if it's 2 chars
                if len(val_str) == 2:
                    df.at[idx, field] = val_str
                elif len(val_str) > 2:
                    # Could be full country name like "UNITED STATES" — keep first 2 of code column
                    # but don't flag as error, just truncate
                    df.at[idx, field] = val_str[:2]

        # Currency normalization
        currency = _safe_get_scalar(df, idx, "Currency") if "Currency" in df.columns else None
        if currency is not None:
            currency_str = str(currency).strip().upper()
            if currency_str and currency_str not in ["", "nan", "None"]:
                df.at[idx, "Currency"] = currency_str

        # Weight UOM normalization
        if "Weight UOM" in df.columns:
            wuom = _safe_get_scalar(df, idx, "Weight UOM")
            wuom_str = str(wuom).strip().upper() if wuom is not None and str(wuom).strip() not in ["", "nan", "None"] else ""
            normalize_map = {"KGS": "KG", "KILOS": "KG", "KILOGRAM": "KG", "KILOGRAMS": "KG",
                             "LB": "LBS", "POUND": "LBS", "POUNDS": "LBS", "G": "KG", "GRAMS": "KG"}
            if wuom_str in normalize_map:
                df.at[idx, "Weight UOM"] = normalize_map[wuom_str]
            elif wuom_str:
                df.at[idx, "Weight UOM"] = wuom_str

        # Numeric field conversion
        for field in ["Item Quantity", "Item Weight", "Item Value", "Line Weight",
                       "Line Value", "Total Weight", "Total Value", "Shipping rate"]:
            if field not in df.columns:
                continue
            val = _safe_get_scalar(df, idx, field)
            numeric = _safe_float(val)
            if numeric is not None:
                df.at[idx, field] = numeric
            elif val is not None and str(val).strip() not in ["", "nan", "None"]:
                row_errors.append({"field": field, "issue": f"Non-numeric value: {val}", "row": int(idx)})

        # Weight/value auto-calculation
        try:
            qty = _safe_float(_safe_get_scalar(df, idx, "Item Quantity"))
            item_wt = _safe_float(_safe_get_scalar(df, idx, "Item Weight"))
            item_val = _safe_float(_safe_get_scalar(df, idx, "Item Value"))
            line_wt = _safe_float(_safe_get_scalar(df, idx, "Line Weight"))
            line_val = _safe_float(_safe_get_scalar(df, idx, "Line Value"))

            if qty and item_wt and not line_wt:
                df.at[idx, "Line Weight"] = round(qty * item_wt, 2)
            if qty and item_val and not line_val:
                df.at[idx, "Line Value"] = round(qty * item_val, 2)
        except (ValueError, TypeError):
            pass

        if row_errors:
            errors.extend(row_errors)
        else:
            stats["valid_rows"] += 1

    stats["errors"] = len(errors)
    return df, errors, stats


def calculate_completeness(df: pd.DataFrame) -> float:
    """Calculate what percentage of mandatory fields are populated."""
    mandatory_fields = [
        "Reference1", "Shipper Name", "Shipper Country Code",
        "Consignee", "Consignee Country Code",
        "Description", "Item Quantity", "Weight UOM", "Currency"
    ]
    if len(df) == 0:
        return 0.0
    present = 0
    total = len(mandatory_fields) * len(df)
    for field in mandatory_fields:
        if field in df.columns:
            for idx in df.index:
                val = _safe_get_scalar(df, idx, field)
                val_str = str(val).strip() if val is not None else ""
                if val_str and val_str.lower() not in ["", "nan", "none"]:
                    present += 1
    return round((present / total) * 100, 1) if total > 0 else 0.0


# ── Main Extraction Pipeline ─────────────────────────────────────────────────

class ExtractionService:
    """Step 1: Extract, map, validate, and normalize uploaded files."""

    def process(self, file_path: str, run_id: str = None, progress_callback=None) -> Dict:
        """Main extraction pipeline."""
        # 1. Read file
        df, metadata = read_file(file_path)
        if progress_callback:
            progress_callback(10, {"Extract Status": True})

        # 2. Detect mode
        mode = detect_input_mode(df)

        if mode == "unstructured":
            return self._process_unstructured(df, metadata, run_id, progress_callback)
        else:
            return self._process_structured(df, metadata, run_id, progress_callback)

    def _process_structured(self, df: pd.DataFrame, metadata: Dict, run_id: str, progress_callback) -> Dict:
        """Process structured CSV/Excel files."""
        source_columns = list(df.columns)
        sample_data = {col: df[col].head(3).tolist() for col in source_columns}

        # Tier 1: Exact match
        exact_mappings = exact_match(source_columns)
        mappings = dict(exact_mappings)
        mapped_targets = set(mappings.values())
        if progress_callback:
            progress_callback(30, {"Extract Status": True, "Mapping Status": False})

        # Tier 2: Fuzzy match for unmapped
        unmapped = [c for c in source_columns if c not in mappings]
        if unmapped:
            fuzzy_mappings = fuzzy_match(unmapped, mapped_targets)
            mappings.update(fuzzy_mappings)
            mapped_targets = set(mappings.values())
        if progress_callback:
            progress_callback(50, {"Extract Status": True, "Mapping Status": False})

        # Tier 3: AI match for still unmapped
        still_unmapped = [c for c in source_columns if c not in mappings]
        if still_unmapped:
            ai_mappings = ai_match(still_unmapped, sample_data, mapped_targets)
            mappings.update(ai_mappings)

        if progress_callback:
            progress_callback(65, {"Extract Status": True, "Mapping Status": True})

        # Build mapping records with method tracking
        mapping_records = []
        for source, target in mappings.items():
            if source in exact_mappings:
                method = "exact"
            elif source in still_unmapped:
                method = "ai"
            else:
                method = "fuzzy"
            mapping_records.append({
                "source_column": source, "target_field": target,
                "confidence": 1.0 if method == "exact" else 0.85 if method == "fuzzy" else 0.75,
                "method": method
            })

        # Rename columns using mappings
        df_mapped = df.rename(columns=mappings)

        # Handle duplicate columns (multiple source cols mapping to same target)
        df_mapped = df_mapped.loc[:, ~df_mapped.columns.duplicated(keep="first")]

        # Ensure all 49 target fields exist, in order
        df_result = df_mapped.reindex(columns=TARGET_FIELDS).copy()

        if progress_callback:
            progress_callback(75, {"Extract Status": True, "Mapping Status": True, "Normalization Status": False})

        # Validate and normalize
        df_result, errors, stats = validate_and_normalize(df_result)

        if progress_callback:
            progress_callback(90, {"Extract Status": True, "Mapping Status": True, "Normalization Status": True, "Completeness Status": False})

        # Calculate completeness
        completeness = calculate_completeness(df_result)

        if progress_callback:
            progress_callback(100, {
                "Extract Status": True, "Mapping Status": True,
                "Normalization Status": True,
                "Completeness Status": completeness > 50
            })

        final_unmapped = [c for c in source_columns if c not in mappings]

        return {
            "success": True,
            "mode": "structured",
            "dataframe": df_result,
            "total_rows": len(df_result),
            "mappings": mapping_records,
            "unmapped_columns": final_unmapped,
            "completeness": completeness,
            "validation_errors": errors,
            "stats": stats,
            "metadata": metadata
        }

    def _process_unstructured(self, df: pd.DataFrame, metadata: Dict, run_id: str, progress_callback) -> Dict:
        """Process unstructured text inputs (emails, invoices, etc.)."""
        if progress_callback:
            progress_callback(20, {"Extract Status": True, "Mapping Status": False})

        records = df.to_dict("records")
        df_result = extract_batch_unstructured(records)

        if progress_callback:
            progress_callback(70, {"Extract Status": True, "Mapping Status": True, "Normalization Status": False})

        df_result, errors, stats = validate_and_normalize(df_result)
        completeness = calculate_completeness(df_result)

        if progress_callback:
            progress_callback(100, {
                "Extract Status": True, "Mapping Status": True,
                "Normalization Status": True,
                "Completeness Status": completeness > 50
            })

        return {
            "success": True,
            "mode": "unstructured",
            "dataframe": df_result,
            "total_rows": len(df_result),
            "mappings": [],
            "unmapped_columns": [],
            "completeness": completeness,
            "validation_errors": errors,
            "stats": stats,
            "metadata": metadata
        }