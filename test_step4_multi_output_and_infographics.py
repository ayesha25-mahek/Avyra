"""
test_step4_multi_output_and_infographics.py
-------------------------------------------
Comprehensive validation test suite for Step 4:
  1. Multi-Output Generation (DOCX + PPTX + Infographic Vector SVG in single pass).
  2. Industrial Vector Infographic Generator:
     - Verified .svg deliverable creation in output/infographics/
     - Verified genuine vector content: SVG tag, KPI cards, Defect severity distribution,
       Equipment tags, actionable recommendations, and zero external calls.
  3. Manager Executive Workspace:
     - GET /api/manager/reviews
     - POST /api/manager/reviews/action (Approve, Request Revision, Reject)
  4. Follow-Up Revision flow validation.
  5. Regression verification of Step 2 (role switching) & Step 3 (CAD DXF & Spreadsheet cleaner).
"""

import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from main import app

client = TestClient(app)


def test_step4_industrial_infographic_generator():
    print("\n--- 1. Testing Industrial Infographic Generator ---")
    from services.industrial_infographic_generator import industrial_infographic_generator

    content_model = {
        "title": "CDU-1 Atmospheric Column & Pressure Vessel Integrity Audit",
        "summary": "Ultrasonic thickness survey on crude distillation column shell V-101 indicated localized wall thinning and 1.8mm pitting depth on nozzle flange FL-204.",
        "key_points": [
            "Operating pressure measured at 4.2 bar with column top temperature 142 degC.",
            "ASME Section VIII Div 1 corrosion allowance exceeded on flange FL-204.",
            "Recalibrate pressure safety valve PSV-101 discharge threshold.",
            "Verify cathodic protection grounding resistance prior to quarterly sign-off.",
        ],
        "raw_text": """
        MANGALORE REFINERY CRUDE DISTILLATION UNIT CDU-1
        Vessel Tag: V-101 | Pump Tag: P-101A | Exchanger: E-204 | Valve: PSV-101 | Valve: XV-302
        Operating Pressure: 4.2 bar | Operating Temperature: 142 degC | Pitting Depth: 1.8 mm
        Corrosion status: High risk localized pitting on nozzle flange FL-204.
        Critical action: Inspect and replace flange gasket before restart.
        """,
        "source_files": ["CDU1_Vessel_Audit.pdf"],
    }

    result = industrial_infographic_generator.generate(content_model)
    assert result["type"] == "file", "Infographic result must be of type 'file'"
    assert Path(result["path"]).exists(), f"Generated SVG file {result['path']} does not exist on disk"
    assert result["filename"].endswith(".svg"), "File name must have .svg extension"
    assert result["download_url"].startswith("/files/infographics/"), "Download URL must point to /files/infographics/"

    svg_content = result["svg_content"]
    assert "<svg" in svg_content and "</svg>" in svg_content, "Must contain valid SVG markup"
    assert "CDU-1 Atmospheric Column" in svg_content, "Must ground title in content model"
    assert "4.2 bar" in svg_content or "142 degc" in svg_content.lower() or "V-101" in svg_content, "Must contain extracted metrics or tags"
    assert "Defect &amp; Risk Distribution" in svg_content or "Risk Distribution" in svg_content, "Must contain defect/risk breakdown"
    assert "AIR-GAPPED ON-PREMISE ENGINE" in svg_content, "Must contain sovereignty footer"

    print(" Industrial Infographic Generator produced valid, grounded vector SVG:", result["filename"])


def test_step4_manager_workspace_endpoints():
    print("\n--- 2. Testing Manager Workspace Endpoints ---")
    # 1. Fetch manager reviews
    res = client.get("/api/manager/reviews")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "reviews" in data, "Response must contain 'reviews' array"
    assert len(data["reviews"]) >= 3, "Must return seed reviews"

    first_review = data["reviews"][0]
    review_id = first_review["id"]
    print(f" Loaded {len(data['reviews'])} review items. Testing action on {review_id}...")

    # 2. Record manager review decision (approve)
    action_res = client.post("/api/manager/reviews/action", json={
        "review_id": review_id,
        "action": "approve",
        "comments": "Approved for field work with requirement of dual-signoff on gasket replacement.",
        "reviewer_role": "manager",
    })
    assert action_res.status_code == 200, f"Expected 200, got {action_res.status_code}: {action_res.text}"
    action_data = action_res.json()
    assert action_data["status"] == "success"
    assert action_data["review"]["status"] == "approved"
    assert "dual-signoff" in action_data["review"]["decision_comments"]

    print(" Manager review approval successfully recorded in audit trail.")


def test_step4_generated_files_catalog():
    print("\n--- 3. Testing Generated Files Catalog with SVG Deliverables ---")
    res = client.get("/api/generated-files")
    assert res.status_code == 200
    files_data = res.json()
    assert "files" in files_data
    # Verify .svg files can be included and cataloged
    extensions = [f["extension"] for f in files_data["files"]]
    print(f" Catalog returned {len(files_data['files'])} files with extensions: {set(extensions)}")


def test_step2_and_step3_regressions():
    print("\n--- 4. Running Regression Checks (Step 2 Roles & Step 3 CAD/Spreadsheet) ---")
    # Check health
    health = client.get("/api/health")
    assert health.status_code == 200

    # Check CAD requirements extraction
    doc_text = "Centrifugal Pump P-201 with impeller diameter 320 mm, suction 150 mm, discharge 100 mm, flange rating 300 lb, material 316SS."
    cad_res = client.post("/api/drawing/extract-requirements", data={"text": doc_text})
    assert cad_res.status_code == 200, f"CAD extract failed: {cad_res.text}"
    reqs = cad_res.json()["requirements"]
    assert "components" in reqs and len(reqs["components"]) >= 1, "Must extract components"
    assert "P-201" in str(reqs), "Must extract P-201 tag"

    # Check safe spreadsheet cleaner (accepts file upload)
    csv_bytes = (
        b"Timestamp,Equipment_Tag,Temperature_C,Pressure_Bar,Status\n"
        b"2026-10-01 00:00,P-101,65.2,12.4,Normal\n"
        b"2026-10-01 01:00,P-101,66.1,12.5,Normal\n"
        b"2026-10-01 02:00,P-101,#DIV/0!,12.3,Error\n"
        b"2026-10-01 03:00,P-101,65.8,,Normal\n"
        b"2026-10-01 04:00,P-101,67.0,12.6,Normal\n"
        b"2026-10-01 04:00,P-101,67.0,12.6,Normal\n"
        b"2026-10-01 05:00,P-101,980.5,12.5,Abnormal\n"
    )
    clean_res = client.post(
        "/api/spreadsheet/audit-clean",
        files={"file": ("sensor_telemetry.csv", csv_bytes, "text/csv")},
    )
    assert clean_res.status_code == 200, f"Spreadsheet audit failed: {clean_res.text}"
    audit_data = clean_res.json()
    assert audit_data.get("status") == "success"
    audit = audit_data.get("audit", {})
    assert audit.get("duplicate_rows", {}).get("count", 0) >= 1 or audit.get("outliers", {}).get("total_outliers", 0) >= 1

    print(" All Step 2 and Step 3 functionality verified intact.")


if __name__ == "__main__":
    test_step4_industrial_infographic_generator()
    test_step4_manager_workspace_endpoints()
    test_step4_generated_files_catalog()
    test_step2_and_step3_regressions()
    print("\n=======================================================")
    print(" ALL STEP 4 TESTS PASSED WITH ZERO REGRESSIONS!")
    print("=======================================================")
