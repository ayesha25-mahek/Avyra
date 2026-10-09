"""
services/document_reader.py
---------------------------
Multimodal Document & Image Ingestion Engine for Avyara Enterprise AI Workbench.

Supports:
1. Native Text PDFs (high-speed extraction via pypdf)
2. Scanned / Image-Only PDFs (automatic detection of insufficient text -> local OCR via Windows Media OCR)
3. Uploaded Images & Inspection Photographs (.png, .jpg, .jpeg, .webp, .bmp, .tiff)
   (local OCR + modular local vision feature extraction)
4. Word Documents (.docx via python-docx)
5. PowerPoint Presentations (.pptx via python-pptx)
6. Plain Text Files (.txt)

Guarantees:
- 100% on-premise execution (external_calls: 0, model_provider: local)
- Zero cloud OCR / cloud vision dependencies
- Graceful fallbacks for empty or corrupted files
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pypdf import PdfReader
from docx import Document
from pptx import Presentation

from services.local_ocr import LocalOcrEngine
from services.local_vision_provider import LocalVisionProvider
from services.multimodal_classifier import multimodal_classifier
from services.industrial_drawing_parser import industrial_drawing_parser
from services.sovereignty_monitor import sovereignty_monitor

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")
DOCUMENT_EXTENSIONS = (".pdf", ".docx", ".txt", ".pptx", ".csv")
ALL_SUPPORTED_EXTENSIONS = DOCUMENT_EXTENSIONS + IMAGE_EXTENSIONS


class DocumentReader:
    """
    Multimodal document and image reader with automatic scanned-PDF detection
    and local on-premise OCR.
    """

    def __init__(self):
        self.ocr = LocalOcrEngine()
        self.vision = LocalVisionProvider()

    def read(self, file_path: str) -> str:
        """
        Extract text content from any supported document or image.
        Preserves complete backwards-compatibility with existing code expecting str.
        """
        result = self.read_with_metadata(file_path)
        return result["text"]

    def read_with_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text content along with detailed provenance telemetry:
        - source_type: 'native_pdf', 'scanned_pdf', 'image', 'docx', 'pptx', 'txt'
        - processing: 'native_text_extraction', 'local_ocr', 'image_processing'
        - model_provider: 'local'
        - external_calls: 0
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = path.suffix.lower()
        file_size = path.stat().st_size

        logger.info("DocumentReader: Reading '%s' (%s, %d bytes)...", path.name, extension, file_size)

        if extension == ".pdf":
            extracted_text, source_type, processing, details = self._read_pdf(path)

        elif extension in IMAGE_EXTENSIONS:
            extracted_text, source_type, processing, details = self._read_image(path)

        elif extension == ".docx":
            extracted_text = self._read_docx(path)
            source_type = "docx"
            processing = "native_text_extraction"
            details = {}

        elif extension == ".txt":
            extracted_text = self._read_txt(path)
            source_type = "txt"
            processing = "native_text_extraction"
            details = {}

        elif extension == ".pptx":
            extracted_text = self._read_pptx(path)
            source_type = "pptx"
            processing = "native_text_extraction"
            details = {}

        elif extension == ".csv":
            extracted_text, details = self._read_csv(path)
            source_type = "spreadsheet"
            processing = "native_csv_extraction"

        else:
            raise ValueError(
                f"Unsupported file type: {extension}. Supported formats: {', '.join(ALL_SUPPORTED_EXTENSIONS)}"
            )

        # Standardized telemetry logging
        logger.info(
            "DocumentReader: Completed '%s' | source_type: %s | processing: %s | model_provider: local | external_calls: 0",
            path.name,
            source_type,
            processing,
        )

        # Record event in Sovereignty Monitor
        sovereignty_monitor.record_event(
            operation="OCR" if "ocr" in processing else "INGEST",
            component="DocumentReader",
            provider="Windows Media OCR" if "ocr" in processing else "Native Document Engine",
            model="local",
            local_or_external="LOCAL",
            external_calls=0,
            data_transfer_bytes=0,
            status="SUCCESS",
            details={
                "filename": path.name,
                "source_type": source_type,
                "processing": processing,
                "size_bytes": file_size,
            },
        )

        return {
            "text": extracted_text,
            "source_type": source_type,
            "processing": processing,
            "external_calls": 0,
            "model_provider": "local",
            "file_path": str(path),
            "filename": path.name,
            "extension": extension,
            "size_bytes": file_size,
            "char_count": len(extracted_text),
            "details": details,
            "confidentiality": sovereignty_monitor.get_confidentiality_metadata(),
        }

    # -----------------------------------------------------------------------
    # PDF (Native Text vs. Scanned Local OCR)
    # -----------------------------------------------------------------------
    def _read_pdf(self, path: Path) -> Tuple[str, str, str, Dict[str, Any]]:
        """
        Attempt native text extraction first. If text is missing or insufficient (< 50 chars),
        automatically route to local on-premise OCR.
        """
        try:
            reader = PdfReader(str(path))
            pages = []
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    pages.append(f"\n--- Page {page_number} ---\n{text.strip()}")

            native_content = "\n".join(pages).strip()
            num_pages = len(reader.pages)
        except Exception as exc:
            logger.warning("DocumentReader: Native pypdf read failed on '%s': %s", path.name, exc)
            native_content = ""
            num_pages = 0

        # Heuristic: if text length < 50 chars across all pages, treat as scanned PDF
        is_scanned = len(native_content.strip()) < 50

        if not is_scanned:
            logger.info("DocumentReader: Native text extracted from '%s' (%d pages)", path.name, num_pages)
            return (
                native_content,
                "native_pdf",
                "native_text_extraction",
                {"pages": num_pages, "mode": "native"},
            )

        # ── Route to Local OCR for Scanned PDF ─────────────────────────────
        logger.info(
            "DocumentReader: Insufficient native text (%d chars). Routing '%s' to local OCR...",
            len(native_content.strip()),
            path.name,
        )

        ocr_res = self.ocr.recognize_pdf_pages(path)
        ocr_text = ocr_res.get("text", "").strip()

        if ocr_text:
            return (
                ocr_text,
                "scanned_pdf",
                "local_ocr",
                {
                    "pages": ocr_res.get("page_count", num_pages),
                    "mode": "local_ocr",
                    "engine": ocr_res.get("engine", "windows_media_ocr"),
                },
            )
        else:
            # Graceful fallback: return whatever native snippet was found or advisory notice
            fallback_text = native_content or f"[Scanned Document: {path.name} - No readable text extracted via local OCR]"
            return (
                fallback_text,
                "scanned_pdf",
                "local_ocr",
                {"pages": num_pages, "mode": "local_ocr_empty"},
            )

    # -----------------------------------------------------------------------
    # Image Ingestion (OCR + Classifier + Drawing Parser + Modular Vision)
    # -----------------------------------------------------------------------
    def _read_image(self, path: Path) -> Tuple[str, str, str, Dict[str, Any]]:
        """
        Ingest inspection photograph, drawing, or handwritten document:
        1. Run local on-premise OCR for printed text / equipment markings.
        2. Run local vision inspection if vision model is installed.
        3. Deterministically classify image category (drawings, photos, nameplates, handwritten).
        4. Extract industrial drawing tags or format observations.
        """
        # 1. Local OCR
        ocr_res = self.ocr.recognize_image(path)
        ocr_text = ocr_res.get("text", "").strip()

        # 2. Local Vision Provider
        vision_notes = None
        if self.vision.is_vision_model_available():
            try:
                vision_notes = self.vision.describe_image(str(path))
            except Exception as exc:
                logger.warning("DocumentReader: Vision model description failed: %s", exc)

        img_meta = self.vision.extract_image_metadata(str(path))

        # 3. Local Deterministic Multimodal Classification
        classification = multimodal_classifier.classify_image(
            str(path), ocr_text=ocr_text, vision_notes=vision_notes
        )
        detected_category = classification.get("category", "general_image")

        # 4. Route based on classification
        if detected_category in ("engineering_drawing", "pid_or_process_diagram"):
            drawing_parsed = industrial_drawing_parser.parse_drawing(
                ocr_text=ocr_text,
                image_metadata=img_meta,
                vision_notes=vision_notes,
            )
            observation_text = industrial_drawing_parser.format_for_agent(drawing_parsed, path.name)
            source_type = detected_category
            processing = "local_ocr_and_drawing_parser"
            details = {
                "drawing_parsed": drawing_parsed,
                "equipment_tags": drawing_parsed.get("equipment_tags", []),
                "line_numbers": drawing_parsed.get("line_numbers", []),
                "classification": classification,
                "resolution": img_meta.get("resolution"),
                "confidence": drawing_parsed.get("confidence", 0.85),
                "vision_model_used": vision_notes is not None,
            }

        elif detected_category == "handwritten_note":
            source_type = "handwritten_note"
            processing = "local_ocr"
            # Extract detectable measurements, dates, equipment IDs
            import re
            dates_found = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", ocr_text)
            measurements = re.findall(r"\b\d+(?:\.\d+)?\s*(?:C|bar|psi|rpm|mm|m|kW|V|A|Hz)\b", ocr_text, re.IGNORECASE)
            eq_tags = re.findall(r"\b[A-Z]{1,3}-[0-9]{2,4}[A-Z]?\b", ocr_text)
            has_sig = any(w in ocr_text.lower() for w in ("signed", "signature", "initials", "operator", "engineer"))

            # Determine OCR Quality rating: GOOD / PARTIAL / LOW
            if len(ocr_text) > 80 and (dates_found or measurements or eq_tags):
                quality_indicator = "GOOD"
                hw_confidence = 0.78
            elif len(ocr_text) > 25:
                quality_indicator = "PARTIAL"
                hw_confidence = 0.65
            else:
                quality_indicator = "LOW"
                hw_confidence = 0.35

            hw_notice = (
                f"\n--- Handwritten Script Provenance ---\n"
                f"Source Type: handwritten_note | OCR Quality: {quality_indicator} | Confidence: {hw_confidence:.2f}\n"
                f"Extracted Dates: {', '.join(dates_found) if dates_found else 'None detected'}\n"
                f"Extracted Measurements: {', '.join(measurements) if measurements else 'None detected'}\n"
                f"Equipment IDs: {', '.join(eq_tags) if eq_tags else 'None detected'}\n"
                f"Signature/Presence: {'Detected' if has_sig else 'Not detected'}\n"
                f"Note: Manual verification recommended for critical statutory figures. Uncertainty preserved."
            )
            observation_text = (
                self.vision.format_inspection_observation(str(path), ocr_text, vision_notes)
                + hw_notice
            )
            details = {
                "classification": classification,
                "resolution": img_meta.get("resolution"),
                "confidence": hw_confidence,
                "quality_indicator": quality_indicator,
                "ocr_quality": quality_indicator,
                "dates_detected": dates_found,
                "measurements_detected": measurements,
                "equipment_tags": eq_tags,
                "signature_detected": has_sig,
                "vision_model_used": vision_notes is not None,
            }

        elif detected_category == "equipment_nameplate":
            source_type = "equipment_nameplate"
            processing = "local_ocr"
            observation_text = self.vision.format_inspection_observation(str(path), ocr_text, vision_notes)
            details = {
                "classification": classification,
                "resolution": img_meta.get("resolution"),
                "confidence": classification.get("confidence", 0.80),
                "vision_model_used": vision_notes is not None,
            }

        else:
            source_type = detected_category if detected_category in ("inspection_photo", "scanned_document") else "image"
            processing = "local_ocr_and_vision" if vision_notes else "local_ocr"
            observation_text = self.vision.format_inspection_observation(str(path), ocr_text, vision_notes)
            details = {
                "classification": classification,
                "ocr_line_count": ocr_res.get("line_count", 0),
                "resolution": img_meta.get("resolution"),
                "format": img_meta.get("format"),
                "confidence": classification.get("confidence", 0.85),
                "vision_model_used": vision_notes is not None,
            }

        return (observation_text, source_type, processing, details)

    # -----------------------------------------------------------------------
    # DOCX
    # -----------------------------------------------------------------------
    def _read_docx(self, path: Path) -> str:
        document = Document(str(path))
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    # -----------------------------------------------------------------------
    # TXT
    # -----------------------------------------------------------------------
    def _read_txt(self, path: Path) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            return file.read()

    # -----------------------------------------------------------------------
    # PPTX
    # -----------------------------------------------------------------------
    def _read_pptx(self, path: Path) -> str:
        presentation = Presentation(str(path))
        slides = []
        for slide_number, slide in enumerate(presentation.slides, start=1):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    txt = shape.text.strip()
                    if txt:
                        slide_text.append(txt)
            if slide_text:
                slides.append(f"\n--- Slide {slide_number} ---\n" + "\n".join(slide_text))
        return "\n".join(slides)

    # -----------------------------------------------------------------------
    # CSV / SPREADSHEET
    # -----------------------------------------------------------------------
    def _read_csv(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        import csv
        rows: List[List[str]] = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if any(cell.strip() for cell in row):
                    rows.append(row)

        header = rows[0] if rows else []
        row_count = len(rows)
        col_count = len(header)

        # Build clean markdown table preview
        lines = [f"=== INDUSTRIAL SPREADSHEET: {path.name} ({row_count} rows, {col_count} columns) ==="]
        if rows:
            lines.append(" | ".join(header))
            lines.append(" | ".join(["---"] * len(header)))
            for r in rows[1:101]:  # preview up to first 100 rows
                lines.append(" | ".join(r))
            if row_count > 101:
                lines.append(f"... [{row_count - 101} additional rows omitted for brevity] ...")

        return "\n".join(lines), {
            "row_count": row_count,
            "column_count": col_count,
            "headers": header[:20],
            "category": "spreadsheet",
        }