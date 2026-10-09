"""
services/docx_generator.py
--------------------------
Sovereign DOCX Deliverable Generator for Avyara Enterprise AI Workbench.

Reuses and extends python-docx to transform LLM-synthesized inspection dossiers,
risk analyses, and approval notes into beautifully formatted, publication-grade
Word (.docx) deliverables.

Workflow:
Inspection Report
    ↓
Analysis (Findings & Risks)
    ↓
Recommendation (Mitigation roadmap)
    ↓
Approval Note (Regulatory & Sign-off criteria)
    ↓
.docx (Executive Word Document Deliverable)
"""

import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

logger = logging.getLogger(__name__)


def _set_cell_background(cell, hex_color: str) -> None:
    """Set background color of a docx table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150) -> None:
    """Set inner cell padding in twips (1/20 of a pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for margin_name, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{margin_name}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


class DocxGenerator:
    """
    Enterprise-grade DOCX document generator for technical inspection reports,
    risk dossiers, and sovereign executive approval notes.
    """

    def __init__(self, output_dir: str = "output/documents"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Palette
        self.COLOR_PRIMARY = RGBColor(16, 31, 23)        # Forest Navy
        self.COLOR_ACCENT = RGBColor(36, 99, 70)          # Avyara Green
        self.COLOR_MUTED = RGBColor(86, 112, 98)          # Slate Green
        self.COLOR_TEXT = RGBColor(30, 41, 59)            # Deep Slate Body
        self.COLOR_CRITICAL = RGBColor(185, 28, 28)       # Red-700
        self.COLOR_APPROVED = RGBColor(22, 101, 52)       # Green-800

    def generate_inspection_approval_docx(
        self,
        title: str,
        content_markdown: str,
        metadata: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convert structured markdown inspection dossier into an executive .docx file.
        Returns metadata dict with file path, filename, and download URL.
        """
        doc = Document()

        # ── Page Setup ────────────────────────────────────────────────────────
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

            # Header & Footer
            header_p = section.header.paragraphs[0]
            header_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            h_run = header_p.add_run("AVYARA SOVEREIGN WORKBENCH | OFFICIAL INSPECTION DOSSIER")
            h_run.font.name = "Calibri"
            h_run.font.size = Pt(8.5)
            h_run.font.color.rgb = self.COLOR_MUTED

            footer_p = section.footer.paragraphs[0]
            footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            f_run = footer_p.add_run("SOVEREIGN GOVERNANCE & RISK AUDIT — ON-PREMISE VERIFIED — CONFIDENTIAL")
            f_run.font.name = "Calibri"
            f_run.font.size = Pt(8.5)
            f_run.font.color.rgb = self.COLOR_MUTED

        # ── Document Title Banner ─────────────────────────────────────────────
        title_p = doc.add_paragraph()
        title_p.paragraph_format.space_before = Pt(0)
        title_p.paragraph_format.space_after = Pt(4)
        run_title = title_p.add_run(title.upper())
        run_title.font.name = "Calibri"
        run_title.font.size = Pt(20)
        run_title.font.bold = True
        run_title.font.color.rgb = self.COLOR_PRIMARY

        subtitle_p = doc.add_paragraph()
        subtitle_p.paragraph_format.space_after = Pt(14)
        run_sub = subtitle_p.add_run("Formal Technical Inspection Findings, Risk Analysis & Compliance Approval Note")
        run_sub.font.name = "Calibri"
        run_sub.font.size = Pt(11)
        run_sub.font.italic = True
        run_sub.font.color.rgb = self.COLOR_ACCENT

        # ── Metadata Summary Grid ─────────────────────────────────────────────
        meta_table = doc.add_table(rows=2, cols=2)
        meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        meta_table.autofit = False

        meta_info = metadata or {}
        date_str = meta_info.get("date", datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC"))
        provider_str = meta_info.get("provider", "Local Ollama (Qwen 2.5 7B)")
        doc_ref = meta_info.get("doc_ref", f"SIH-INSP-{uuid.uuid4().hex[:6].upper()}")
        status_str = meta_info.get("status", "Sovereign Audit Verified")

        cells_data = [
            ("Audit Reference ID:", doc_ref, "Date & Timestamp:", date_str),
            ("Autonomous AI Engine:", provider_str, "Governance Classification:", status_str),
        ]

        for row_idx, (k1, v1, k2, v2) in enumerate(cells_data):
            row = meta_table.rows[row_idx]

            # Left Cell
            c1 = row.cells[0]
            _set_cell_background(c1, "F0F5F2")
            _set_cell_margins(c1, top=80, bottom=80, left=120, right=120)
            p1 = c1.paragraphs[0]
            p1.paragraph_format.space_after = Pt(0)
            r1_k = p1.add_run(f"{k1} ")
            r1_k.font.bold = True
            r1_k.font.size = Pt(9)
            r1_k.font.color.rgb = self.COLOR_PRIMARY
            r1_v = p1.add_run(v1)
            r1_v.font.size = Pt(9)
            r1_v.font.color.rgb = self.COLOR_TEXT

            # Right Cell
            c2 = row.cells[1]
            _set_cell_background(c2, "F0F5F2")
            _set_cell_margins(c2, top=80, bottom=80, left=120, right=120)
            p2 = c2.paragraphs[0]
            p2.paragraph_format.space_after = Pt(0)
            r2_k = p2.add_run(f"{k2} ")
            r2_k.font.bold = True
            r2_k.font.size = Pt(9)
            r2_k.font.color.rgb = self.COLOR_PRIMARY
            r2_v = p2.add_run(v2)
            r2_v.font.size = Pt(9)
            r2_v.font.color.rgb = self.COLOR_TEXT

        p_spacer = doc.add_paragraph()
        p_spacer.paragraph_format.space_after = Pt(12)

        # ── Body Content Rendering ────────────────────────────────────────────
        lines = content_markdown.splitlines()
        in_code_block = False

        for line in lines:
            trimmed = line.strip()

            if not trimmed:
                continue

            if trimmed.startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                p_code = doc.add_paragraph()
                p_code.paragraph_format.left_indent = Inches(0.4)
                p_code.paragraph_format.space_after = Pt(2)
                r_c = p_code.add_run(trimmed)
                r_c.font.name = "Consolas"
                r_c.font.size = Pt(9)
                r_c.font.color.rgb = self.COLOR_MUTED
                continue

            # Heading 1 (# ...)
            if trimmed.startswith("# "):
                h_text = trimmed[2:].strip()
                p_h1 = doc.add_paragraph()
                p_h1.paragraph_format.space_before = Pt(16)
                p_h1.paragraph_format.space_after = Pt(6)
                p_h1.paragraph_format.keep_with_next = True
                r = p_h1.add_run(h_text)
                r.font.name = "Calibri"
                r.font.size = Pt(15)
                r.font.bold = True
                r.font.color.rgb = self.COLOR_PRIMARY
                continue

            # Heading 2 (## ...)
            if trimmed.startswith("## "):
                h_text = trimmed[3:].strip()
                p_h2 = doc.add_paragraph()
                p_h2.paragraph_format.space_before = Pt(14)
                p_h2.paragraph_format.space_after = Pt(4)
                p_h2.paragraph_format.keep_with_next = True
                r = p_h2.add_run(h_text)
                r.font.name = "Calibri"
                r.font.size = Pt(12.5)
                r.font.bold = True
                r.font.color.rgb = self.COLOR_ACCENT
                continue

            # Heading 3 (### ...)
            if trimmed.startswith("### "):
                h_text = trimmed[4:].strip()
                p_h3 = doc.add_paragraph()
                p_h3.paragraph_format.space_before = Pt(10)
                p_h3.paragraph_format.space_after = Pt(2)
                p_h3.paragraph_format.keep_with_next = True
                r = p_h3.add_run(h_text)
                r.font.name = "Calibri"
                r.font.size = Pt(11)
                r.font.bold = True
                r.font.color.rgb = self.COLOR_PRIMARY
                continue

            # Sign-off Determination Callout Box
            if "Determination:" in trimmed or "Current Status:" in trimmed or "Current Determination:" in trimmed:
                callout_tbl = doc.add_table(rows=1, cols=1)
                callout_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = callout_tbl.rows[0].cells[0]
                _set_cell_background(cell, "EAF2EE")
                _set_cell_margins(cell, top=120, bottom=120, left=160, right=160)
                p_callout = cell.paragraphs[0]
                p_callout.paragraph_format.space_after = Pt(0)
                r_sign = p_callout.add_run("OFFICIAL SIGN-OFF STATUS: ")
                r_sign.font.bold = True
                r_sign.font.size = Pt(10.5)
                r_sign.font.color.rgb = self.COLOR_PRIMARY
                r_val = p_callout.add_run(trimmed)
                r_val.font.bold = True
                r_val.font.size = Pt(10.5)
                r_val.font.color.rgb = self.COLOR_APPROVED if "APPROVED" in trimmed and "CONDITIONAL" not in trimmed else self.COLOR_ACCENT
                continue

            # Bullet List Items (- or *)
            if trimmed.startswith("- ") or trimmed.startswith("* "):
                bullet_text = trimmed[2:].strip()
                p_bullet = doc.add_paragraph(style="List Bullet")
                p_bullet.paragraph_format.space_after = Pt(3)
                p_bullet.paragraph_format.line_spacing = 1.15
                self._format_inline_markdown(p_bullet, bullet_text)
                continue

            # Numbered List Items (1. , 2. )
            num_match = re.match(r"^(\d+)\.\s+(.*)$", trimmed)
            if num_match:
                item_text = num_match.group(2)
                p_num = doc.add_paragraph(style="List Number")
                p_num.paragraph_format.space_after = Pt(3)
                p_num.paragraph_format.line_spacing = 1.15
                self._format_inline_markdown(p_num, item_text)
                continue

            # Standard Paragraph
            p_body = doc.add_paragraph()
            p_body.paragraph_format.space_after = Pt(5)
            p_body.paragraph_format.line_spacing = 1.15
            self._format_inline_markdown(p_body, trimmed)

        # ── Save File ─────────────────────────────────────────────────────────
        if not filename:
            clean_title = re.sub(r"[^a-zA-Z0-9_\-]+", "_", title.lower())[:30]
            unique_id = uuid.uuid4().hex[:8]
            filename = f"inspection_approval_{clean_title}_{unique_id}.docx"

        file_path = self.output_dir / filename
        doc.save(str(file_path))
        logger.info("DocxGenerator: Saved inspection approval note to %s", file_path)

        return {
            "type": "file",
            "path": str(file_path),
            "filename": filename,
            "content": content_markdown,
            "size_bytes": file_path.stat().st_size,
        }

    def _format_inline_markdown(self, paragraph, text: str) -> None:
        """Parse bold (**text**) and inline code (`code`) within paragraph text."""
        # Split by bold markers
        tokens = re.split(r"(\*\*.*?\*\*)", text)
        for token in tokens:
            if not token:
                continue
            if token.startswith("**") and token.endswith("**"):
                inner = token[2:-2]
                r = paragraph.add_run(inner)
                r.font.name = "Calibri"
                r.font.size = Pt(10)
                r.font.bold = True
                r.font.color.rgb = self.COLOR_PRIMARY
            else:
                # Check for inline code
                code_parts = re.split(r"(`.*?`)", token)
                for part in code_parts:
                    if part.startswith("`") and part.endswith("`"):
                        r_code = paragraph.add_run(part[1:-1])
                        r_code.font.name = "Consolas"
                        r_code.font.size = Pt(9)
                        r_code.font.color.rgb = self.COLOR_MUTED
                    else:
                        r_plain = paragraph.add_run(part)
                        r_plain.font.name = "Calibri"
                        r_plain.font.size = Pt(10)
                        r_plain.font.color.rgb = self.COLOR_TEXT
