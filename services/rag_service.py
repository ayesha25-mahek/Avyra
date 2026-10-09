"""
services/rag_service.py
-----------------------
Core RAG orchestration service:
- Smart text chunking (paragraph & sentence aware)
- Document & File ingestion into Supabase pgvector
- Semantic vector retrieval with similarity scores
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.embeddings_provider import EmbeddingsProvider
from services.rag_db import RagDatabase
from services.document_reader import DocumentReader

logger = logging.getLogger(__name__)


class RagService:
    """End-to-end RAG operations for BizzoraAI / aiAdGen."""

    def __init__(
        self,
        db: Optional[RagDatabase] = None,
        embeddings: Optional[EmbeddingsProvider] = None,
    ):
        self.db = db or RagDatabase()
        self.embeddings = embeddings or EmbeddingsProvider()
        self.doc_reader = DocumentReader()

    # -----------------------------------------------------------------------
    # Chunking Strategy
    # -----------------------------------------------------------------------
    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
    ) -> List[str]:
        """
        Split text into overlapping semantic chunks respecting paragraphs and sentence boundaries.
        chunk_size: approximate character length of each chunk.
        chunk_overlap: approximate character overlap between consecutive chunks.
        """
        if not text or not text.strip():
            return []

        # Split into logical paragraphs or double-newlines
        raw_paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for para in raw_paragraphs:
            para_len = len(para)

            # If a single paragraph is larger than chunk_size, split by sentences
            if para_len > chunk_size:
                sentences = re.split(r'(?<=[.?!])\s+', para)
                for sent in sentences:
                    sent_len = len(sent)
                    if current_len + sent_len > chunk_size and current_chunk:
                        chunk_str = " ".join(current_chunk).strip()
                        if chunk_str:
                            chunks.append(chunk_str)
                        # Keep overlap if possible
                        overlap_chunk = []
                        overlap_len = 0
                        for prev_s in reversed(current_chunk):
                            if overlap_len + len(prev_s) <= chunk_overlap:
                                overlap_chunk.insert(0, prev_s)
                                overlap_len += len(prev_s)
                            else:
                                break
                        current_chunk = overlap_chunk
                        current_len = overlap_len

                    current_chunk.append(sent)
                    current_len += sent_len
            else:
                if current_len + para_len > chunk_size and current_chunk:
                    chunk_str = "\n\n".join(current_chunk).strip()
                    if chunk_str:
                        chunks.append(chunk_str)
                    current_chunk = []
                    current_len = 0

                current_chunk.append(para)
                current_len += para_len

        # Append trailing chunk
        if current_chunk:
            chunk_str = "\n\n".join(current_chunk).strip()
            if chunk_str:
                chunks.append(chunk_str)

        return chunks

    # -----------------------------------------------------------------------
    # Ingestion: Raw Text
    # -----------------------------------------------------------------------
    def ingest_text(
        self,
        title: str,
        text: str,
        source_type: str = "text",
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
    ) -> Dict[str, Any]:
        """Ingest raw text into Supabase pgvector."""
        if not text.strip():
            raise ValueError("Input text is empty.")

        meta = metadata or {}
        chunks = self.chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        if not chunks:
            raise ValueError("No chunks could be extracted from input text.")

        logger.info("Ingesting document '%s' (%d chunks)...", title, len(chunks))

        # 1. Insert parent document record
        doc_id = self.db.insert_document(
            title=title,
            source_type=source_type,
            filename=filename,
            file_size=len(text.encode("utf-8")),
            total_chunks=len(chunks),
            metadata=meta,
        )

        # 2. Generate embeddings in batch
        embeddings = self.embeddings.embed_batch(chunks)

        # 3. Prepare chunk payload
        chunks_data = [
            {
                "chunk_index": idx,
                "content": chunk,
                "token_count": len(chunk.split()),
                "embedding": emb,
                "metadata": {**meta, "chunk_index": idx},
            }
            for idx, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]

        # 4. Insert chunks into pgvector
        inserted_count = self.db.insert_chunks(doc_id, chunks_data)

        logger.info("Document '%s' successfully ingested with ID: %s", title, doc_id)
        return {
            "document_id": doc_id,
            "title": title,
            "chunks_count": inserted_count,
            "status": "indexed",
        }

    # -----------------------------------------------------------------------
    # Ingestion: File (PDF, DOCX, PPTX, TXT)
    # -----------------------------------------------------------------------
    def ingest_file(
        self,
        file_path: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Read a file on disk, extract text, and index it into Supabase pgvector."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found at '{path}'")

        doc_title = title or path.stem.replace("_", " ").title()
        ext = path.suffix.lower().lstrip(".")

        # Extract text via DocumentReader (supports native PDF, scanned PDF via local OCR, images, DOCX, TXT, PPTX)
        meta_res = self.doc_reader.read_with_metadata(str(path))
        extracted_text = meta_res["text"]
        source_type = meta_res.get("source_type", ext)

        meta = metadata or {}
        meta["filename"] = path.name
        meta["file_extension"] = ext
        meta["file_size_bytes"] = path.stat().st_size
        meta["processing"] = meta_res.get("processing", "native_text_extraction")
        meta["model_provider"] = "local"
        meta["external_calls"] = 0

        return self.ingest_text(
            title=doc_title,
            text=extracted_text,
            source_type=source_type,
            filename=path.name,
            metadata=meta,
        )

    # -----------------------------------------------------------------------
    # Retrieval
    # -----------------------------------------------------------------------
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.15,
        filter_doc_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search against Supabase pgvector for top-k matching chunks."""
        if not query.strip():
            return []

        # 1. Embed query
        query_vector = self.embeddings.embed_text(query)

        # 2. Search database
        results = self.db.search_chunks(
            query_embedding=query_vector,
            top_k=top_k,
            threshold=threshold,
            filter_doc_id=filter_doc_id,
        )

        return results

    def format_context_for_llm(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into a clean grounded context string for LLM prompting."""
        if not retrieved_chunks:
            return "No relevant context found in knowledge base."

        context_blocks = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            source = chunk.get("document_title") or chunk.get("filename") or f"Doc {chunk.get('document_id', '')[:8]}"
            similarity = chunk.get("similarity", 0.0)
            context_blocks.append(
                f"[Source {i}: {source} (Relevance: {similarity:.2f})]\n{chunk['content']}"
            )

        return "\n\n---\n\n".join(context_blocks)

    def ensure_default_sops(self) -> int:
        """
        Seed standard organizational SOPs and compliance manuals if the knowledge base is empty.
        Ensures sovereign on-premise inspection and risk analysis workflows are immediately grounded.
        """
        docs = self.db.list_documents(limit=1)
        if docs:
            return 0  # Knowledge base already has documents

        logger.info("RagService: Seeding baseline sovereign organizational SOPs and compliance standards...")
        count = 0

        # SOP 1: Incident response & phishing triage
        sop_phishing = (
            "SOP-SEC-402: Enterprise Phishing Triage, Containment & Administrative System Hardening Standard\n\n"
            "1. PURPOSE & APPLICABILITY:\n"
            "This Standard Operating Procedure governs mandatory containment protocols when coordinated phishing campaigns, "
            "credential harvesting portals, or unauthorized administrative credential submissions are detected.\n\n"
            "2. MANDATORY CONTAINMENT ACTIONS:\n"
            "- Tier-1 Immediate Revocation: All targeted user sessions and active JWT / OAuth tokens must be invalidated within 30 minutes of detection.\n"
            "- Privileged Access Reset: Any account possessing internal administrative system or root privileges must undergo mandatory credential reset.\n"
            "- Multi-Factor Authentication: FIDO2 hardware token or phishing-resistant authenticator app enforcement must be activated immediately.\n"
            "- Network Perimeter Defense: Malicious sender domains, fraudulent login URLs, and phishing relay IPs must be added to enterprise firewall and MTA blocklists within 15 minutes.\n"
            "- Forensic Endpoint Isolation: Any workstation that submitted credentials to a spoofed page must be placed in network isolation for endpoint detection and response (EDR) memory triage.\n\n"
            "3. REGULATORY NOTIFICATION:\n"
            "Preliminary incident notification must be submitted to the Chief Information Security Officer (CISO) and Compliance Officer within 2 hours of confirmation.\n\n"
            "4. SIGN-OFF CRITERIA:\n"
            "An incident report may only receive final clearance if all exposed credentials have been verified revoked and no unauthorized administrative lateral movement is detected."
        )
        self.ingest_text(
            title="SOP-SEC-402: Enterprise Phishing Triage & Containment Standard",
            text=sop_phishing,
            source_type="sop",
            metadata={"category": "Cybersecurity", "standard_id": "SOP-SEC-402", "classification": "Internal SOP"},
        )
        count += 1

        # SOP 2: Technical inspection audit & approval governance
        sop_audit = (
            "SOP-INSP-001: Sovereign Technical Infrastructure Inspection & Approval Note Governance Standard\n\n"
            "1. PURPOSE & SCOPE:\n"
            "Defines the rigorous evaluation criteria required to issue formal inspection approval notes, conditional clearances, or audit rejections across enterprise facilities and digital infrastructure.\n\n"
            "2. RISK & DEFECT SEVERITY CLASSIFICATION:\n"
            "- Critical Severity: Direct risk of data breach, safety hazard, unauthenticated administrative access, or systemic process disruption. Requires immediate executive escalation.\n"
            "- High Severity: Absence of redundancy, overdue security patches, or non-compliance with statutory safety controls. Remediation required within 24-48 hours.\n"
            "- Medium Severity: Operational friction, procedural drift, or partial compliance gaps. Remediate within 14 calendar days.\n"
            "- Low Severity: Cosmetic findings, documentation enhancements, or routine maintenance advisory observations.\n\n"
            "3. SIGN-OFF DETERMINATION RULES:\n"
            "- APPROVED: Permitted only when all critical and high findings have verified zero-risk status or completed corrective containment.\n"
            "- CONDITIONAL APPROVAL: Permitted if high/critical risks have verified temporary mitigations and an irrevocable corrective action plan is binding within 7 business days.\n"
            "- REJECTION: Mandatory if unmitigated critical exposures, active exploitation, or compromised administrative credentials remain unresolved.\n\n"
            "4. MULTI-AGENT VERIFICATION TRAIL:\n"
            "All autonomous inspection dossiers must preserve an indelible 7-stage agent audit trail verifying source ingestion, finding extraction, risk calculation, knowledge base cross-referencing, recommendation mapping, deliverable synthesis, and compliance verification."
        )
        self.ingest_text(
            title="SOP-INSP-001: Sovereign Technical Infrastructure Inspection & Approval Note Governance Standard",
            text=sop_audit,
            source_type="sop",
            metadata={"category": "Audit & Compliance", "standard_id": "SOP-INSP-001", "classification": "Governance Standard"},
        )
        count += 1

        # SOP 3: ISO/IEC 27001 & NIST SP 800-61 Protocol
        sop_iso = (
            "ISO/IEC 27001 & NIST SP 800-61 Rev 2: Incident Management & Evidence Preservation Protocol\n\n"
            "1. SCOPE:\n"
            "Mandates international best-practice procedures for incident classification, evidence preservation, and operational security verification.\n\n"
            "2. CONTROL REQUIREMENTS (Clause A.12 & A.16):\n"
            "- A.12.1 Operational Procedures: Documented operating procedures must be maintained for all critical information processing facilities.\n"
            "- A.12.6 Management of Technical Vulnerabilities: Timely information regarding technical vulnerabilities must be obtained and evaluated with appropriate mitigation.\n"
            "- A.16.1 Information Security Incident Management: Ensure consistent and effective approach to the life cycle management of incidents.\n\n"
            "3. EVIDENCE PRESERVATION & CHAIN OF CUSTODY:\n"
            "All email logs, packet captures, and user authentication tokens must be cryptographically hashed and archived prior to remediation to ensure legal chain-of-custody validity."
        )
        self.ingest_text(
            title="ISO/IEC 27001 & NIST SP 800-61: Incident Management Protocol",
            text=sop_iso,
            source_type="compliance",
            metadata={"category": "International Standards", "standard_id": "ISO-27001-NIST-800", "classification": "Regulatory Standard"},
        )
        count += 1

        logger.info("RagService: Successfully seeded %d sovereign SOP documents into local RAG.", count)
        return count
