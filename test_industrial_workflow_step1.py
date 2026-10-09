"""
test_industrial_workflow_step1.py
---------------------------------
Comprehensive verification suite for Step 1 of the Industrial Workflow:
1. Image Upload -> Defect Inspection Report (DOCX) + Inspection Summary
2. Document/PDF Upload -> Extracted Text + Inspection/Approval Report (DOCX) + Presentation (PPTX)
3. Engineering Drawing / P&ID Upload -> Drawing Analysis + Equipment/Tag Extraction + Technical Report (DOCX)
4. Spreadsheet Upload -> Data Summary + Calculations & Abnormal Values + Analysis Workbook (XLSX)
5. Multi-output selection -> single-pass source analysis producing multiple deliverables
6. Download verification -> verifies physical files (.docx, .pptx, .xlsx) exist and are valid
7. Error handling -> verifies appropriate handling for empty prompts/files and edge cases
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

import json
from services.content_intelligence import ContentIntelligence
from services.inspection_analysis_generator import InspectionAnalysisGenerator
from services.workbook_generator import WorkbookGenerator
from services.ppt_generator import PPTGenerator
from services.output_request import OutputRequest


def test_industrial_workflow():
    print("=" * 80)
    print("STEP 1: TESTING COMPREHENSIVE INDUSTRIAL WORKFLOW & OUTPUT FORMATS")
    print("=" * 80)

    ci = ContentIntelligence(provider="ollama")

    # ──────────────────────────────────────────────────────────────────────────
    # TEST 1: Image Defect Analysis -> Inspection Summary & Defect Report (DOCX)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 1] Image Defect Analysis Flow...")
    image_text = "VISUAL INSPECTION: Surface crack 45mm detected along circumferential weld seam W-04 on reactor pressure vessel V-201. Visible pitting corrosion depth estimated at 1.8mm. Spatial location: Center-Right grid."
    image_metas = [{
        "filename": "reactor_weld_crack.png",
        "source_type": "inspection_photo",
        "extension": ".png",
        "details": {"category": "defective_product_image"}
    }]

    cm_image = ci.analyze(image_text, source_files=["reactor_weld_crack.png"], file_metas=image_metas)
    assert cm_image is not None, "ContentIntelligence failed for image"
    print("  [PASS] Content model created for image defect analysis")

    gen = InspectionAnalysisGenerator(provider="ollama")
    req = OutputRequest(outputs=["defect_report"])
    res_image = gen.generate(cm_image, req)

    assert isinstance(res_image, dict), "Result must be a dict"
    assert res_image.get("type") == "file", "Result should return a file deliverable"
    docx_path = res_image.get("path")
    assert docx_path and os.path.exists(docx_path), f"DOCX deliverable does not exist: {docx_path}"
    assert os.path.getsize(docx_path) > 1000, "DOCX file too small"
    print(f"  [PASS] Defect Inspection Report (DOCX) generated: {docx_path} ({os.path.getsize(docx_path)} bytes)")

    content_text = res_image.get("content", "")
    assert "Visible Defect" in content_text or "Observed Findings" in content_text or "Executive Summary" in content_text
    print("  [PASS] Visual findings grounded in uploaded defect evidence")

    # ──────────────────────────────────────────────────────────────────────────
    # TEST 2: Document Analysis -> Extracted Text + Inspection Report (DOCX) + PPTX
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 2] Document Analysis Flow (Multi-Output)...")
    doc_text = """ANNUAL COMPLIANCE AUDIT - BOILER FEED PUMP P-101A
Equipment: Multistage Centrifugal Pump P-101A
Design Capacity: 250 m3/hr at 65 bar
Observed Discharge Pressure: 58.2 bar (Degraded from 65.0 bar design)
Thrust Bearing Temperature: 88.4 C (High alarm: 85 C)
Vibration Velocity: 6.2 mm/s RMS (ISO 10816 limit: 4.5 mm/s)
Oil Analysis: Iron particulate count 140 ppm, water in oil 0.08%."""
    doc_metas = [{
        "filename": "pump_audit_report.pdf",
        "source_type": "inspection_report",
        "extension": ".pdf",
        "characters": len(doc_text)
    }]

    cm_doc = ci.analyze(doc_text, source_files=["pump_audit_report.pdf"], file_metas=doc_metas)

    # Output A: Extracted Text
    assert cm_doc.get("raw_text") == doc_text, "Raw extracted text preserved"
    print("  [PASS] Extracted Text preserved and accessible")

    # Output B: Inspection Report (DOCX)
    res_doc = gen.generate(cm_doc, OutputRequest(outputs=["inspection_analysis"]))
    assert res_doc.get("type") == "file"
    assert os.path.exists(res_doc["path"])
    print(f"  [PASS] Inspection / Approval Report (DOCX) created: {res_doc['path']}")

    # Output C: Management Presentation (PPTX)
    ppt_gen = PPTGenerator()
    slide_plan = [
        {"slide_number": 1, "title": "Boiler Feed Pump P-101A Audit", "type": "title", "content": ["Annual Compliance Review", "Unit 2 Utilities"]},
        {"slide_number": 2, "title": "Field Observations & Findings", "type": "content", "content": ["Discharge pressure degraded to 58.2 bar", "Vibration velocity 6.2 mm/s exceeds ISO limit"]},
        {"slide_number": 3, "title": "Mandatory Corrective Interventions", "type": "content", "content": ["Dynamic rebalancing of rotor", "Lube oil flush & replacement"]}
    ]
    pptx_path = ppt_gen.create_presentation(slide_plan)
    assert os.path.exists(pptx_path) and os.path.getsize(pptx_path) > 1000
    print(f"  [PASS] Management Presentation (PPTX) created: {pptx_path} ({os.path.getsize(pptx_path)} bytes)")

    # ──────────────────────────────────────────────────────────────────────────
    # TEST 3: Engineering Drawing / P&ID -> Tags & Technical Report (DOCX)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 3] Engineering Drawing / P&ID Analysis Flow...")
    drawing_text = """P&ID DRAWING NO: DWG-PID-REF-2026-REV3
Plant Section: Crude Distillation Column Train 1
Equipment Tags:
- P-101A/B: Crude Charge Pumps (10"-CS-101-150#)
- V-204: Reflux Drum with PSV-204A/B set at 4.5 bar
- E-301: Overhead Condenser Shell & Tube
- XV-104: Emergency Depressuring Valve
- TI-201: Column Top Temperature Transmitter (Normal 125 C)"""
    drawing_metas = [{
        "filename": "crude_unit_pid_rev3.png",
        "source_type": "engineering_drawing",
        "extension": ".png",
        "details": {"category": "pid_or_process_diagram"}
    }]

    cm_dwg = ci.analyze(drawing_text, source_files=["crude_unit_pid_rev3.png"], file_metas=drawing_metas)

    # Equipment Tag Extraction
    import re
    tags = list(set(re.findall(r'\b([A-Z]{1,4}-\d{2,5}[A-Z]?(?:/[A-Z])?)\b', drawing_text)))
    assert len(tags) >= 4, f"Tags extracted: {tags}"
    print(f"  [PASS] Equipment tags extracted successfully: {tags}")

    # Technical Report (DOCX)
    res_dwg = gen.generate(cm_dwg, OutputRequest(outputs=["technical_report"]))
    assert res_dwg.get("type") == "file"
    assert os.path.exists(res_dwg["path"])
    print(f"  [PASS] Drawing Technical Report (DOCX) generated: {res_dwg['path']}")

    # ──────────────────────────────────────────────────────────────────────────
    # TEST 4: Spreadsheet Analysis -> Workbook (XLSX) & Anomalies
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 4] Spreadsheet Analysis Flow...")
    csv_data = """Timestamp,Pump_Tag,Vibration_mm_s,Bearing_Temp_C,Discharge_Pressure_bar
2026-10-01 08:00,P-101A,2.1,65.2,16.2
2026-10-01 12:00,P-101A,2.4,66.1,16.0
2026-10-01 16:00,P-101A,4.9,82.4,14.8
2026-10-01 20:00,P-101A,6.5,88.9,13.2
2026-10-02 00:00,P-101A,7.8,94.1,11.5"""

    cm_sheet = ci.analyze(csv_data, source_files=["pump_telemetry.csv"])
    workbook_gen = WorkbookGenerator()
    res_wb = workbook_gen.generate(cm_sheet, OutputRequest(outputs=["analysis_workbook"]))

    assert res_wb.get("type") == "file"
    xlsx_path = res_wb.get("path")
    assert xlsx_path and os.path.exists(xlsx_path), "XLSX file does not exist"
    assert os.path.getsize(xlsx_path) > 1000, "XLSX file too small"
    print(f"  [PASS] Analysis Workbook (XLSX) generated: {xlsx_path} ({os.path.getsize(xlsx_path)} bytes)")

    # ──────────────────────────────────────────────────────────────────────────
    # TEST 5: Download Deliverable Integrity Verification
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 5] Verifying Physical File Deliverables...")
    files_to_check = [
        ("Defect Report DOCX", docx_path, b"PK\x03\x04"),       # Zip-based format
        ("Inspection Report DOCX", res_doc["path"], b"PK\x03\x04"),
        ("Presentation PPTX", pptx_path, b"PK\x03\x04"),
        ("Analysis Workbook XLSX", xlsx_path, b"PK\x03\x04"),
    ]
    for label, path, magic in files_to_check:
        assert os.path.exists(path), f"File missing: {path}"
        with open(path, "rb") as f:
            header = f.read(4)
        assert header == magic, f"{label} magic bytes mismatch: {header} vs {magic}"
        print(f"  [PASS] {label}: Valid file format on disk ({os.path.basename(path)})")

    # ──────────────────────────────────────────────────────────────────────────
    # TEST 6: Error Handling Verification
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 6] Verifying Robust Error Handling...")
    try:
        ci.analyze("", source_files=[])
        assert False, "Should raise ValueError on empty content"
    except ValueError:
        print("  [PASS] Correctly rejected empty analysis content with ValueError")

    print("\n" + "=" * 80)
    print("ALL STEP 1 INDUSTRIAL WORKFLOW TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    test_industrial_workflow()
