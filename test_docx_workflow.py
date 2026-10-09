"""
test_docx_workflow.py
---------------------
End-to-End verification script for STEP 7:
Integrate DOCX Deliverable Generation into Sovereign Workflow:
Inspection Report → Analysis → Recommendation → Approval Note → .docx
"""

import os
from pathlib import Path

from services.docx_generator import DocxGenerator
from services.document_reader import DocumentReader
from services.inspection_analysis_generator import InspectionAnalysisGenerator
from services.output_request import OutputRequest

def test_docx_pipeline():
    print("=" * 65)
    print("STEP 7: SOVEREIGN DOCX DELIVERABLE GENERATION VERIFICATION")
    print("=" * 65)

    # 1. Test DocxGenerator Standalone
    print("\n[1] Testing DocxGenerator Standalone Rendering...")
    docx_gen = DocxGenerator(output_dir="output/documents")
    sample_title = "Quarterly Facility & Network Inspection"
    sample_content = """# QUARTERLY FACILITY & NETWORK INSPECTION: INSPECTION FINDINGS & RISK ANALYSIS

## 1. EXECUTIVE SUMMARY & INSPECTION SCOPE
A comprehensive technical inspection of enterprise access relays and administrative terminals was conducted on 06 October 2026. The inspection aimed to assess identity boundary controls and credential integrity.

## 2. KEY INSPECTION FINDINGS
- **Finding 1**: Unauthenticated administrative portal exposed without MFA enforcement.
- **Finding 2**: 14 user workstations targeted by coordinated credential harvesting.
- **Conformity**: Network perimeter firewall rules comply with basic gateway standards.

## 3. COMPREHENSIVE RISK & VULNERABILITY ANALYSIS
- **Operational Risk (Critical)**: Potential lateral movement to core domain controllers.
- **Compliance Exposure (High)**: Non-compliance with mandatory zero-trust identity policy.

## 4. STRATEGIC RECOMMENDATIONS & MITIGATION ROADMAP
1. **Immediate Revocation**: Invalidate all administrative tokens within 30 minutes.
2. **Process Hardening**: Enforce FIDO2 hardware tokens on all privileged endpoints.
3. **Long-Term Governance**: Deploy autonomous continuous SOC telemetry verification.

## 5. REGULATORY COMPLIANCE & SIGN-OFF DETERMINATION
OFFICIAL SIGN-OFF STATUS: CONDITIONAL APPROVAL
- Statutory Reference: SOP-SEC-402 Clause 2.1 & SOP-INSP-001 Section 3
- Verification Conditions: Full operational approval contingent upon verified FIDO2 deployment within 7 business days.

## 6. AUTONOMOUS AGENT VERIFICATION AUDIT TRAIL
1. Document Ingestion: Source report parsed via DocumentReader.
2. Findings Extraction: Observation parameters structured.
3. Risk Assessment: Critical/High severity tags assigned.
4. Knowledge Base Verification: Cross-referenced against Sovereign RAG SOP-SEC-402.
5. Mitigation Planning: 7-stage tactical roadmap compiled.
6. Deliverable Synthesis: Publication-grade .docx generated via DocxGenerator.
7. Compliance Verification: Sovereign compliance criteria satisfied.
"""
    standalone_res = docx_gen.generate_inspection_approval_docx(
        title=sample_title,
        content_markdown=sample_content,
        metadata={
            "provider": "Local Ollama (Qwen 2.5 7B)",
            "doc_ref": "SIH-TEST-001",
            "status": "Standalone Verification",
        },
        filename="test_standalone_approval_note.docx",
    )
    print("    Standalone Generation Result:")
    print(f"    - Type: {standalone_res['type']}")
    print(f"    - Path: {standalone_res['path']}")
    print(f"    - Filename: {standalone_res['filename']}")
    print(f"    - Size: {standalone_res['size_bytes']} bytes")

    assert os.path.exists(standalone_res["path"]), "Generated DOCX file must exist on disk!"
    assert standalone_res["size_bytes"] > 0, "DOCX file must not be empty!"

    # 2. Verify reading back the generated DOCX via existing DocumentReader
    print("\n[2] Verifying Generated DOCX via Existing DocumentReader...")
    reader = DocumentReader()
    readback_text = reader.read(standalone_res["path"])
    print(f"    Read back text length: {len(readback_text)} chars")
    assert "QUARTERLY FACILITY & NETWORK INSPECTION" in readback_text
    assert "CONDITIONAL APPROVAL" in readback_text
    print("    [OK] DocumentReader successfully parsed generated DOCX!")

    # 3. Test Full SIH End-to-End Workflow with Local Qwen + RAG + DOCX
    print("\n[3] Testing End-to-End SIH Workflow (Inspection Report -> Qwen -> RAG -> .docx)...")
    gen = InspectionAnalysisGenerator(provider="ollama")
    mock_content_model = {
        "title": "Quarterly Technical Infrastructure & Phishing Incident Audit",
        "summary": "Coordinated phishing attack targeted administrative users; multiple employees submitted credentials to fraudulent login page. High risk of lateral movement to internal core services.",
        "key_points": [
            "14 administrative employees targeted across finance and infrastructure teams",
            "3 credentials submitted before fraudulent domain was isolated",
            "Absence of FIDO2 hardware token enforcement on legacy administrative portal",
        ],
        "source_files": ["cybersecurity_test_document.pdf"],
    }
    mock_req = OutputRequest(
        outputs=["inspection_analysis"],
        tone="Executive & Authoritative",
        language="English",
        target_audience="Enterprise Risk & Compliance Committee",
    )

    full_workflow_res = gen.generate(mock_content_model, mock_req)
    print("\n    End-to-End Workflow Result:")
    print(f"    - Type: {full_workflow_res.get('type')}")
    print(f"    - File Path: {full_workflow_res.get('path')}")
    print(f"    - Filename: {full_workflow_res.get('filename')}")
    print(f"    - Size: {full_workflow_res.get('size_bytes')} bytes")
    print(f"    - Content Preview (First 300 chars):\n{full_workflow_res.get('content', '')[:300]}...")

    assert full_workflow_res.get("type") == "file"
    assert os.path.exists(full_workflow_res.get("path")), "Workflow output file must exist!"
    assert full_workflow_res.get("filename").endswith(".docx"), "Filename must end with .docx!"

    print("\n" + "=" * 65)
    print("[SUCCESS] STEP 7 DOCX DELIVERABLE GENERATION FULLY VERIFIED!")
    print("=" * 65)

if __name__ == "__main__":
    test_docx_pipeline()
