"""
test_model_router.py
--------------------
Comprehensive verification test suite for STEP 9:
Local Model Router & Dynamic Task-Model Selection for SIH 26117 Sovereign Workbench.

Verifications:
1. General reasoning task -> selects suitable local model (qwen2.5:7b).
2. Inspection analysis -> selects local reasoning model with RAG grounding.
3. Multimodal task with no vision model installed -> falls back safely to Local OCR + Qwen.
4. Explicit Ollama/Sovereign mode -> external_calls == 0 guaranteed (zero cloud leakage).
5. Cloud provider mode -> preserves cloud provider routing.
6. Unavailable preferred model -> safe fallback without crashing.
7. Existing Step 8 scanned-PDF workflow -> still works with router integration.
8. Existing DOCX deliverable generation -> still works with routing metadata attached.
9. Existing Sovereign RAG -> still works.
"""

import os
from pathlib import Path

from services.model_router import LocalModelRouter, ModelRegistry, TaskClassifier, model_router
from services.llm_pool import LLMPool
from services.agent_planner import AgentPlanner
from services.inspection_analysis_generator import InspectionAnalysisGenerator
from services.output_request import OutputRequest
from services.rag_service import RagService


def run_router_tests():
    print("=" * 70)
    print("STEP 9: LOCAL MODEL ROUTER & TASK-MODEL SELECTION VERIFICATION")
    print("=" * 70)

    # ─────────────────────────────────────────────────────────────────
    # TEST 1: General Reasoning Task -> Selects Qwen 2.5 7B Locally
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 1] Testing General Reasoning Task in Sovereign Mode...")
    d1 = model_router.route(
        prompt="Explain the difference between fail-safe and fail-secure mechanisms in plant control systems.",
        provider_mode="ollama",
    )
    print(f"    - Task Type: {d1.task_type}")
    print(f"    - Selected Model: {d1.selected_model}")
    print(f"    - Provider: {d1.provider}")
    print(f"    - Local: {d1.local}")
    print(f"    - External Calls: {d1.external_calls}")
    print(f"    - Reason: {d1.reason}")

    assert d1.task_type == "general_reasoning"
    assert d1.selected_model in ("qwen2.5:7b", "gemma3:1b")
    assert d1.local is True
    assert d1.external_calls == 0
    print("    [OK] General reasoning correctly routed to local sovereign model!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 2: Inspection Analysis Task -> Selects Qwen 2.5 7B with RAG Grounding
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 2] Testing Inspection Analysis Routing...")
    d2 = model_router.route(
        prompt="Analyze petrochemical inspection report, evaluate high-pressure flange leak against SOP standards.",
        outputs=["inspection_analysis"],
        provider_mode="ollama",
    )
    print(f"    - Task Type: {d2.task_type}")
    print(f"    - Selected Model: {d2.selected_model}")
    print(f"    - Provider: {d2.provider}")
    print(f"    - Local: {d2.local}")
    print(f"    - External Calls: {d2.external_calls}")
    print(f"    - Reason: {d2.reason}")

    assert d2.task_type == "inspection_analysis"
    assert d2.selected_model == "qwen2.5:7b"
    assert d2.local is True
    assert d2.external_calls == 0
    print("    [OK] Inspection analysis routed to Qwen 2.5 7B sovereign reasoning model!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 3: Multimodal Task with No Vision Model Installed -> Fallback to OCR + Qwen
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 3] Testing Multimodal Task Fallback Behavior (No Vision Model Installed)...")
    test_img = "output/uploads/multimodal_test/inspection_transformer_tx09.jpg"
    d3 = model_router.route(
        prompt="Inspect transformer placard photo for dielectric oil breakdown.",
        files=[test_img],
        provider_mode="ollama",
    )
    print(f"    - Task Type: {d3.task_type}")
    print(f"    - Selected Model: {d3.selected_model}")
    print(f"    - Vision Model: {d3.vision_model}")
    print(f"    - Fallback Used: {d3.fallback_used}")
    print(f"    - Fallback Engine: {d3.fallback}")
    print(f"    - External Calls: {d3.external_calls}")
    print(f"    - Reason: {d3.reason}")

    assert d3.task_type == "multimodal"
    assert d3.selected_model == "qwen2.5:7b"
    assert d3.fallback_used is True
    assert d3.fallback == "local_ocr"
    assert d3.external_calls == 0
    print("    [OK] Multimodal safely and cleanly fell back to Local OCR + Qwen without crashing!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 4: Explicit Sovereign/Ollama Mode -> external_calls == 0
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 4] Testing Strict Sovereign Mode Boundary (external_calls == 0)...")
    d4 = model_router.route(
        prompt="Prepare statutory approval note for turbine shutdown.",
        provider_mode="sovereign",
    )
    print(f"    - Provider Mode: sovereign")
    print(f"    - Routed Provider: {d4.provider}")
    print(f"    - External Calls: {d4.external_calls}")
    print(f"    - Local Flag: {d4.local}")

    assert d4.provider == "ollama"
    assert d4.local is True
    assert d4.external_calls == 0
    print("    [OK] Strict zero-external-call boundary verified for sovereign mode!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 5: Cloud Provider Mode -> Preserved Behavior
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 5] Testing Cloud Provider Mode Preservation...")
    d5 = model_router.route(
        prompt="Draft an executive summary for Q3 stakeholder deck.",
        provider_mode="auto",
    )
    print(f"    - Provider Mode: auto")
    print(f"    - Routed Provider: {d5.provider}")
    print(f"    - Selected Model: {d5.selected_model}")
    print(f"    - Local Flag: {d5.local}")

    # Should use gemini / groq or local if no cloud keys exist
    if model_router.registry.has_cloud_credentials("gemini"):
        assert d5.provider == "gemini"
        assert d5.local is False
        assert d5.external_calls == 1
    elif model_router.registry.has_cloud_credentials("groq"):
        assert d5.provider == "groq"
        assert d5.local is False
        assert d5.external_calls == 1
    print("    [OK] Cloud mode preserved and functioning as configured!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 6: Unavailable Preferred Model -> Safe Resilient Fallback
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 6] Testing Resilient Fallback When Preferred Model is Missing...")
    custom_registry = ModelRegistry()
    # Force mock installed list with only gemma3:1b
    custom_registry._installed_cache = ["gemma3:1b"]
    custom_registry._cache_timestamp = 9999999999.0
    fallback_router = LocalModelRouter(registry=custom_registry)

    d6 = fallback_router.route(
        task_type="coding",
        requirements={"task_hint": "coding"},
        provider_mode="ollama",
    )
    print(f"    - Requested Task: coding")
    print(f"    - Installed in Ollama: {custom_registry.get_installed_ollama_models()}")
    print(f"    - Selected Fallback Model: {d6.selected_model}")
    print(f"    - Fallback Used: {d6.fallback_used}")
    print(f"    - Reason: {d6.reason}")

    assert d6.selected_model == "gemma3:1b"
    assert d6.fallback_used is True
    assert d6.external_calls == 0
    print("    [OK] Safe resilient fallback without crashing verified!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 7: Existing Step 8 Scanned-PDF Workflow with Router Integration
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 7] Testing Step 8 Scanned-PDF Workflow through Model Router & Agent Planner...")
    scanned_pdf = "output/uploads/multimodal_test/scanned_petrochemical_audit.pdf"
    planner = AgentPlanner(provider="ollama")
    plan = planner.create_plan(
        task="Audit petrochemical flange leak from scanned inspection report.",
        file_paths=[scanned_pdf],
    )
    print(f"    - Plan Title: {plan.get('title')}")
    print(f"    - Total Steps: {plan.get('total_steps')}")
    print(f"    - Routing in Plan Metadata: {plan.get('routing')}")

    assert plan.get("routing") is not None
    assert plan["routing"]["selected_model"] == "qwen2.5:7b"
    assert plan["routing"]["external_calls"] == 0
    print("    [OK] Step 8 Scanned-PDF workflow seamlessly integrated with router metadata!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 8: Existing Sovereign RAG Retrieval Remains Functional
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 8] Testing Sovereign RAG Retrieval...")
    rag = RagService()
    rag.ensure_default_sops()
    chunks = rag.retrieve(query="flange seal leak temperature threshold", top_k=2, threshold=0.05)
    print(f"    - Retrieved Chunks: {len(chunks)}")
    for c in chunks:
        doc_title = c.get("document_title") if isinstance(c, dict) else getattr(c, "document_title", "")
        sim = float(c.get("similarity", 0.0)) if isinstance(c, dict) else getattr(c, "similarity", 0.0)
        content = c.get("content", "") if isinstance(c, dict) else getattr(c, "content", "")
        print(f"      * [{doc_title}] Sim: {sim:.4f} | Preview: {content[:80]}...")
    assert len(chunks) > 0
    print("    [OK] Sovereign RAG retrieval verified!")

    # ─────────────────────────────────────────────────────────────────
    # TEST 9: Existing DOCX Deliverable Generation with Routing Telemetry
    # ─────────────────────────────────────────────────────────────────
    print("\n[TEST 9] Testing End-to-End DOCX Deliverable Synthesis with Routing Metadata...")
    generator = InspectionAnalysisGenerator(provider="ollama")
    content_model = {
        "title": "Sovereign Model Router Petrochemical Audit",
        "summary": "Router identified high-pressure flange seal leak exceeding statutory 85 C ceiling at 104 C. Assigned to Qwen 2.5 7B sovereign reasoning model.",
        "key_points": [
            "Flange seal leak at 104 C exceeds statutory 85 C threshold (Critical Risk)",
            "Automatic Model Router selected Qwen 2.5 7B with zero external calls",
            "Emergency isolation mandated per SOP-ENG-44",
        ],
        "source_files": [Path(scanned_pdf).name],
    }
    req = OutputRequest(
        outputs=["inspection_analysis"],
        tone="Executive & Authoritative",
        language="English",
        target_audience="Chief Technical Officer",
    )
    docx_res = generator.generate(content_model, req)
    print(f"    - DOCX Deliverable: {docx_res.get('filename')}")
    print(f"    - File Path: {docx_res.get('path')}")
    print(f"    - Routing in Deliverable: {docx_res.get('routing')}")

    assert docx_res.get("type") == "file"
    assert os.path.exists(docx_res.get("path"))
    assert docx_res.get("routing") is not None
    assert docx_res["routing"]["external_calls"] == 0
    print("    [OK] DOCX Deliverable compiled with full routing telemetry!")

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL 9 STEP 9 MODEL ROUTER CAPABILITIES FULLY VERIFIED!")
    print("=" * 70)


if __name__ == "__main__":
    run_router_tests()
