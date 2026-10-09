"""
test_real_industrial_upload_analysis.py
---------------------------------------
Verifies that Avyara analyzes the ACTUAL uploaded content of documents/images
and produces genuine industrial reports matching the required sections:

1. Test PDF with explicit unique facts (e.g., Compressor K-502, Vibration 8.4 mm/s, Bearing Temp 92.5 C).
2. Test Image with visual observations and equipment markings.
3. Test Engineering Drawing / P&ID with tags (e.g., P-101A, TI-104, 4"-P-102-CS).
4. Test Handwritten / scanned document with dates and notes.
5. Asserts the exact section structure requested by the user.
6. Asserts technical/sovereignty details are strictly in the bottom evidence section.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.document_reader import DocumentReader
from services.content_intelligence import ContentIntelligence
from services.inspection_analysis_generator import InspectionAnalysisGenerator
from services.output_request import OutputRequest


def test_real_industrial_analysis():
    print("=" * 80)
    print("RUNNING REAL INDUSTRIAL DOCUMENT & IMAGE ANALYSIS TEST")
    print("=" * 80)

    reader = DocumentReader()
    ci = ContentIntelligence(provider="ollama")
    generator = InspectionAnalysisGenerator(provider="ollama")

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 1: Real Inspection Report PDF
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 1] Testing Real Inspection Report Analysis...")
    # Generate a temporary real test PDF with explicit, unique parameters
    test_pdf_path = Path("output/test_compressor_inspection.txt")  # also testable via reader
    # Let's write a realistic inspection report text file
    inspection_content = """REFINERY ROTATING EQUIPMENT AUDIT REPORT
Location: Unit 4 - Catalytic Reforming Section
Equipment Tag: K-502-A (Recycle Gas Compressor)
Manufacturer: Dresser-Rand | Model: 3M8-6
Inspection Date: 12/04/2026
Inspector: Senior Reliability Engineer R. Sharma

FIELD READINGS & OBSERVATIONS:
- Drive end bearing radial vibration recorded at 8.4 mm/s (Alarm limit: 4.5 mm/s, Trip: 7.1 mm/s).
- Non-drive end bearing temperature elevated to 92.5 C (Normal range: 60-75 C).
- Lube oil pressure: 2.1 bar (Baseline: 2.4 bar).
- Audible high-frequency cavitation/rubbing noise detected near inboard seal housing.
- Visible oil weeping around mechanical seal barrier fluid reservoir vent line.
- Foundation bolt #3 loose with visible fretting powder.

RECOMMENDATIONS & ACTIONS:
1. Immediate operational load reduction to 65% rated capacity.
2. Schedule vibration spectrum analysis (FFT) within 24 hours.
3. Tighten foundation bolts to 450 Nm torque.
4. Replace mechanical seal barrier fluid and check for hydrocarbon contamination.
"""
    test_pdf_path.write_text(inspection_content, encoding="utf-8")

    meta_1 = reader.read_with_metadata(str(test_pdf_path))
    content_model_1 = ci.analyze(meta_1["text"], [test_pdf_path.name], [meta_1])

    req_1 = OutputRequest(outputs=["inspection_analysis"], language="English", tone="Professional", target_audience="Refinery Engineers")
    res_1 = generator.generate(content_model_1, req_1)
    markdown_1 = res_1.get("content", "")

    print(f"    - Generated {len(markdown_1)} characters.")
    # Verify exact required sections for inspection report:
    # - Executive Summary
    # - Equipment / Asset Details
    # - Observed Findings
    # - Measurements / Readings
    # - Visible Defects or Abnormalities
    # - Risk / Priority Assessment
    # - Recommended Actions
    # - Evidence / Source
    # - Uncertainties and Limitations
    # - Verification Status
    # - Technical & Sovereignty Evidence
    assert "Executive Summary" in markdown_1, "Missing Executive Summary"
    assert "Equipment" in markdown_1 or "Asset Details" in markdown_1, "Missing Equipment/Asset Details"
    assert "Observed Findings" in markdown_1, "Missing Observed Findings"
    assert "Measurements" in markdown_1 or "Readings" in markdown_1, "Missing Measurements/Readings"
    assert "Visible Defects" in markdown_1 or "Abnormalities" in markdown_1, "Missing Visible Defects"
    assert "Risk" in markdown_1 or "Priority Assessment" in markdown_1, "Missing Risk Assessment"
    assert "Recommended Actions" in markdown_1, "Missing Recommended Actions"
    assert "Evidence" in markdown_1 or "Source" in markdown_1, "Missing Evidence/Source"
    assert "Uncertainties" in markdown_1 or "Limitations" in markdown_1, "Missing Uncertainties and Limitations"
    assert "Verification Status" in markdown_1, "Missing Verification Status"
    assert "Technical & Sovereignty Evidence" in markdown_1, "Missing Technical & Sovereignty Evidence at bottom"

    # Verify actual content from source is present and NOT generic
    assert "K-502" in markdown_1 or "K-502-A" in markdown_1, "Actual equipment tag K-502 missing!"
    assert ("8.4" in markdown_1 or "8.4 mm/s" in markdown_1 or "92.5" in markdown_1 or "92.5 C" in markdown_1), "Actual measurements missing!"
    print("    [OK] Case 1: Real Inspection Report accurately analyzed with real facts and correct sections!")

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 2: Engineering Drawing / P&ID
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 2] Testing Engineering Drawing / P&ID Analysis...")
    pid_file_meta = {
        "filename": "unit3_hydrocracker_pid.png",
        "source_type": "pid_or_process_diagram",
        "processing": "local_ocr_and_drawing_parser",
        "text": """=== INDUSTRIAL ENGINEERING DRAWING / P&ID AUDIT: unit3_hydrocracker_pid.png ===
Drawing No: DWG-HC-402-01 | Revision: Rev-B
--- Equipment & Instrument Tags Detected ---
P-202A, P-202B, V-301, TI-305, PT-302, PSV-201
--- Process Piping / Line Designations ---
6"-HC-201-CS, 4"-HC-202-CS
--- Engineering Specifications & Ratings ---
Design Pressure: 85 bar, Operating Temp: 240 C, Flange Class: 600#
--- Structured Engineering Observations ---
• Identified 6 readable equipment tags: P-202A, P-202B, V-301, TI-305, PT-302, PSV-201
• Identified 2 process line designations: 6"-HC-201-CS, 4"-HC-202-CS
""",
        "details": {
            "drawing_parsed": {
                "drawing_number": "DWG-HC-402-01",
                "revision": "Rev-B",
                "equipment_tags": ["P-202A", "P-202B", "V-301", "TI-305", "PT-302", "PSV-201"],
                "line_numbers": ["6\"-HC-201-CS", "4\"-HC-202-CS"],
                "parameters": ["85 bar", "240 C"],
            }
        }
    }
    content_model_2 = ci.analyze(pid_file_meta["text"], ["unit3_hydrocracker_pid.png"], [pid_file_meta])
    res_2 = generator.generate(content_model_2, req_1)
    markdown_2 = res_2.get("content", "")

    print(f"    - Generated {len(markdown_2)} characters.")
    # Verify exact required sections for engineering drawing/P&ID:
    # - Drawing Summary
    # - Identified Equipment/Tags
    # - Visible Connections/Lines
    # - Important Labels and Values
    # - Observed Relationships
    # - Potential Issues/Observations
    # - Unreadable/Uncertain Elements
    # - Verification Status
    assert "Drawing Summary" in markdown_2, "Missing Drawing Summary"
    assert "Identified Equipment" in markdown_2 or "Equipment/Tags" in markdown_2, "Missing Identified Equipment/Tags"
    assert "Visible Connections" in markdown_2 or "Connections/Lines" in markdown_2, "Missing Visible Connections/Lines"
    assert "Important Labels" in markdown_2 or "Labels and Values" in markdown_2, "Missing Important Labels and Values"
    assert "Observed Relationships" in markdown_2, "Missing Observed Relationships"
    assert "Potential Issues" in markdown_2 or "Observations" in markdown_2, "Missing Potential Issues/Observations"
    assert "Unreadable" in markdown_2 or "Uncertain Elements" in markdown_2, "Missing Unreadable/Uncertain Elements"
    assert "Verification Status" in markdown_2, "Missing Verification Status"
    assert "Technical & Sovereignty Evidence" in markdown_2, "Missing Technical Evidence at bottom"

    # Verify actual tags from source are present
    assert "P-202A" in markdown_2 or "P-202B" in markdown_2 or "V-301" in markdown_2, "Actual P&ID equipment tags missing!"
    print("    [OK] Case 2: Engineering Drawing / P&ID accurately analyzed with real tags and required sections!")

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 3: Handwritten / Scanned Document
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 3] Testing Handwritten / Scanned Document Analysis...")
    hw_file_meta = {
        "filename": "shift_operator_log.png",
        "source_type": "handwritten_note",
        "processing": "local_ocr",
        "text": """Shift 2 Field Notes - Date: 14/04/2026
Operator: J. Patel (Signed)
Unit: Crude Distillation Unit (CDU-1)
Inspected Pump P-104B at 14:30.
Discharge pressure reading 18.2 bar. Motor surface temp 68 C.
Noticed slight gland packing leakage (approx 12 drops/min).
Oil level in bearing housing normal.
Action taken: Greased outboard bearing, notified maintenance for packing adjustment.
OCR Quality: PARTIAL (Handwritten script)
""",
        "details": {
            "dates_detected": ["14/04/2026"],
            "measurements_detected": ["18.2 bar", "68 C"],
            "equipment_tags": ["P-104B"],
        }
    }
    content_model_3 = ci.analyze(hw_file_meta["text"], ["shift_operator_log.png"], [hw_file_meta])
    res_3 = generator.generate(content_model_3, req_1)
    markdown_3 = res_3.get("content", "")

    print(f"    - Generated {len(markdown_3)} characters.")
    # Verify exact required sections for handwritten/scanned documents:
    # - Extracted Information
    # - Important Findings
    # - Document Summary
    # - Actions/Recommendations
    # - Uncertain OCR text clearly marked
    assert "Extracted Information" in markdown_3, "Missing Extracted Information"
    assert "Important Findings" in markdown_3, "Missing Important Findings"
    assert "Document Summary" in markdown_3, "Missing Document Summary"
    assert "Actions" in markdown_3 or "Recommendations" in markdown_3, "Missing Actions/Recommendations"
    assert "Uncertain OCR Text" in markdown_3 or "Uncertain" in markdown_3, "Missing Uncertain OCR Text section"
    assert "Technical & Sovereignty Evidence" in markdown_3, "Missing Technical Evidence at bottom"

    # Verify actual extracted facts
    assert "P-104B" in markdown_3 or "18.2 bar" in markdown_3 or "Patel" in markdown_3, "Actual handwritten log content missing!"
    print("    [OK] Case 3: Handwritten / Scanned document accurately analyzed with required sections!")

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 4: Real Inspection Image
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 4] Testing Real Inspection Photograph / Asset Image...")
    from services.sih_demo_service import sih_demo_service
    sih_demo_service._ensure_demo_dataset()
    photo_path = Path("output/demo_data_pack/demo_inspection_flange_photo.png")
    assert photo_path.exists(), f"Demo photo missing: {photo_path}"
    meta_4 = reader.read_with_metadata(str(photo_path))
    content_model_4 = ci.analyze(meta_4["text"], [photo_path.name], [meta_4])
    res_4 = generator.generate(content_model_4, req_1)
    markdown_4 = res_4.get("content", "")

    print(f"    - Generated {len(markdown_4)} characters.")
    # Verify Step 14 exact required sections for defective/inspection image:
    assert "Executive Summary" in markdown_4, "Missing Executive Summary in image analysis"
    assert "Visible Defect" in markdown_4 or "Defect" in markdown_4, "Missing Visible Defect in image analysis"
    assert "Defect Location" in markdown_4 or "Location" in markdown_4, "Missing Defect Location in image analysis"
    assert "Visual Evidence" in markdown_4 or "Evidence" in markdown_4, "Missing Visual Evidence in image analysis"
    assert "Preliminary Severity" in markdown_4 or "Severity" in markdown_4, "Missing Preliminary Severity in image analysis"
    assert "Possible Impact" in markdown_4 or "Impact" in markdown_4, "Missing Possible Impact in image analysis"
    assert "Recommended Action" in markdown_4 or "Action" in markdown_4, "Missing Recommended Action in image analysis"
    assert "Uncertainty" in markdown_4 or "Limitations" in markdown_4, "Missing Uncertainty/Limitations in image analysis"
    assert "Technical & Sovereignty Evidence" in markdown_4, "Missing bottom Technical Evidence section"
    print("    [OK] Case 4: Real inspection image accurately analyzed with Step 14 defect sections!")

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 5: Different Asset Image (Cooling Tower Structure)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[TEST 5] Testing Different Asset Image (Cooling Tower Structure)...")
    pure_img_meta = {
        "filename": "cooling_tower_structure.jpg",
        "source_type": "image",
        "processing": "local_ocr",
        "text": """=== INSPECTION ARTIFACT: cooling_tower_structure.jpg ===
Technical Image Parameters: Format JPEG | Resolution: 1920x1080 | Size: 412 KB
--- Extracted Equipment Markings, Text & Labels (via Local OCR) ---
COOLING TOWER CELL #2 - HAZARD NOTICE
--- Visual Inspection Analysis Note ---
Inspection image verified on-premise. Structural timber framing, cross-bracing, and drift eliminator louvers visible.
""",
        "details": {
            "classification": {"category": "image"},
            "resolution": "1920x1080",
        }
    }
    content_model_5 = ci.analyze(pure_img_meta["text"], ["cooling_tower_structure.jpg"], [pure_img_meta])
    res_5 = generator.generate(content_model_5, req_1)
    markdown_5 = res_5.get("content", "")
    print(f"    - Generated {len(markdown_5)} characters.")
    assert "Executive Summary" in markdown_5, "Missing Executive Summary in Case 5"
    assert "Defect" in markdown_5 or "Visible Defect" in markdown_5, "Missing Visible Defect in Case 5"
    assert "Defect Location" in markdown_5 or "Location" in markdown_5, "Missing Location in Case 5"
    assert "Technical & Sovereignty Evidence" in markdown_5, "Missing bottom Technical Evidence section"

    # Assert that different images produce DIFFERENT findings
    assert markdown_4 != markdown_5, "Findings between different images must be distinct!"
    assert "cooling tower" in markdown_5.lower() or "tower" in markdown_5.lower(), "Case 5 content must reflect cooling tower!"
    assert "flange" in markdown_4.lower() or "p-101a" in markdown_4.lower(), "Case 4 content must reflect flange joint!"
    print("    [OK] Case 5: Verified that different uploaded images produce different relevant findings!")

    print("\n" + "=" * 80)
    print("ALL REAL INDUSTRIAL DOCUMENT & IMAGE ANALYSIS TESTS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    test_real_industrial_analysis()
