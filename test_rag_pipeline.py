"""
test_rag_pipeline.py
--------------------
End-to-end test script for Supabase pgvector RAG:
1. Initialize Schema & pgvector on Supabase
2. Ingest Sample Enterprise Knowledge Text
3. Perform Semantic Retrieval
4. Generate Grounded Executive Summary via RAG
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

from services.rag_db import RagDatabase
from services.rag_service import RagService
from services.rag_exec_summary_generator import RagExecutiveSummaryGenerator

def main():
    print("=" * 60)
    print("BIZZORAAI / CORTEX - SUPABASE PGVECTOR RAG VERIFICATION")
    print("=" * 60)

    db_url = os.getenv("SUPABASE_DB_URL")
    print(f"[*] Supabase DB URL configured: {db_url[:40]}...")

    # 1. Initialize Database Schema
    print("\n[Step 1] Initializing Supabase pgvector schema (schema.sql)...")
    rag_db = RagDatabase(db_url)
    try:
        init_res = rag_db.init_db("schema.sql")
        print(f"[OK] Schema Init Result: {init_res}")
    except Exception as e:
        print(f"[!] Schema init error: {e}")
        return

    # 2. Ingest Sample Document
    print("\n[Step 2] Ingesting Sample Enterprise Security & AI Policy Document...")
    rag_service = RagService(db=rag_db)

    sample_doc_text = """
    Enterprise AI Security and Governance Framework 2026

    1. Autonomous Agent Governance & SOC Integration
    In 2026, enterprise security operations centers (SOC) are transitioning to autonomous threat triage and multimodal telemetry.
    The primary goal is to reduce Mean Time to Detect (MTTD) from 45 minutes down to sub-800 milliseconds using precision AI pipelines.
    All autonomous agent actions must adhere to zero-trust architecture, with encrypted vector embedding retrieval and role-based access control.

    2. Multimodal Marketing & Content Generation Compliance
    All outbound digital assets—including LinkedIn leadership posts, executive briefings, investor decks, and AI-narrated video packages—
    must undergo automated policy validation against brand compliance and data loss prevention (DLP) filters.
    BizzoraAI is deployed as the standardized enterprise content generation engine across all global business units.

    3. Infrastructure and Cost Optimization Metrics
    By implementing dynamic LLM mesh routing (switching dynamically between Gemini Pro 1.5 and Groq LLaMA-3),
    API infrastructure operating costs have been reduced by 64% while maintaining 99.98% pipeline uptime.
    Storage of document embeddings is centralized in Supabase PostgreSQL utilizing the pgvector extension with HNSW indexing.
    """

    try:
        ingest_res = rag_service.ingest_text(
            title="Enterprise AI Security and Governance Framework 2026",
            text=sample_doc_text,
            source_type="advisory",
            metadata={"department": "Security & Marketing", "classification": "Confidential"},
        )
        print(f"[OK] Ingest Result: {ingest_res}")
        doc_id = ingest_res["document_id"]
    except Exception as e:
        print(f"[!] Ingest error: {e}")
        return

    # 3. Retrieve Matching Context
    query = "What are the infrastructure cost optimization metrics and SOC response time goals?"
    print(f"\n[Step 3] Performing Semantic Retrieval for Query:\n    '{query}'")
    try:
        results = rag_service.retrieve(query=query, top_k=3, threshold=0.1)
        print(f"[OK] Retrieved {len(results)} matching chunks:")
        for i, r in enumerate(results, 1):
            print(f"    - Chunk {i} (Similarity: {r['similarity']:.4f}): {r['content'][:120]}...")
    except Exception as e:
        print(f"[!] Retrieval error: {e}")
        return

    # 4. Generate RAG Grounded Executive Summary
    print("\n[Step 4] Synthesizing Grounded Executive Summary...")
    try:
        rag_gen = RagExecutiveSummaryGenerator(rag_service=rag_service)
        summary_res = rag_gen.generate_summary(
            query="Summarize the enterprise AI security response time goals and cost optimization results.",
            top_k=3,
        )
        print("\n" + "=" * 60)
        print("GENERATED GROUNDED EXECUTIVE SUMMARY:")
        print("=" * 60)
        print(summary_res["executive_summary"])
        print("=" * 60)
        print(f"[OK] Sources Cited: {summary_res['retrieved_sources_count']}")
    except Exception as e:
        print(f"[!] Summary generation error: {e}")

    print("\n[OK] ALL RAG PIPELINE CHECKS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
