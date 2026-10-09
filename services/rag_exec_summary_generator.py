"""
services/rag_exec_summary_generator.py
--------------------------------------
RAG-Powered Executive Summary Generator.
Retrieves relevant knowledge chunks from Supabase pgvector and synthesizes
an executive briefing grounded in verified source facts with citations.
"""

import logging
from typing import Any, Dict, List, Optional
from services.llm_pool import LLMPool
from services.rag_service import RagService

logger = logging.getLogger(__name__)


class RagExecutiveSummaryGenerator:
    """Generates grounded Executive Summaries using RAG + pgvector retrieval."""

    def __init__(
        self,
        llm: Optional[LLMPool] = None,
        rag_service: Optional[RagService] = None,
    ):
        self.llm = llm or LLMPool()
        self.rag = rag_service or RagService()

    def generate_summary(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.15,
        filter_doc_id: Optional[str] = None,
        tone: str = "Executive & Authoritative",
        target_audience: str = "C-Suite Executives",
    ) -> Dict[str, Any]:
        """
        1. Query pgvector for relevant context chunks.
        2. Format grounded prompt with source citations.
        3. Invoke LLMPool to generate executive briefing.
        """
        logger.info("Generating RAG Executive Summary for query: '%s'", query)

        # 1. Semantic vector retrieval
        retrieved_chunks = self.rag.retrieve(
            query=query,
            top_k=top_k,
            threshold=threshold,
            filter_doc_id=filter_doc_id,
        )

        context_text = self.rag.format_context_for_llm(retrieved_chunks)

        # 2. Grounded system & user prompts
        system_prompt = (
            "You are an elite Enterprise AI Strategic Advisor. "
            "You write concise, authoritative, high-impact Executive Summaries grounded strictly in provided knowledge sources. "
            "Always include: Executive Overview, Key Strategic Takeaways, Business / Operational Impact, and Actionable Recommendations. "
            "Cite sources where relevant (e.g. [Source 1]). Do not hallucinate outside the retrieved facts."
        )

        user_prompt = f"""
# STRATEGIC EXECUTIVE BRIEFING REQUEST

## TOPIC / QUERY:
{query}

## TARGET AUDIENCE:
{target_audience}

## TONE:
{tone}

## RETRIEVED KNOWLEDGE BASE CONTEXT (From Supabase pgvector):
{context_text}

---

Please produce a comprehensive, structured Executive Summary in clean Markdown format:
1. **EXECUTIVE OVERVIEW**: High-level synthesis answering the query.
2. **KEY STRATEGIC FINDINGS**: 3-5 bulleted core points backed by the source data.
3. **STRATEGIC & OPERATIONAL IMPACT**: Financial, technical, or organizational implications.
4. **RECOMMENDED ACTION PLAN**: Immediate and next-phase tactical recommendations.
"""

        # 3. Generate via LLM Pool
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        generated_content = self.llm.generate(
            prompt=full_prompt,
            temperature=0.3, # low temperature for high precision grounding
        )

        sources_metadata = [
            {
                "id": c.get("id"),
                "document_id": c.get("document_id"),
                "document_title": c.get("document_title"),
                "chunk_index": c.get("chunk_index"),
                "similarity": c.get("similarity"),
                "snippet": c.get("content", "")[:180] + "...",
            }
            for c in retrieved_chunks
        ]

        return {
            "query": query,
            "executive_summary": generated_content,
            "retrieved_sources_count": len(retrieved_chunks),
            "sources": sources_metadata,
        }
