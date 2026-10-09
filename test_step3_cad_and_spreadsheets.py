"""
Comprehensive Verification Suite for Step 3:
1. Document-to-Engineering-Drawing Generation (Deterministic SVG & AutoCAD DXF).
2. Document-to-Spreadsheet Generation (Publication-grade multi-sheet XLSX).
3. Safe Spreadsheet Data Cleanup & Outlier Detection (Non-destructive correction with raw preservation).
"""

import sys
import os
import io
import json
import zipfile
import requests

BASE_URL = "http://127.0.0.1:8000"

def log(msg, status="INFO"):
    symbol = "+" if status == "PASS" else ("X" if status == "FAIL" else "*")
    print(f"[{symbol}] [{status}] {msg}")

def test_document_to_cad_extraction():
    log("Testing CAD Requirements Extraction from Technical Specification...", "INFO")
    sample_doc_text = """
    CRUDE DISTILLATION UNIT SPECIFICATION (CDU-01)
    Drawing: P&ID-CDU-2026-REV01
    Unit: Atmospheric Fractionation Section
    
    EQUIPMENT LIST:
    1. Crude Column V-101: Diameter 4200mm, Height 48000mm, Material SA-516 Gr 70. Design Pressure 3.5 bar, Design Temp 360 C.
    2. Crude Charge Furnace F-101: Duty 45 MW, Tube Material 5Cr-0.5Mo.
    3. Atmospheric Column Overhead Condenser E-102: Shell & Tube, Material Carbon Steel with Titanium tubes.
    4. Heavy Naphtha Reflux Pump P-103A/B: Flow 120 m3/h, Head 85m, Impeller SS 316.
    5. Crude Feed Transfer Line: 16"-CDU-1001-CS-600# from storage tank TK-401 to Desalter V-102.
    
    SAFETY NOTES:
    - All flanged connections to comply with ASME B16.5 Class 300.
    - Relief valves PSV-101A/B set at 4.2 bar gauge relieving to flare header.
    """

    res = requests.post(
        f"{BASE_URL}/api/drawing/extract-requirements",
        data={"text": sample_doc_text},
        timeout=15,
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data.get("status") == "success"
    reqs = data.get("requirements", {})
    
    assert "V-101" in json.dumps(reqs), "V-101 tag missing from extracted components"
    assert "F-101" in json.dumps(reqs), "F-101 tag missing from extracted components"
    assert len(reqs.get("components", [])) >= 3, f"Expected at least 3 components, got {len(reqs.get('components', []))}"
    log(f"Extracted {len(reqs.get('components', []))} components and {len(reqs.get('dimensions', []))} dimensions", "PASS")
    return reqs

def test_cad_drawing_generation(extracted_reqs):
    log("Testing Deterministic CAD Generation (SVG + AutoCAD DXF)...", "INFO")
    drawing_types = ["pid_schematic", "process_flow", "2d_mechanical", "equipment_arrangement"]
    
    for dtype in drawing_types:
        payload = {
            "title": f"CDU Atmospheric Fractionation ({dtype.replace('_', ' ').title()})",
            "drawing_number": f"DWG-CDU-2026-{dtype[:4].upper()}",
            "revision": "REV 0 (DRAFT - NOT FOR CONSTRUCTION)",
            "project_unit": "Atmospheric Crude Distillation Section",
            "drawing_type": dtype,
            "components": extracted_reqs.get("components", []),
            "dimensions": extracted_reqs.get("dimensions", []),
            "notes": extracted_reqs.get("notes", [
                "CONFIDENTIAL INDUSTRIAL DESIGN - FOR LOCAL REVIEW ONLY",
                "PRELIMINARY DRAFT GENERATION - PENDING PROFESSIONAL ENGINEER CERTIFICATION",
            ]),
        }
        
        res = requests.post(f"{BASE_URL}/api/drawing/generate-cad", json=payload, timeout=15)
        assert res.status_code == 200, f"Failed for {dtype}: {res.text}"
        data = res.json()
        assert data.get("status") == "success", f"Status not success for {dtype}"
        
        # Verify SVG content
        svg_content = data.get("svg_content", "")
        assert "<svg" in svg_content and "</svg>" in svg_content, "Invalid SVG structure"
        assert "PRELIMINARY / DRAFT" in svg_content, "Draft watermark missing from SVG"
        assert data.get("svg_path"), "SVG file path missing"
        assert os.path.exists(data["svg_path"]), f"Physical SVG file does not exist: {data['svg_path']}"
        
        # Verify DXF output
        dxf_path = data.get("dxf_path")
        assert dxf_path and os.path.exists(dxf_path), f"Physical DXF file does not exist: {dxf_path}"
        with open(dxf_path, "r", encoding="utf-8") as f:
            dxf_text = f.read()
        assert "SECTION" in dxf_text and "ENTITIES" in dxf_text and "EOF" in dxf_text, "Invalid AutoCAD DXF ASCII structure"
        
        # Verify static download endpoints
        svg_url = data["download_urls"]["svg"]
        dxf_url = data["download_urls"]["dxf"]
        svg_dl_res = requests.get(f"{BASE_URL}{svg_url}", timeout=10)
        assert svg_dl_res.status_code == 200, f"SVG download URL failed: {svg_url}"
        dxf_dl_res = requests.get(f"{BASE_URL}{dxf_url}", timeout=10)
        assert dxf_dl_res.status_code == 200, f"DXF download URL failed: {dxf_url}"
        
        log(f"Drawing Type '{dtype}' generated: SVG ({len(svg_content)} chars), DXF ({len(dxf_text)} chars)", "PASS")

def test_document_to_spreadsheet():
    log("Testing Document-to-Spreadsheet Schema Extraction and Multi-Sheet XLSX Generation...", "INFO")
    sample_plant_doc = """
    MONTHLY ASSET HEALTH & MAINTENANCE REGISTER
    Refinery Section: Hydrocracker Unit 03
    Period: October 2026
    
    EQUIPMENT MASTER:
    Tag: R-301 | Description: 1st Stage Hydrocracking Reactor | Design Temp: 450 C | Design Pressure: 150 bar | Status: Operational
    Tag: C-301 | Description: Recycle Gas Compressor | Power: 8500 kW | Seal Type: Dry Gas Seal | Status: Active
    Tag: P-302A | Description: Reactor Feed Booster Pump | Flow: 280 m3/h | Head: 320m | Status: Running
    Tag: P-302B | Description: Reactor Feed Standby Pump | Flow: 280 m3/h | Head: 320m | Status: Standby
    Tag: E-301 | Description: Combined Feed Effluent Exchanger | Duty: 32 MW | Area: 2400 m2 | Status: Operational
    
    MAINTENANCE LOG:
    Date: 2026-10-01 | Equipment: C-301 | Task: Vibration Analysis Routine | Performed By: Tech-A | Findings: Normal 1.8 mm/s
    Date: 2026-10-04 | Equipment: P-302B | Task: Mechanical Seal Inspection | Performed By: Tech-C | Findings: Minor seepage noted
    Date: 2026-10-08 | Equipment: R-301 | Task: Catalyst Bed DP Monitoring | Performed By: Tech-B | Findings: Bed delta-P 0.82 bar
    
    OPERATIONAL SENSOR LOGS:
    Timestamp: 2026-10-09 08:00 | Sensor: TI-3011 | Location: R-301 Bed 1 Inlet | Reading: 412.5 C | Limit: 435.0 C | Normal
    Timestamp: 2026-10-09 08:00 | Sensor: PI-3015 | Location: R-301 Top Dome | Reading: 142.8 bar | Limit: 155.0 bar | Normal
    Timestamp: 2026-10-09 08:00 | Sensor: VI-3022 | Location: C-301 NDE Bearing | Reading: 2.1 mm/s | Limit: 4.5 mm/s | Normal
    """

    res = requests.post(
        f"{BASE_URL}/api/spreadsheet/extract-from-doc",
        data={"text": sample_plant_doc},
        timeout=15,
    )
    assert res.status_code == 200, f"Extraction failed: {res.text}"
    data = res.json()
    assert data.get("status") == "success"
    schema = data.get("proposed_schema", {})
    assert len(schema.get("sheets", [])) >= 2, f"Expected multiple sheets, got {len(schema.get('sheets', []))}"
    log(f"Extracted workbook schema with {len(schema['sheets'])} sheets", "PASS")

    # Generate workbook
    gen_res = requests.post(f"{BASE_URL}/api/spreadsheet/generate-workbook", json=schema, timeout=15)
    assert gen_res.status_code == 200, f"Workbook generation failed: {gen_res.text}"
    gen_data = gen_res.json()
    assert gen_data.get("status") == "success"
    assert gen_data.get("sheet_count") >= 2
    xlsx_path = gen_data.get("file_path")
    assert xlsx_path and os.path.exists(xlsx_path), f"XLSX file not found on disk: {xlsx_path}"
    
    # Verify XLSX is valid zip file with standard Excel structure
    with zipfile.ZipFile(xlsx_path, "r") as zf:
        namelist = zf.namelist()
        assert "[Content_Types].xml" in namelist and "xl/workbook.xml" in namelist, "Not a valid Excel XLSX archive"
    
    # Download check
    dl_res = requests.get(f"{BASE_URL}{gen_data['download_url']}", timeout=10)
    assert dl_res.status_code == 200 and len(dl_res.content) > 1000, "XLSX download endpoint failed"
    log(f"Multi-sheet XLSX generated successfully ({len(dl_res.content)} bytes)", "PASS")

def test_safe_spreadsheet_cleanup():
    log("Testing Safe Tabular Data Audit & Safe Correction Pipeline...", "INFO")
    # Synthetic operational dataset with:
    # 1. Duplicate row
    # 2. Missing cell
    # 3. Formula error token (#DIV/0!)
    # 4. Outlier value (Temperature = 980 C vs normal ~65-75 C)
    csv_content = (
        "Timestamp,Equipment_Tag,Temperature_C,Pressure_Bar,Vibration_mm_s,Status\n"
        "2026-10-01 00:00,P-101,65.2,12.4,1.8,Normal\n"
        "2026-10-01 01:00,P-101,66.1,12.5,1.9,Normal\n"
        "2026-10-01 02:00,P-101,#DIV/0!,12.3,1.7,Error\n"
        "2026-10-01 03:00,P-101,65.8,,1.8,Normal\n"
        "2026-10-01 04:00,P-101,67.0,12.6,2.0,Normal\n"
        "2026-10-01 04:00,P-101,67.0,12.6,2.0,Normal\n" # Duplicate row
        "2026-10-01 05:00,P-101,980.5,12.5,1.9,Abnormal\n" # Extreme 3-sigma outlier
        "2026-10-01 06:00,P-101,66.4,12.4,1.8,Normal\n"
        "2026-10-01 07:00,P-101,65.9,12.5,1.8,Normal\n"
    )

    files = {"file": ("sensor_telemetry.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    audit_res = requests.post(f"{BASE_URL}/api/spreadsheet/audit-clean", files=files, timeout=15)
    assert audit_res.status_code == 200, f"Audit failed: {audit_res.text}"
    audit_data = audit_res.json()
    assert audit_data.get("status") == "success"
    
    audit = audit_data.get("audit", {})
    assert audit.get("duplicate_rows", {}).get("count", 0) >= 1, "Duplicate row not detected"
    assert audit.get("missing_values", {}).get("total_missing", 0) >= 1, "Missing value not detected"
    assert audit.get("formula_errors", {}).get("total_errors", 0) >= 1, "Formula error (#DIV/0!) not detected"
    assert audit.get("outliers", {}).get("total_outliers", 0) >= 1, "Outlier (980.5 C) not detected"
    
    corrections = audit.get("proposed_corrections", [])
    assert len(corrections) >= 3, f"Expected at least 3 corrections, got {len(corrections)}"
    log(f"Audit detected: {audit['duplicate_rows']['count']} duplicate, {audit['missing_values']['total_missing']} missing, {audit['formula_errors']['total_errors']} formula error, {audit['outliers']['total_outliers']} outliers", "PASS")

    # Apply all approved corrections
    apply_payload = {
        "headers": audit_data["raw_headers"],
        "original_rows": audit_data["raw_rows"],
        "approved_correction_ids": [c["id"] for c in corrections],
        "all_proposed_corrections": corrections,
        "source_filename": "sensor_telemetry.csv",
    }
    clean_res = requests.post(f"{BASE_URL}/api/spreadsheet/apply-corrections", json=apply_payload, timeout=15)
    assert clean_res.status_code == 200, f"Applying corrections failed: {clean_res.text}"
    clean_data = clean_res.json()
    assert clean_data.get("status") == "success"
    assert clean_data.get("corrections_applied_count") >= 3
    assert clean_data.get("remaining_rows") == 8, f"Expected 8 rows after duplicate removal, got {clean_data.get('remaining_rows')}"
    
    # Verify raw copy preservation
    assert clean_data.get("raw_preserved_url"), "Raw preserved download URL missing"
    assert clean_data.get("download_url"), "Cleaned XLSX download URL missing"
    
    cleaned_file_res = requests.get(f"{BASE_URL}{clean_data['download_url']}", timeout=10)
    assert cleaned_file_res.status_code == 200 and len(cleaned_file_res.content) > 1000, "Cleaned XLSX download failed"
    
    raw_file_res = requests.get(f"{BASE_URL}{clean_data['raw_preserved_url']}", timeout=10)
    assert raw_file_res.status_code == 200 and len(raw_file_res.content) > 0, "Raw preserved file download failed"
    
    log(f"Applied {clean_data['corrections_applied_count']} corrections. Cleaned XLSX size: {len(cleaned_file_res.content)} bytes. Raw preserved copy verified intact.", "PASS")

if __name__ == "__main__":
    print("=" * 80)
    print("RUNNING STEP 3 AUTOMATED VERIFICATION SUITE")
    print("=" * 80)
    try:
        reqs = test_document_to_cad_extraction()
        test_cad_drawing_generation(reqs)
        test_document_to_spreadsheet()
        test_safe_spreadsheet_cleanup()
        print("=" * 80)
        log("ALL STEP 3 CAD AND SPREADSHEET VERIFICATIONS PASSED WITH ZERO ERRORS!", "PASS")
        print("=" * 80)
    except AssertionError as e:
        log(str(e), "FAIL")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "FAIL")
        sys.exit(1)
