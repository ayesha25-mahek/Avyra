"""
api/engineering_routes.py
-------------------------
API Router for Engineering Document-to-Drawing, Document-to-Spreadsheet,
and Safe Spreadsheet Data Correction.

Endpoints:
  POST /api/drawing/extract-requirements   — Extracts components, dimensions, and tags from doc
  POST /api/drawing/generate-cad           — Generates deterministic SVG and AutoCAD DXF from approved spec
  POST /api/spreadsheet/extract-from-doc  — Extracts proposed inventories, schedules, and readings for review
  POST /api/spreadsheet/generate-workbook  — Generates styled multi-sheet XLSX from approved schema
  POST /api/spreadsheet/audit-clean       — Audits spreadsheet for duplicates, missing, formulas, outliers
  POST /api/spreadsheet/apply-corrections — Safely applies approved fixes, creates corrected XLSX & preserves raw
"""

import json
import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from services.cad_drawing_generator import cad_drawing_generator
from services.doc_to_spreadsheet_generator import doc_to_spreadsheet_generator
from services.spreadsheet_cleaner_service import spreadsheet_cleaner_service
from services.document_reader import DocumentReader
from api.auth_routes import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(tags=["engineering-workspaces"])

UPLOAD_TEMP_DIR = Path("output/uploads/temp")
UPLOAD_TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# 1. DOCUMENT-TO-ENGINEERING-DRAWING GENERATOR ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/drawing/extract-requirements")
async def extract_drawing_requirements(
    request: Request,
    text: Optional[str] = Form(default=""),
    files: List[UploadFile] = File(default=[]),
    authorization: Optional[str] = Header(None),
):
    """
    Extracts explicit dimensions, component tags, materials, and connections
    from uploaded documents (PDF, DOCX, TXT, image) for engineer review.
    """
    # Enforce authentication & role if token provided
    if authorization:
        user = get_current_user(authorization)
        if not has_permission(user, "drawing_tools") and not has_permission(user, "all"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{user.get('role')}' is not authorized to use engineering drawing generator.",
            )

    extracted_text = text or ""
    filename = "document"

    if files:
        reader = DocumentReader()
        for f in files:
            if f.filename:
                filename = f.filename
                dest = UPLOAD_TEMP_DIR / f"{uuid.uuid4().hex}_{f.filename}"
                with open(dest, "wb") as buf:
                    shutil.copyfileobj(f.file, buf)
                try:
                    file_text = reader.read(str(dest))
                    extracted_text += "\n" + file_text
                except Exception as exc:
                    logger.warning("Error reading file %s: %s", f.filename, exc)
                finally:
                    if dest.exists():
                        try:
                            dest.unlink()
                        except Exception:
                            pass

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found. Please upload a supported PDF, DOCX, TXT, image or provide text.",
        )

    requirements = cad_drawing_generator.extract_requirements_from_text(extracted_text, filename)
    return {
        "status": "success",
        "requirements": requirements,
        "source_length": len(extracted_text),
    }


class GenerateCadRequest(BaseModel):
    title: str = Field(..., description="Drawing title")
    drawing_number: Optional[str] = Field(default="DWG-2026-001")
    revision: Optional[str] = Field(default="REV 0 (DRAFT)")
    project_unit: Optional[str] = Field(default="Fractionation Section")
    drawing_type: str = Field(default="pid_schematic", description="2d_mechanical | equipment_arrangement | process_flow | pid_schematic")
    components: List[Dict[str, Any]] = Field(default_factory=list)
    connections: List[Dict[str, Any]] = Field(default_factory=list)
    dimensions: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


@router.post("/drawing/generate-cad")
async def generate_cad_drawing(
    req: GenerateCadRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Generates deterministic vector SVG and AutoCAD DXF drawings from approved requirements.
    """
    if authorization:
        user = get_current_user(authorization)
        if not has_permission(user, "drawing_tools") and not has_permission(user, "all"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{user.get('role')}' is not authorized to generate CAD drawings.",
            )

    spec = req.model_dump()
    result = cad_drawing_generator.generate_drawing(spec)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 2. DOCUMENT-TO-EXCEL WORKBOOK GENERATOR ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/spreadsheet/extract-from-doc")
async def extract_spreadsheet_tables(
    request: Request,
    text: Optional[str] = Form(default=""),
    files: List[UploadFile] = File(default=[]),
    authorization: Optional[str] = Header(None),
):
    """
    Extracts structured tables (inventories, schedules, readings) from technical document.
    Returns proposed columns and rows for engineer review prior to generation.
    """
    if authorization:
        user = get_current_user(authorization)
        if not has_permission(user, "spreadsheet_tools") and not has_permission(user, "all"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{user.get('role')}' is not authorized to use document-to-spreadsheet generator.",
            )

    extracted_text = text or ""
    filename = "document"

    if files:
        reader = DocumentReader()
        for f in files:
            if f.filename:
                filename = f.filename
                dest = UPLOAD_TEMP_DIR / f"{uuid.uuid4().hex}_{f.filename}"
                with open(dest, "wb") as buf:
                    shutil.copyfileobj(f.file, buf)
                try:
                    file_text = reader.read(str(dest))
                    extracted_text += "\n" + file_text
                except Exception as exc:
                    logger.warning("Error reading file %s: %s", f.filename, exc)
                finally:
                    if dest.exists():
                        try:
                            dest.unlink()
                        except Exception:
                            pass

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found. Please upload a supported PDF, DOCX, TXT, image or provide text.",
        )

    schema = doc_to_spreadsheet_generator.extract_tables_from_doc(extracted_text, filename)
    return {
        "status": "success",
        "proposed_schema": schema,
    }


class GenerateWorkbookRequest(BaseModel):
    workbook_title: str
    source_filename: Optional[str] = "document"
    sheets: List[Dict[str, Any]]


@router.post("/spreadsheet/generate-workbook")
async def generate_spreadsheet_workbook(
    req: GenerateWorkbookRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Generates genuine formatted multi-sheet Excel workbook (.xlsx) from approved table schema.
    """
    if authorization:
        user = get_current_user(authorization)
        if not has_permission(user, "spreadsheet_tools") and not has_permission(user, "all"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{user.get('role')}' is not authorized to generate spreadsheet workbooks.",
            )

    approved_schema = req.model_dump()
    result = doc_to_spreadsheet_generator.generate_workbook(approved_schema)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 3. SPREADSHEET AUDIT & SAFE DATA CORRECTION ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/spreadsheet/audit-clean")
async def audit_spreadsheet_data(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    """
    Performs data quality audit on uploaded spreadsheet or CSV.
    Detects duplicates, missing values, formula errors, format inconsistencies, and outliers.
    Returns proposed corrections and before/after previews.
    """
    if authorization:
        user = get_current_user(authorization)
        if not has_permission(user, "spreadsheet_tools") and not has_permission(user, "all"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{user.get('role')}' is not authorized to use spreadsheet cleaner.",
            )

    filename = file.filename or "dataset.csv"
    dest = UPLOAD_TEMP_DIR / f"{uuid.uuid4().hex}_{filename}"
    with open(dest, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    try:
        headers, rows = spreadsheet_cleaner_service.parse_tabular_data(str(dest))
        if not headers or not rows:
            raise HTTPException(status_code=400, detail="Uploaded file does not contain valid tabular rows.")

        audit_res = spreadsheet_cleaner_service.audit_spreadsheet(headers, rows, filename)
        return {
            "status": "success",
            "audit": audit_res,
            "raw_headers": headers,
            "raw_rows": rows,
        }
    finally:
        if dest.exists():
            try:
                dest.unlink()
            except Exception:
                pass


class ApplyCorrectionsRequest(BaseModel):
    headers: List[str]
    original_rows: List[List[Any]]
    approved_correction_ids: List[str]
    all_proposed_corrections: List[Dict[str, Any]]
    source_filename: Optional[str] = "dataset.csv"


@router.post("/spreadsheet/apply-corrections")
async def apply_spreadsheet_corrections(
    req: ApplyCorrectionsRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Applies only user-approved corrections.
    Non-destructive: Preserves original raw copy and creates a separate corrected .xlsx.
    """
    if authorization:
        user = get_current_user(authorization)
        if not has_permission(user, "spreadsheet_tools") and not has_permission(user, "all"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{user.get('role')}' is not authorized to apply spreadsheet corrections.",
            )

    # Cast row cells to strings
    string_rows = [[str(c) for c in r] for r in req.original_rows]

    result = spreadsheet_cleaner_service.apply_corrections(
        headers=req.headers,
        original_rows=string_rows,
        approved_correction_ids=req.approved_correction_ids,
        all_proposed_corrections=req.all_proposed_corrections,
        source_filename=req.source_filename,
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 3. MANAGER EXECUTIVE WORKSPACE ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

class ReviewActionRequest(BaseModel):
    review_id: str
    action: str  # 'approve' | 'reject' | 'request_revision'
    comments: Optional[str] = ""
    reviewer_role: Optional[str] = "manager"


# In-memory audit tracker for pending reviews & approvals
_PENDING_REVIEWS: List[Dict[str, Any]] = [
    {
        "id": "rev-101",
        "title": "CDU-1 Atmospheric Column Flange Pitting Inspection",
        "category": "inspection",
        "status": "pending_approval",
        "submitted_by": "inspector@avyara.internal",
        "submitted_at": "2026-10-09 04:30 UTC",
        "risk_level": "HIGH",
        "deliverables": ["inspection_report.docx", "infographic_flange.svg"],
        "summary": "Local pitting depth 1.8mm exceeds 1.5mm ASME Section VIII allowance on Flange FL-204.",
    },
    {
        "id": "rev-102",
        "title": "Centrifugal Slurry Pump P-102A Impeller Clearance Drawing",
        "category": "engineering",
        "status": "pending_approval",
        "submitted_by": "engineer@avyara.internal",
        "submitted_at": "2026-10-09 05:15 UTC",
        "risk_level": "MEDIUM",
        "deliverables": ["drawing_cad.svg", "technical_report.docx"],
        "summary": "Shaft runout corrected to 0.04mm. Approved CAD drawing package awaiting sign-off.",
    },
    {
        "id": "rev-103",
        "title": "Quarterly Refinery Operating Pressure Telemetry Outliers",
        "category": "data",
        "status": "approved",
        "submitted_by": "analyst@avyara.internal",
        "submitted_at": "2026-10-08 18:20 UTC",
        "risk_level": "LOW",
        "deliverables": ["corrected_telemetry.xlsx", "outlier_analysis.docx"],
        "summary": "14 sensor outlier spikes reconciled against redundant transmitter PT-301.",
    },
]


@router.get("/manager/reviews")
async def get_manager_reviews(authorization: Optional[str] = Header(None)):
    """Returns active pending human reviews and completed sign-offs."""
    return {"status": "success", "reviews": _PENDING_REVIEWS}


@router.post("/manager/reviews/action")
async def update_manager_review_action(
    req: ReviewActionRequest,
    authorization: Optional[str] = Header(None),
):
    """Records human review decision (approve, reject, request revision) in on-premise audit trail."""
    for rev in _PENDING_REVIEWS:
        if rev["id"] == req.review_id:
            rev["status"] = "approved" if req.action == "approve" else "revision_requested" if req.action == "request_revision" else "rejected"
            rev["decision_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            rev["decision_comments"] = req.comments
            return {"status": "success", "review": rev}

    raise HTTPException(status_code=404, detail=f"Review '{req.review_id}' not found.")
