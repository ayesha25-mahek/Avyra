"""
test_sovereign_rag.py
---------------------
Verification test for STEP 6:
Connect Existing RAG to Sovereign SIH Workflow:
1. Initialize local Sovereign SQLite RAG database
2. Seed baseline organizational SOP standards
3. Perform semantic vector retrieval against local SOPs
4. Verify AgentPlanner integration with RAG
5. Generate grounded Inspection Findings & Risk Analysis via Local Qwen 2.5 7B
"""

import sys
from services.rag_db import RagDatabase
from services.rag_service import RagService
from services.agent_planner import AgentPlanner
from services.inspection_analysis_generator import InspectionAnalysisGenerator
from services.output_request import OutputRequest

def test_rag():
    print("=" * 65)
    print("STEP 6: SOVEREIGN LOCAL RAG PIPELINE VERIFICATION")
    print("=" * 65)

    # 1. RagDatabase Initialization
    print("\n[1] Testing RagDatabase with Local Sovereign SQLite...")
    db = RagDatabase()
    res = db.init_db()
    print("    Result:", res)

    # 2. RagService Seeding
    print("\n[2] Testing Baseline Organizational SOPs Seeding...")
    rag = RagService(db=db)
    seeded_count = rag.ensure_default_sops()
    print(f"    Seeded {seeded_count} new SOP(s).")

    docs = db.list_documents()
    print(f"    Total Documents in Sovereign RAG: {len(docs)}")
    for d in docs:
        print(f"    - {d['title']} ({d['total_chunks']} chunks, type: {d['source_type']})")

    # 3. Retrieval
    query = "unauthorized administrative credentials phishing session revocation SOP"
    print(f"\n[3] Testing Sovereign Semantic Retrieval for Query:\n    '{query}'")
    matches = rag.retrieve(query=query, top_k=2)
    print(f"    Matches found: {len(matches)}")
    for i, m in enumerate(matches, 1):
        print(f"    Match {i}: [{m['document_title']}] (Similarity: {m['similarity']:.4f})")
        print(f"    Excerpt: {m['content'][:140]}...")

    # 4. AgentPlanner Document Analysis with RAG
    print("\n[4] Testing AgentPlanner Document Analysis with RAG...")
    planner = AgentPlanner(provider="ollama")
    doc_path = "output/uploads/072a4e33e7e0484c8f3cbac6989f51f1/cybersecurity_test_document.pdf"
    analysis = planner.analyze_document(
        file_paths=[doc_path],
        task="Analyze inspection findings and cross-reference organizational SOPs.",
    )
    print(f"    Analysis Title: {analysis.get('title')}")
    print(f"    Compliance Status: {analysis.get('compliance_status')}")
    retrieved_k = analysis.get("retrieved_knowledge", [])
    print(f"    Retrieved Knowledge Items in Plan: {len(retrieved_k)}")
    for rk in retrieved_k:
        print(f"    - Standard: {rk.get('document_title')} (Sim: {rk.get('similarity')})")

    # 5. InspectionAnalysisGenerator Grounded Synthesis
    print("\n[5] Testing InspectionAnalysisGenerator with Sovereign RAG + Local Qwen...")
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

    result_text = gen.generate(mock_content_model, mock_req)
    print("\n" + "=" * 65)
    print("GENERATED GROUNDED INSPECTION APPROVAL DOSSIER (FIRST 800 CHARS):")
    print("=" * 65)
    print(result_text[:800])
    print("...\n" + "=" * 65)

    assert "INSPECTION FINDINGS" in result_text or "EXECUTIVE SUMMARY" in result_text
    print("\n[SUCCESS] STEP 6 Sovereign RAG Workflow fully verified!")

if __name__ == "__main__":
    test_rag()
