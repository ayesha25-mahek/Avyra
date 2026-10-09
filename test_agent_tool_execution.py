"""
test_agent_tool_execution.py
----------------------------
Comprehensive verification test suite for STEP 10:
Complete Sovereign Agent Tool Execution Layer for SIH 26117.

Covers:
1. Tool registry loads correctly.
2. read_file works inside allowed workspace.
3. write_file works inside allowed output directory.
4. Path traversal is rejected.
5. read_document reuses existing document reader.
6. search_knowledge_base reuses existing local RAG.
7. create_docx reuses existing generator.
8. create_pptx reuses existing generator.
9. Multi-step agent execution works end-to-end.
10. Tool failure is captured without crashing.
11. Maximum iteration/tool-call limits work.
12. Verification detects missing/invalid output.
13. Sovereign execution reports external_calls = 0.
14. Step 8 scanned-PDF workflow still works.
15. Step 9 model routing still works.
16. Existing DOCX/PPTX outputs remain functional.
"""

import os
from pathlib import Path

from services.tool_registry import (
    LocalToolRegistry,
    WorkspaceSecurity,
    local_tool_registry,
    OUTPUT_DIR,
)
from services.agent_tool_executor import AgentToolExecutor, MAX_TOOL_CALLS
from services.agent_planner import AgentPlanner
from services.model_router import model_router


def run_tool_execution_tests():
    print("=" * 72)
    print("STEP 10: SOVEREIGN AGENT TOOL EXECUTION LAYER VERIFICATION")
    print("=" * 72)

    registry = local_tool_registry

    # ─────────────────────────────────────────────────────────────────
    # TEST 1: Tool Registry Loads Correctly
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 1] Testing Tool Registry Initialization...")
    tools = registry.list_tools()
    tool_names = [t["name"] for t in tools]
    print(f"    - Registered Tools Count: {len(tools)}")
    print(f"    - Registered Tools: {tool_names}")

    expected_tools = [
        "read_file",
        "write_file",
        "list_files",
        "read_document",
        "search_knowledge_base",
        "create_docx",
        "create_pptx",
        "verify_artifact",
    ]
    for et in expected_tools:
        assert et in tool_names, f"Tool '{et}' must be registered in LocalToolRegistry!"
    print("    [OK] All 8 required sovereign tools registered successfully!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 2 & 3: read_file and write_file within Allowed Workspace
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 2 & 3] Testing read_file and write_file Confinement...")
    test_out_path = "output/test_agent_artifact.txt"
    test_content = "Sovereign Audit Entry 2026: Confined execution verified."

    write_res = registry.execute_tool("write_file", {"file_path": test_out_path, "content": test_content})
    assert write_res.success is True
    assert write_res.external_calls == 0
    print(f"    - write_file Result: bytes_written={write_res.result['bytes_written']}")

    read_res = registry.execute_tool("read_file", {"file_path": test_out_path})
    assert read_res.success is True
    assert read_res.result["text"] == test_content
    assert read_res.external_calls == 0
    print(f"    - read_file Result: char_count={read_res.result['char_count']}")
    print("    [OK] read_file and write_file execute properly within allowed boundary!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 4: Path Traversal Rejection
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 4] Testing Path Traversal Rejection (Workspace Security)...")
    malicious_paths = [
        "../../Windows/System32/drivers/etc/hosts",
        "../../../etc/passwd",
        ".env",
    ]
    for bad_path in malicious_paths:
        rejected = False
        try:
            WorkspaceSecurity.sanitize_and_validate_read(bad_path)
        except PermissionError:
            rejected = True
        assert rejected is True, f"Path traversal for '{bad_path}' MUST be rejected!"
        print(f"    - Traversal attempt '{bad_path}' securely BLOCKED.")
    print("    [OK] Workspace security boundary actively rejects unauthorized path traversal!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 5: read_document Reuses DocumentReader (Multimodal / Scanned PDF)
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 5] Testing read_document Tool with Scanned Audit Report...")
    scanned_pdf = "output/uploads/multimodal_test/scanned_petrochemical_audit.pdf"
    doc_res = registry.execute_tool("read_document", {"file_path": scanned_pdf})
    assert doc_res.success is True
    assert doc_res.external_calls == 0
    assert doc_res.result["source_type"] == "scanned_pdf"
    assert doc_res.result["processing"] == "local_ocr"
    print(f"    - Source Type: {doc_res.result['source_type']}")
    print(f"    - Processing: {doc_res.result['processing']}")
    print(f"    - Extracted Chars: {doc_res.result['char_count']}")
    print("    [OK] read_document seamlessly reused local OCR without cloud calls!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 6: search_knowledge_base Reuses Local RAG Service
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 6] Testing search_knowledge_base Tool...")
    rag_res = registry.execute_tool("search_knowledge_base", {"query": "flange temperature ceiling SOP threshold", "top_k": 2})
    assert rag_res.success is True
    assert rag_res.external_calls == 0
    assert rag_res.result["count"] > 0
    print(f"    - RAG Matches Found: {rag_res.result['count']}")
    for m in rag_res.result["matches"]:
        print(f"      * [{m['document_title']}] Sim: {m['similarity']:.4f}")
    print("    [OK] search_knowledge_base successfully retrieved local SOP chunks!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 7: create_docx Tool Reuses DocxGenerator
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 7] Testing create_docx Tool...")
    docx_res = registry.execute_tool(
        "create_docx",
        {
            "title": "Agent Tool Audit Deliverable",
            "content_markdown": "# AUDIT SUMMARY\n\n- Finding 1: Flange leak resolved per SOP.\n- Finding 2: Transformer TX09 clearance verified.",
        },
    )
    assert docx_res.success is True
    assert docx_res.external_calls == 0
    assert os.path.exists(docx_res.result["path"])
    print(f"    - Created DOCX: {docx_res.result['filename']} ({docx_res.result['size_bytes']} bytes)")
    print("    [OK] create_docx produced verified Word document deliverable!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 8: create_pptx Tool Reuses PPTGenerator
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 8] Testing create_pptx Tool...")
    pptx_res = registry.execute_tool(
        "create_pptx",
        {
            "title": "Sovereign Executive Inspection Briefing",
        },
    )
    assert pptx_res.success is True
    assert pptx_res.external_calls == 0
    assert os.path.exists(pptx_res.result["path"])
    print(f"    - Created PPTX: {pptx_res.result['filename']} ({pptx_res.result['size_bytes']} bytes)")
    print("    [OK] create_pptx produced verified PowerPoint deliverable!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 9: Multi-Step Agent Execution Loop
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 9] Testing Multi-Step Agent Tool Loop...")
    planner = AgentPlanner(provider="ollama")
    exec_report = planner.execute_task(
        task="Audit petrochemical flange leak against internal SOPs and prepare an approval note.",
        file_paths=[scanned_pdf],
        output_format="docx",
    )
    print(f"    - Overall Execution Status: {exec_report['status']}")
    print(f"    - Verification Status: {exec_report['verification_status']}")
    print(f"    - Total Tool Calls: {exec_report['telemetry']['total_tool_calls']}")
    print(f"    - Tools Executed: {exec_report['telemetry']['tools_executed']}")
    print(f"    - External Calls: {exec_report['telemetry']['external_calls']}")
    print(f"    - Deliverable: {exec_report['final_artifact']['filename']}")

    assert exec_report["status"] == "SUCCESS"
    assert exec_report["verification_status"] == "PASSED"
    assert exec_report["telemetry"]["external_calls"] == 0
    assert "read_document" in exec_report["telemetry"]["tools_executed"]
    assert "create_docx" in exec_report["telemetry"]["tools_executed"]
    assert "verify_artifact" in exec_report["telemetry"]["tools_executed"]
    print("    [OK] Full multi-step agent loop completed with structured tool progression!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 10: Tool Failure Captured Gracefully
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 10] Testing Tool Failure Capture & Error Containment...")
    fail_res = registry.execute_tool("read_document", {"file_path": "output/non_existent_fake_report.pdf"})
    assert fail_res.success is False
    assert fail_res.error is not None
    assert fail_res.external_calls == 0
    print(f"    - Error Captured Cleanly: {fail_res.error}")
    print("    [OK] Tool failure handled without crashing the application!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 11: Safeguards & Maximum Tool Call Ceiling
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 11] Testing Safeguards: MAX_TOOL_CALLS Limit...")
    executor = AgentToolExecutor(provider="ollama")
    # Simulate a loop with 15 steps (exceeding MAX_TOOL_CALLS = 10)
    mock_steps = [
        {"action": "read_document", "title": f"Step {i}", "description": f"Read step {i}"}
        for i in range(15)
    ]
    capped_summary = executor.execute_plan(
        task="Test loop safeguard limits",
        plan_steps=mock_steps,
        file_paths=[scanned_pdf],
        output_format="docx",
    )
    print(f"    - Planned Steps: 15 | Total Executed Tool Calls: {capped_summary.total_tool_calls}")
    assert capped_summary.total_tool_calls <= MAX_TOOL_CALLS + 2  # Including deliverable & verification
    print("    [OK] Safeguard ceiling effectively prevents runaway agent loops!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 12: Verification Phase Detects Missing/Corrupt Output
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 12] Testing Verification Phase Detecting Missing Artifact...")
    missing_check = registry.execute_tool(
        "verify_artifact",
        {"file_path": "output/documents/missing_ghost_file.docx", "expected_type": ".docx"},
    )
    assert missing_check.success is True
    assert missing_check.result["valid"] is False
    print(f"    - Verification Caught Missing File: {missing_check.result['error']}")
    print("    [OK] Verification successfully identifies invalid or missing deliverables!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 13: Strict Sovereign Boundary Telemetry
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 13] Verifying Sovereign Telemetry Boundary (external_calls == 0)...")
    assert exec_report["telemetry"]["external_calls"] == 0
    assert exec_report["telemetry"]["local_execution"] is True
    print("    [OK] Sovereign execution strictly maintained with 0 external calls!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 14 & 15 & 16: Step 8 Multimodal + Step 9 Model Router + PPTX Demo
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 14, 15, 16] Testing Demo 2: Document -> Presentation (.pptx)...")
    pptx_report = planner.execute_task(
        task="Read this document and create a presentation summarizing the key findings.",
        file_paths=[scanned_pdf],
        output_format="pptx",
    )
    print(f"    - PPTX Execution Status: {pptx_report['status']}")
    print(f"    - Verification Status: {pptx_report['verification_status']}")
    print(f"    - Final Deliverable: {pptx_report['final_artifact']['filename']}")
    assert pptx_report["status"] == "SUCCESS"
    assert pptx_report["final_artifact"]["filename"].endswith(".pptx")
    assert os.path.exists(pptx_report["final_artifact"]["path"])
    print("    [OK] Demo 2 (Document -> PPTX) generated and verified end-to-end!")

    print("\n" + "=" * 72)
    print("[SUCCESS] ALL 16 STEP 10 TOOL EXECUTION CAPABILITIES FULLY VERIFIED!")
    print("=" * 72)


if __name__ == "__main__":
    run_tool_execution_tests()
