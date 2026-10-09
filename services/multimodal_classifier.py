"""
services/multimodal_classifier.py
---------------------------------
Local Deterministic Document & Image Classifier for Avyara Confidential Workbench.
SIH Problem Statement 26117.

Categorizes uploaded visual documents into industrial classes:
1. scanned_document       — multi-line typed text, uniform layout, page margins
2. handwritten_note       — irregular line heights, handwriting markers, cursive token artifacts
3. inspection_photo       — high color variance, EXIF camera metadata, defect/corrosion visual indicators
4. engineering_drawing    — high aspect ratio, title blocks, dimensioning, low color variance / line drawing
5. pid_or_process_diagram — process flow keywords, equipment tags (P-101, V-201), instrument loops
6. equipment_nameplate    — rating plates, electrical/pressure specifications (kW, RPM, Bar, Serial, Model)
7. general_image          — uncategorized visual media

Guarantees:
- 100% on-premise execution (external_calls: 0, model_provider: local)
- Zero external cloud vision API requirements
- Deterministic heuristic fallback with transparent confidence metrics
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)

# Industrial Regex Patterns for Document Classification
PID_TAG_PATTERN = re.compile(
    r"\b(?:[A-Z]{1,4}-[0-9]{2,4}[A-Z]?|[0-9]{1,2}\"[A-Z0-9\-]+|DN\s*[0-9]{2,4}|PN\s*[0-9]{1,3})\b"
)
NAMEPLATE_KEYWORDS = {
    "serial", "model", "volts", "voltage", "amps", "amperage", "kw", "hp", "rpm",
    "hz", "phase", "mwp", "bar", "psi", "rating", "manufacturer", "mfg", "tag no",
    "operating pressure", "design pressure", "temp rating", "capacity", "enclosure",
}
PID_KEYWORDS = {
    "p&id", "pid", "piping", "instrumentation", "flow", "schematic", "pump", "valve",
    "flange", "compressor", "heat exchanger", "line no", "stream", "nozzle",
    "transmitter", "interlock", "vent", "drain", "suction", "discharge", "bypass",
}
DRAWING_KEYWORDS = {
    "drawing", "dwg", "scale", "rev", "revision", "title block", "elevation",
    "plan view", "section a-a", "general arrangement", "dimensions", "tolerance",
    "isometric", "fabrication", "structural", "blueprint", "sheet",
}
HANDWRITING_KEYWORDS = {
    "note", "memo", "log", "handwritten", "shift log", "remarks", "signed",
    "signature", "field note", "operator note", "initials", "dated",
}
INSPECTION_PHOTO_KEYWORDS = {
    "corrosion", "crack", "leak", "leakage", "flange", "pitting", "weld", "rust",
    "spall", "erosion", "coating failure", "defect", "inspection", "damage",
    "blistering", "deformation", "transformer", "insulator", "bearing",
}
SPREADSHEET_KEYWORDS = {
    "total", "sum", "average", "qty", "quantity", "unit", "price", "cost", "budget",
    "variance", "column", "row", "balance", "debit", "credit", "subtotal", "table",
}
TECHNICAL_DOC_KEYWORDS = {
    "specification", "procedure", "standard", "manual", "protocol", "compliance",
    "guideline", "section", "clause", "scope", "requisition", "datasheet",
}


class MultimodalClassifier:
    """
    Deterministic on-premise visual and document classifier.
    Combines raster image geometry, color depth, EXIF data, and OCR token heuristics.
    """

    def __init__(self):
        pass

    def classify_image(
        self,
        image_path: str,
        ocr_text: str = "",
        vision_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Classify image into industrial categories without external cloud calls.
        Returns category, confidence score, detected features, and sovereign telemetry.
        """
        p = Path(image_path)
        if not p.exists():
            return {
                "category": "general_image",
                "confidence": 0.0,
                "features": ["file_not_found"],
                "external_calls": 0,
                "model_provider": "local",
            }

        # 1. Analyze Image Geometry & Color Attributes
        geometry_info = self._analyze_geometry(p)

        # 2. Analyze Text Token Clues
        text_lower = (ocr_text or "").lower()
        if vision_notes:
            text_lower += " " + vision_notes.lower()

        scores: Dict[str, float] = {
            "scanned_document": 0.1,
            "handwritten_note": 0.05,
            "inspection_photo": 0.2 if geometry_info.get("is_photo") else 0.05,
            "engineering_drawing": 0.2 if geometry_info.get("is_schematic") else 0.05,
            "pid_or_process_diagram": 0.1 if geometry_info.get("is_schematic") else 0.05,
            "equipment_nameplate": 0.1,
            "technical_document": 0.1,
            "spreadsheet": 0.05,
            "general_image": 0.1,
        }
        detected_features: List[str] = []

        # Geometry-based feature contributions
        if geometry_info.get("aspect_ratio", 1.0) >= 1.35 and geometry_info.get("is_schematic"):
            scores["engineering_drawing"] += 0.35
            scores["pid_or_process_diagram"] += 0.25
            detected_features.append("wide_schematic_aspect_ratio")

        if geometry_info.get("has_camera_exif"):
            scores["inspection_photo"] += 0.45
            detected_features.append("camera_exif_metadata_present")

        if geometry_info.get("is_high_color_depth") and not geometry_info.get("is_schematic"):
            scores["inspection_photo"] += 0.25
            detected_features.append("photographic_color_depth")

        # P&ID and Equipment Tag Regex
        pid_tags = PID_TAG_PATTERN.findall(ocr_text)
        if len(pid_tags) >= 2:
            scores["pid_or_process_diagram"] += 0.55
            scores["engineering_drawing"] += 0.35
            detected_features.append(f"detected_{len(pid_tags)}_industrial_equipment_tags")

        # P&ID Keywords
        pid_kw_matches = [w for w in PID_KEYWORDS if w in text_lower]
        if len(pid_kw_matches) >= 2:
            scores["pid_or_process_diagram"] += 0.40
            detected_features.append(f"pid_keywords_found({','.join(pid_kw_matches[:3])})")

        # Engineering Drawing Keywords
        dwg_kw_matches = [w for w in DRAWING_KEYWORDS if w in text_lower]
        if len(dwg_kw_matches) >= 2:
            scores["engineering_drawing"] += 0.45
            detected_features.append(f"drawing_keywords_found({','.join(dwg_kw_matches[:3])})")

        # Equipment Nameplate Keywords
        nameplate_matches = [w for w in NAMEPLATE_KEYWORDS if w in text_lower]
        if len(nameplate_matches) >= 3:
            scores["equipment_nameplate"] += 0.60
            detected_features.append(f"nameplate_specs_found({','.join(nameplate_matches[:3])})")

        # Inspection Photo Keywords
        photo_matches = [w for w in INSPECTION_PHOTO_KEYWORDS if w in text_lower]
        if len(photo_matches) >= 2:
            scores["inspection_photo"] += 0.40
            detected_features.append(f"inspection_defect_terms({','.join(photo_matches[:3])})")

        if any(w in p.name.lower() for w in ("photo", "defect", "flange_photo", "crack", "corrosion")):
            scores["inspection_photo"] += 0.45
            detected_features.append("inspection_photo_filename_cue")

        if "inspection photo" in text_lower or "photograph" in text_lower or "visual finding" in text_lower:
            scores["inspection_photo"] += 0.40
            detected_features.append("inspection_photo_phrase_found")

        # Technical Document Keywords
        tech_matches = [w for w in TECHNICAL_DOC_KEYWORDS if w in text_lower]
        if len(tech_matches) >= 2:
            scores["technical_document"] += 0.40
            detected_features.append(f"technical_doc_terms({','.join(tech_matches[:3])})")

        # Spreadsheet Keywords or Tabular Data Clues
        sheet_matches = [w for w in SPREADSHEET_KEYWORDS if w in text_lower]
        has_csv_or_tsv = any(delim in ocr_text for delim in (",", "\t", "|")) and len(ocr_text.splitlines()) > 3
        if len(sheet_matches) >= 2 or has_csv_or_tsv:
            scores["spreadsheet"] += 0.35
            detected_features.append("tabular_or_spreadsheet_structure")

        # Handwritten Note Clues
        handwriting_matches = [w for w in HANDWRITING_KEYWORDS if w in text_lower]
        words = ocr_text.split()
        short_fragment_ratio = (
            sum(1 for w in words if len(w) <= 2) / max(len(words), 1)
            if words else 0.0
        )
        if handwriting_matches or (short_fragment_ratio > 0.45 and len(words) >= 5):
            # If handwriting or informal note signatures are found, boost handwritten_note
            scores["handwritten_note"] += 0.55
            detected_features.append(f"handwriting_or_informal_note_signatures({','.join(handwriting_matches[:2])})")

        # Scanned Document Clues
        if len(words) > 50 and geometry_info.get("aspect_ratio", 1.0) < 1.0:
            scores["scanned_document"] += 0.50
            detected_features.append("dense_portrait_text_page")

        # Determine Winning Category
        best_category = max(scores, key=scores.get)
        raw_confidence = min(round(scores[best_category], 2), 0.98)
        confidence = max(raw_confidence, 0.50)

        # Disclose if advanced vision model was utilized
        vision_model_status = (
            "Local Vision Model Active"
            if vision_notes
            else "Local Deterministic Feature Analysis (No cloud vision required)"
        )

        return {
            "category": best_category,
            "confidence": confidence,
            "features_detected": detected_features,
            "geometry": geometry_info,
            "external_calls": 0,
            "model_provider": "local",
            "vision_model_status": vision_model_status,
        }

    def _analyze_geometry(self, path: Path) -> Dict[str, Any]:
        """Examine raster properties using PIL without cloud APIs."""
        try:
            with Image.open(path) as img:
                w, h = img.size
                aspect_ratio = round(w / max(h, 1), 2)
                mode = img.mode

                has_exif = False
                try:
                    raw_exif = img.getexif()
                    has_exif = bool(raw_exif and len(raw_exif) > 0)
                except Exception:
                    pass

                # Check color variance (schematics are often near grayscale or few colors)
                is_schematic = False
                if mode in ("1", "L", "P"):
                    is_schematic = True
                elif mode == "RGB":
                    # Sample colors - schematics typically have high dominant background and limited palettes
                    colors = img.getcolors(maxcolors=1024)
                    if colors is not None and len(colors) < 512:
                        is_schematic = True

                is_photo = (mode == "RGB" and not is_schematic) or has_exif

                return {
                    "width": w,
                    "height": h,
                    "aspect_ratio": aspect_ratio,
                    "mode": mode,
                    "has_camera_exif": has_exif,
                    "is_schematic": is_schematic,
                    "is_photo": is_photo,
                    "is_high_color_depth": mode in ("RGB", "RGBA"),
                }
        except Exception as exc:
            logger.debug("MultimodalClassifier: Could not read image geometry: %s", exc)
            return {"aspect_ratio": 1.0, "is_photo": True, "has_camera_exif": False}


multimodal_classifier = MultimodalClassifier()
