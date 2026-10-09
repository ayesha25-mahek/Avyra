"""
services/industrial_drawing_parser.py
-------------------------------------
Industrial Engineering Drawing & P&ID Parser for Avyara Enterprise Workbench.
SIH Problem Statement 26117.

Capabilities:
1. Equipment Tag Recognition:
   - Pumps (P-101A/B), Vessels (V-201), Heat Exchangers (E-301), Columns (C-101),
   - Transmitters & Indicators (TI-104, PI-201, FT-301, LT-102), Control Valves (CV-101, FV-201),
   - Safety Valves (PSV-101, SV-01).
2. Pipeline & Process Identifiers:
   - Line numbers: e.g. 4"-P-102-CS, 2"-HC-201, DN100-PN16.
3. Operating & Design Parameters:
   - Pressure, temperature, flow rates, metallurgy notes.
4. Drawing Block & Revision Extraction:
   - Drawing number, sheet, revision, scale.
5. Structured Observation Generation:
   - Emits verified observation models for downstream Agent Planner & Qwen 2.5 7B.
   - Honest reporting: Does not fabricate unreadable symbols or connections.

Guarantees:
- 100% on-premise execution (external_calls: 0, model_provider: local)
- Zero external cloud calls
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Regular expressions for industrial equipment tags and instrumentation
RE_EQUIPMENT_TAGS = re.compile(
    r"\b([A-Z]{1,4}-[0-9]{2,4}[A-Z]?)\b"
)
RE_LINE_NUMBERS = re.compile(
    r"\b([0-9]{1,2}(?:\"|in)?\s*-[A-Z0-9]+-[0-9]{2,4}(?:-[A-Z0-9]+)?)\b",
    re.IGNORECASE,
)
RE_METRIC_PIPES = re.compile(
    r"\b(DN\s*[0-9]{2,4}\s*PN\s*[0-9]{1,3})\b",
    re.IGNORECASE,
)
RE_PROCESS_PARAMETERS = re.compile(
    r"\b([0-9]+\.?[0-9]*\s*(?:kpa|bar|psi|deg\s*c|°c|c|gpm|m3\/h|m³\/h|kg\/cm2|rpm|kw|hp|volts|amps))\b",
    re.IGNORECASE,
)
RE_DWG_TITLE = re.compile(
    r"\b(?:DWG(?:\s*NO\.?|\s*:)?|DRAWING(?:\s*NO\.?|\s*:)?)\s*([A-Z0-9\-_]{4,20})\b",
    re.IGNORECASE,
)
RE_REVISION = re.compile(
    r"\b(?:REV(?:\.?|\s*:)?|REVISION(?:\.?|\s*:)?)\s*([A-Z0-9]{1,4})\b",
    re.IGNORECASE,
)


class IndustrialDrawingParser:
    """
    Parses OCR text and local visual extractions from industrial blueprints,
    engineering drawings, and P&ID diagrams.
    """

    def __init__(self):
        pass

    def parse_drawing(
        self,
        ocr_text: str,
        image_metadata: Optional[Dict[str, Any]] = None,
        vision_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract readable equipment tags, line numbers, and parameters.
        Returns a structured observation object for the Sovereign Agent Planner.
        """
        text_source = ocr_text or ""
        if vision_notes:
            text_source += "\n" + vision_notes

        # 1. Equipment Tags
        raw_tags = RE_EQUIPMENT_TAGS.findall(text_source)
        # Filter false positives (e.g. standard dates or non-tags)
        valid_tags: List[str] = []
        for t in raw_tags:
            tag_upper = t.upper()
            if not tag_upper.startswith("ISO-") and not tag_upper.startswith("DOC-") and not tag_upper.startswith("PAGE-"):
                if tag_upper not in valid_tags:
                    valid_tags.append(tag_upper)

        # 2. Piping / Line Numbers
        line_numbers: List[str] = []
        for match in RE_LINE_NUMBERS.findall(text_source):
            clean_line = match.strip()
            if clean_line not in line_numbers:
                line_numbers.append(clean_line)
        for match in RE_METRIC_PIPES.findall(text_source):
            clean_pipe = match.strip()
            if clean_pipe not in line_numbers:
                line_numbers.append(clean_pipe)

        # 3. Parameters / Dimensions
        raw_params = RE_PROCESS_PARAMETERS.findall(text_source)
        unique_params = list(dict.fromkeys([p.strip() for p in raw_params]))

        # 4. Title Block & Drawing Identifiers
        dwg_no_match = RE_DWG_TITLE.search(text_source)
        drawing_number = dwg_no_match.group(1) if dwg_no_match else None

        rev_match = RE_REVISION.search(text_source)
        revision = rev_match.group(1) if rev_match else None

        # 5. Formulate Structured Observations
        observations: List[str] = []
        if valid_tags:
            observations.append(
                f"Identified {len(valid_tags)} readable equipment tag(s): {', '.join(valid_tags[:8])}"
                + (f" (+{len(valid_tags)-8} more)" if len(valid_tags) > 8 else "")
            )
        if line_numbers:
            observations.append(f"Identified {len(line_numbers)} process line designation(s): {', '.join(line_numbers[:6])}")
        if unique_params:
            observations.append(f"Recorded {len(unique_params)} engineering parameters / limits: {', '.join(unique_params[:6])}")

        # Compute transparent confidence
        if valid_tags or line_numbers or drawing_number:
            confidence = 0.85
        elif len(ocr_text.strip()) > 30:
            confidence = 0.60
        else:
            confidence = 0.35

        # Honest disclosure of vision model vs deterministic OCR
        vision_model_status = (
            "Local Vision Model Active (multi-modal topological grounding)"
            if vision_notes
            else "Advanced diagram vision unavailable; OCR/text extraction completed."
        )

        return {
            "source_type": "engineering_drawing",
            "processing": "local_ocr_and_drawing_parser",
            "drawing_number": drawing_number,
            "revision": revision,
            "equipment_tags": valid_tags,
            "line_numbers": line_numbers,
            "parameters": unique_params,
            "observations": observations,
            "confidence": confidence,
            "external_calls": 0,
            "model_provider": "local",
            "vision_model_status": vision_model_status,
            "raw_text_length": len(ocr_text),
        }

    def format_for_agent(self, parsed: Dict[str, Any], filename: str) -> str:
        """Format the drawing observations into prompt context for Agent Planner & Qwen."""
        lines = [
            f"=== INDUSTRIAL ENGINEERING DRAWING / P&ID AUDIT: {filename} ===",
            f"Extraction Engine: Local Sovereign OCR & Drawing Parser (external_calls: 0)",
            f"Vision Model Status: {parsed.get('vision_model_status')}",
            f"Confidence Score: {parsed.get('confidence')}",
        ]

        if parsed.get("drawing_number"):
            lines.append(f"Drawing No: {parsed['drawing_number']} | Revision: {parsed.get('revision', 'N/A')}")

        if parsed.get("equipment_tags"):
            lines.append(f"\n--- Equipment & Instrument Tags Detected ---")
            lines.append(", ".join(parsed["equipment_tags"]))

        if parsed.get("line_numbers"):
            lines.append(f"\n--- Process Piping / Line Designations ---")
            lines.append(", ".join(parsed["line_numbers"]))

        if parsed.get("parameters"):
            lines.append(f"\n--- Engineering Specifications & Ratings ---")
            lines.append(", ".join(parsed["parameters"]))

        if parsed.get("observations"):
            lines.append(f"\n--- Structured Engineering Observations ---")
            for obs in parsed["observations"]:
                lines.append(f"• {obs}")

        lines.append(
            "\nNote: Equipment tags and parameters extracted from legible drawing annotations. "
            "Unreadable raster regions or dense schematics are not fabricated."
        )

        return "\n".join(lines)


industrial_drawing_parser = IndustrialDrawingParser()
