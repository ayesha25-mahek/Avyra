"""
services/agent_planner.py
-------------------------
Agent Planner Layer for Avyara Sovereign AI Workbench.

Deconstructs complex enterprise directives (e.g., analyzing inspection reports,
generating approval notes, compliance reviews) into an executable multi-step
plan using the local sovereign Ollama / Qwen2.5 model.
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from services.document_reader import DocumentReader
from services.llm_pool import LLMPool, OLLAMA_MODEL
from services.model_router import model_router
from services.agent_tool_executor import AgentToolExecutor

logger = logging.getLogger(__name__)


class AgentPlanner:
    """
    Sovereign Agent Planner that decomposes directives, executes local tools,
    and produces verified enterprise deliverables.
    Powered by local Ollama (qwen2.5:7b) and LocalToolRegistry.
    """

    def __init__(self, provider: str = "ollama") -> None:
        self.provider = provider
        self.llm = LLMPool(preferred_provider=provider)
        self.document_reader = DocumentReader()
        from services.rag_service import RagService
        self.rag_service = RagService()
        self.tool_executor = AgentToolExecutor(provider=provider)

    def read_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Reuses existing DocumentReader to parse and extract text from uploaded files (PDF, DOCX, TXT, PPTX).
        """
        extracted: List[Dict[str, Any]] = []
        for path_str in file_paths:
            p = Path(path_str)
            if not p.exists():
                logger.warning("DocumentReader: File not found at '%s'", path_str)
                continue
            try:
                meta = self.document_reader.read_with_metadata(str(p))
                extracted.append({
                    "path": str(p),
                    "filename": p.name,
                    "extension": p.suffix.lower(),
                    "size_bytes": p.stat().st_size,
                    "text": meta["text"],
                    "char_count": len(meta["text"]),
                    "source_type": meta.get("source_type", "document"),
                    "processing": meta.get("processing", "native_text_extraction"),
                    "external_calls": 0,
                    "model_provider": "local",
                    "details": meta.get("details", {}),
                })
                logger.info(
                    "DocumentReader: Processed '%s' (%d chars) | source_type: %s | processing: %s | external_calls: 0",
                    p.name,
                    len(meta["text"]),
                    meta.get("source_type"),
                    meta.get("processing"),
                )
            except Exception as exc:
                logger.warning("DocumentReader failed on '%s': %s", path_str, exc)
        return extracted

    def create_plan(
        self,
        task: str,
        context: Optional[str] = "",
        custom_instructions: Optional[str] = "",
        file_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Produce a structured multi-step execution plan for the given task.
        If file_paths are provided, reuses DocumentReader to ingest documents and ground the plan.
        """
        task_clean = (task or "").strip()
        if not task_clean:
            raise ValueError("Task description cannot be empty.")

        docs_info = []
        if file_paths:
            docs_info = self.read_documents(file_paths)
            doc_context = "\n\n".join(
                [f"--- DOCUMENT: {d['filename']} ---\n{d['text'][:4000]}" for d in docs_info]
            )
            context = f"{context}\n\nINGESTED DOCUMENTS:\n{doc_context}" if context else f"INGESTED DOCUMENTS:\n{doc_context}"

        # Dynamic Model Router Selection
        file_path_strs = [d["path"] for d in docs_info] if docs_info else (file_paths or [])
        decision = model_router.route(
            prompt=task_clean,
            provider_mode=self.provider,
            files=file_path_strs,
        )

        prompt = self._build_prompt(task_clean, context or "", custom_instructions or "")
        logger.info(
            "AgentPlanner: Planning task using %s (routed model: %s, attached docs: %d)...",
            self.provider,
            decision.selected_model,
            len(docs_info),
        )

        try:
            raw_response = self.llm.generate(prompt, model=decision.selected_model)
            plan_data = self._parse_json_response(raw_response)
        except Exception as exc:
            logger.warning(
                "AgentPlanner: LLM output parsing failed (%s), constructing resilient fallback plan.",
                exc,
            )
            plan_data = self._fallback_plan(task_clean)

        result = self._normalize_plan(task_clean, plan_data)
        result["routing"] = decision.to_dict()
        if docs_info:
            result["documents"] = [
                {"filename": d["filename"], "extension": d["extension"], "char_count": d["char_count"]}
                for d in docs_info
            ]
        return result

    def execute_task(
        self,
        task: str,
        file_paths: Optional[List[str]] = None,
        output_format: str = "docx",
        custom_instructions: str = "",
        on_step_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Full autonomous tool execution loop:
        1. Formulates structured execution plan.
        2. Steps through plan sequentially calling local tools in LocalToolRegistry.
        3. Observes outcomes and adapts state.
        4. Compiles publication deliverable (.docx or .pptx).
        5. Verifies deliverable integrity.
        6. Returns final result with 100% sovereign telemetry (external_calls: 0).
        """
        task_clean = (task or "").strip()
        if not task_clean:
            raise ValueError("Task cannot be empty.")

        # Stage 1: Generate tactical plan
        plan = self.create_plan(
            task=task_clean,
            file_paths=file_paths,
            custom_instructions=custom_instructions,
        )

        # Stage 2: Execute plan via Local Tool Engine
        summary = self.tool_executor.execute_plan(
            task=task_clean,
            plan_steps=plan.get("steps", []),
            file_paths=file_paths,
            output_format=output_format,
            custom_instructions=custom_instructions,
            on_step_callback=on_step_callback,
        )

        from services.sovereignty_monitor import sovereignty_monitor
        return {
            "status": summary.execution_status,
            "execution_status": summary.execution_status,
            "verification_status": summary.verification_status,
            "task": task_clean,
            "plan": plan,
            "execution_summary": summary.to_dict(),
            "final_artifact": summary.final_artifact,
            "tools_executed": summary.tools_executed,
            "external_calls": summary.external_calls,
            "confidentiality": sovereignty_monitor.get_confidentiality_metadata(),
            "telemetry": {
                "task_type": summary.task_type,
                "selected_model": summary.selected_model,
                "provider": summary.provider,
                "total_tool_calls": summary.total_tool_calls,
                "iterations": summary.iterations,
                "external_calls": summary.external_calls,
                "local_execution": summary.local_execution,
                "tools_executed": summary.tools_executed,
            },
        }

    def execute_coding_task(
        self,
        task: str,
        input_files: Optional[List[str]] = None,
        expected_output_file: Optional[str] = None,
        custom_instructions: Optional[str] = "",
        max_attempts: int = 3,
    ) -> Dict[str, Any]:
        """
        Executes a dedicated Python coding task inside the secure local sandbox
        with autonomous diagnosis, iterative bugfixing, and artifact verification.
        """
        return self.tool_executor.execute_coding_task(
            task=task,
            input_files=input_files,
            expected_output_file=expected_output_file,
            custom_instructions=custom_instructions,
            max_attempts=max_attempts,
        )

    def analyze_document(
        self,
        file_paths: Union[str, List[str]],
        task: Optional[str] = None,
        custom_instructions: Optional[str] = "",
    ) -> Dict[str, Any]:
        """
        Workflow:
        Existing Upload -> Existing DocumentReader -> Agent Planner -> Local Ollama/Qwen -> Structured Analysis
        """
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        docs_info = self.read_documents(file_paths)
        if not docs_info:
            raise ValueError("No readable document content could be extracted from the provided files.")

        combined_text = "\n\n".join(
            [f"--- DOCUMENT: {d['filename']} ---\n{d['text']}" for d in docs_info]
        )
        task_directive = (
            task.strip()
            if task and task.strip()
            else "Analyze this document, extract key findings and risks, and prepare an approval note plan."
        )

        # Dynamic Model Router Selection
        file_path_strs = [d["path"] for d in docs_info]
        decision = model_router.route(
            prompt=task_directive,
            provider_mode=self.provider,
            files=file_path_strs,
        )

        # Retrieve relevant organizational SOPs via existing Sovereign RAG
        rag_query = f"{task_directive} {combined_text[:300]}"
        retrieved_knowledge = []
        rag_context = ""
        try:
            retrieved_knowledge = self.rag_service.retrieve(query=rag_query, top_k=3, threshold=0.05)
            rag_context = self.rag_service.format_context_for_llm(retrieved_knowledge)
        except Exception as exc:
            logger.warning("AgentPlanner: RAG retrieval failed: %s", exc)

        prompt = self._build_document_prompt(task_directive, combined_text, custom_instructions or "", rag_context)
        logger.info(
            "AgentPlanner: Analyzing %d document(s) with %s (routed model: %s, RAG matches: %d)...",
            len(docs_info),
            self.provider,
            decision.selected_model,
            len(retrieved_knowledge),
        )

        try:
            raw_response = self.llm.generate(prompt, model=decision.selected_model)
            parsed = self._parse_json_response(raw_response)
        except Exception as exc:
            logger.warning("AgentPlanner: Document analysis LLM parse failed (%s), using fallback.", exc)
            parsed = self._fallback_document_analysis(task_directive, docs_info)

        res = self._normalize_document_analysis(task_directive, docs_info, parsed, retrieved_knowledge)
        res["routing"] = decision.to_dict()
        return res

    def _build_prompt(self, task: str, context: str, instructions: str) -> str:
        return f"""You are the Sovereign Agent Planner of Avyara Enterprise Workbench.

Your objective is to analyze the enterprise directive below and decompose it into an ordered, tactical multi-step execution plan.

TASK DIRECTIVE:
{task}

OPTIONAL CONTEXT:
{context if context else "None provided."}

ADDITIONAL INSTRUCTIONS:
{instructions if instructions else "Follow standard sovereign inspection & approval workflows."}

RULES:
1. Deconstruct the task into logical, sequential steps.
2. Typical workflows should include steps such as:
   - Read document
   - Extract findings
   - Identify risks
   - Search relevant knowledge
   - Prepare recommendation
   - Generate requested deliverable
   - Verify result
3. Map each step to the appropriate system service or tool:
   - 'document_reader' for document ingestion & extraction
   - 'content_intelligence' for findings, risks, and entity extraction
   - 'rag_service' for searching relevant enterprise policies and knowledge bases
   - 'output_router' for generating the target deliverable
   - 'verifier' for validation and quality assurance
4. Return ONLY valid JSON.
5. Do NOT include markdown codeblocks (```json or ```).
6. Do NOT include any preamble or conversational commentary.

JSON STRUCTURE TO RETURN:
{{
    "title": "Short title of the plan",
    "objective": "One sentence summary of the objective",
    "deliverable_type": "e.g. approval_note, compliance_report, advisory, executive_summary",
    "steps": [
        {{
            "step_number": 1,
            "action": "read_document",
            "title": "Read document",
            "description": "Specific detail on what to read or ingest",
            "tool_or_service": "document_reader",
            "status": "pending"
        }},
        {{
            "step_number": 2,
            "action": "extract_findings",
            "title": "Extract findings",
            "description": "Specific detail on key findings to extract",
            "tool_or_service": "content_intelligence",
            "status": "pending"
        }},
        {{
            "step_number": 3,
            "action": "identify_risks",
            "title": "Identify risks",
            "description": "Specific detail on risks or non-compliance to identify",
            "tool_or_service": "content_intelligence",
            "status": "pending"
        }},
        {{
            "step_number": 4,
            "action": "search_knowledge",
            "title": "Search relevant knowledge",
            "description": "Search enterprise knowledge base or regulations",
            "tool_or_service": "rag_service",
            "status": "pending"
        }},
        {{
            "step_number": 5,
            "action": "prepare_recommendation",
            "title": "Prepare recommendation",
            "description": "Formulate actionable recommendation and risk mitigation",
            "tool_or_service": "content_intelligence",
            "status": "pending"
        }},
        {{
            "step_number": 6,
            "action": "generate_deliverable",
            "title": "Generate requested deliverable",
            "description": "Synthesize formal approval note and compile .docx deliverable via DocxGenerator",
            "tool_or_service": "docx_generator",
            "status": "pending"
        }},
        {{
            "step_number": 7,
            "action": "verify_result",
            "title": "Verify result",
            "description": "Check generated deliverable against policy compliance and requirements",
            "tool_or_service": "verifier",
            "status": "pending"
        }}
    ],
    "verification_criteria": [
        "All risks addressed",
        "Sign-off checklist verified"
    ]
}}
"""

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from the LLM response text."""
        cleaned = text.strip()

        # Strip markdown fences if present
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
            if match:
                cleaned = match.group(1).strip()

        # Find outer braces if wrapped in commentary
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            cleaned = cleaned[start_idx : end_idx + 1]

        return json.loads(cleaned)

    def _fallback_plan(self, task: str) -> Dict[str, Any]:
        """Deterministic fallback plan if LLM output fails JSON parsing."""
        return {
            "title": f"Plan: {task[:50]}",
            "objective": f"Execute directive: {task}",
            "deliverable_type": "approval_note",
            "steps": [
                {
                    "step_number": 1,
                    "action": "read_document",
                    "title": "Read document",
                    "description": "Ingest and extract text from inspection reports or source attachments.",
                    "tool_or_service": "document_reader",
                    "status": "pending",
                },
                {
                    "step_number": 2,
                    "action": "extract_findings",
                    "title": "Extract findings",
                    "description": "Extract critical observations, defects, and audit metrics.",
                    "tool_or_service": "content_intelligence",
                    "status": "pending",
                },
                {
                    "step_number": 3,
                    "action": "identify_risks",
                    "title": "Identify risks",
                    "description": "Evaluate identified non-conformances, hazards, and security/safety risks.",
                    "tool_or_service": "content_intelligence",
                    "status": "pending",
                },
                {
                    "step_number": 4,
                    "action": "search_knowledge",
                    "title": "Search relevant knowledge",
                    "description": "Query enterprise policy guidelines and sovereign knowledge base via RAG.",
                    "tool_or_service": "rag_service",
                    "status": "pending",
                },
                {
                    "step_number": 5,
                    "action": "prepare_recommendation",
                    "title": "Prepare recommendation",
                    "description": "Synthesize mitigation roadmap and regulatory compliance recommendations.",
                    "tool_or_service": "content_intelligence",
                    "status": "pending",
                },
                {
                    "step_number": 6,
                    "action": "generate_deliverable",
                    "title": "Generate requested deliverable",
                    "description": "Draft formal approval note and compile .docx deliverable via DocxGenerator.",
                    "tool_or_service": "docx_generator",
                    "status": "pending",
                },
                {
                    "step_number": 7,
                    "action": "verify_result",
                    "title": "Verify result",
                    "description": "Verify factual grounding, safety sign-offs, and compliance constraints.",
                    "tool_or_service": "verifier",
                    "status": "pending",
                },
            ],
            "verification_criteria": [
                "Inspection findings corroborated with source documentation",
                "Risks clearly delineated with mitigation measures",
                "Approval criteria fulfilled per organization policy",
            ],
        }

    def _normalize_plan(self, task: str, raw_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure standard fields, step numbering, and sovereign metadata."""
        steps = raw_plan.get("steps", [])
        if not isinstance(steps, list) or not steps:
            steps = self._fallback_plan(task)["steps"]

        normalized_steps: List[Dict[str, Any]] = []
        for idx, s in enumerate(steps, start=1):
            if not isinstance(s, dict):
                continue
            normalized_steps.append({
                "step_number": idx,
                "action": s.get("action", f"step_{idx}"),
                "title": s.get("title", f"Step {idx}"),
                "description": s.get("description", ""),
                "tool_or_service": s.get("tool_or_service", "content_intelligence"),
                "status": s.get("status", "pending"),
            })

        return {
            "status": "success",
            "task": task,
            "title": raw_plan.get("title", f"Plan for: {task[:40]}"),
            "objective": raw_plan.get("objective", task),
            "deliverable_type": raw_plan.get("deliverable_type", "approval_note"),
            "total_steps": len(normalized_steps),
            "steps": normalized_steps,
            "verification_criteria": raw_plan.get(
                "verification_criteria",
                ["Verification of source findings", "Compliance approval"],
            ),
            "metadata": {
                "planner_layer": "Avyara Sovereign Agent Planner",
                "model": OLLAMA_MODEL if self.provider == "ollama" else "cloud cascade",
                "provider": self.provider,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    def _build_document_prompt(
        self,
        task: str,
        document_text: str,
        custom_instructions: str,
        rag_context: str = "",
    ) -> str:
        truncated_doc = document_text[:12000]
        rag_section = (
            f"\nRETRIEVED ORGANIZATIONAL SOPS / MANUALS (via Sovereign RAG):\n{rag_context}\n"
            if rag_context
            else ""
        )
        return f"""You are the Sovereign Agent Planner & Content Intelligence Engine of Avyara.

Analyze the following ingested enterprise document(s) and cross-reference retrieved organizational SOPs to produce both a Structured Analysis and an Executable Action Plan for the user directive.

INGESTED DOCUMENT CONTENT:
{truncated_doc}
{rag_section}
DIRECTIVE / OBJECTIVE:
{task}

ADDITIONAL INSTRUCTIONS:
{custom_instructions if custom_instructions else "Extract all factual findings, identify vulnerabilities and risks, formulate recommendations, and map to an action plan."}

RULES:
1. Ground your analysis strictly in the document text provided.
2. Extract specific, factual findings (observations, data points, status).
3. Identify all concrete risks, security issues, or compliance vulnerabilities.
4. Provide actionable mitigation recommendations.
5. Create an ordered 7-step execution plan:
   - Read document
   - Extract findings
   - Identify risks
   - Search relevant knowledge
   - Prepare recommendation
   - Generate requested deliverable
   - Verify result
6. Return ONLY valid JSON.
7. Do NOT include markdown codeblocks (```json or ```).

JSON SCHEMA TO RETURN:
{{
    "title": "Document Analysis & Approval Note Plan",
    "executive_summary": "Concise high-level synthesis of document contents",
    "findings": [
        "Finding 1 with specific facts from document",
        "Finding 2 with specific facts from document"
    ],
    "identified_risks": [
        {{
            "risk": "Description of risk",
            "severity": "High / Medium / Low",
            "impact": "Potential consequence"
        }}
    ],
    "compliance_status": "Compliant / Non-Compliant / Conditional Approval",
    "recommendations": [
        "Actionable recommendation 1",
        "Actionable recommendation 2"
    ],
    "deliverable_type": "approval_note",
    "steps": [
        {{
            "step_number": 1,
            "action": "read_document",
            "title": "Read document",
            "description": "Ingest and parse the source report via DocumentReader.",
            "tool_or_service": "document_reader",
            "status": "completed"
        }},
        {{
            "step_number": 2,
            "action": "extract_findings",
            "title": "Extract findings",
            "description": "Extracted key findings and observations from source content.",
            "tool_or_service": "content_intelligence",
            "status": "completed"
        }},
        {{
            "step_number": 3,
            "action": "identify_risks",
            "title": "Identify risks",
            "description": "Assessed non-compliances and vulnerabilities against safety thresholds.",
            "tool_or_service": "content_intelligence",
            "status": "completed"
        }},
        {{
            "step_number": 4,
            "action": "search_knowledge",
            "title": "Search relevant knowledge",
            "description": "Search enterprise repository / regulations for relevant policy rules.",
            "tool_or_service": "rag_service",
            "status": "pending"
        }},
        {{
            "step_number": 5,
            "action": "prepare_recommendation",
            "title": "Prepare recommendation",
            "description": "Formulate compliance roadmap and mitigation measures.",
            "tool_or_service": "content_intelligence",
            "status": "pending"
        }},
        {{
            "step_number": 6,
            "action": "generate_deliverable",
            "title": "Generate requested deliverable",
            "description": "Synthesize the formal approval note / executive review.",
            "tool_or_service": "output_router",
            "status": "pending"
        }},
        {{
            "step_number": 7,
            "action": "verify_result",
            "title": "Verify result",
            "description": "Verify sign-offs, evidence grounding, and regulatory compliance.",
            "tool_or_service": "verifier",
            "status": "pending"
        }}
    ],
    "verification_criteria": [
        "All identified risks have corresponding mitigation controls",
        "Findings corroborated by source document evidence"
    ]
}}
"""

    def _fallback_document_analysis(self, task: str, docs_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Heuristic fallback document analysis extracting factual evidence directly from source text."""
        sample_text = docs_info[0]["text"] if docs_info else ""
        raw_lines = [line.strip() for line in sample_text.splitlines() if line.strip()]

        # Deterministic extraction of equipment tags, measurements, and key observation lines
        eq_tags = list(dict.fromkeys(re.findall(r"\b[A-Z]{1,4}-[0-9]{2,4}[A-Z]?\b", sample_text)))
        measurements = list(dict.fromkeys(re.findall(r"\b\d+(?:\.\d+)?\s*(?:bar|psi|C|°C|mm|m|kW|V|A|Hz|rpm|mm/s|kPa|MPa)\b", sample_text, re.IGNORECASE)))

        findings: List[str] = []
        if eq_tags:
            findings.append(f"Identified equipment/instrument tags: {', '.join(eq_tags[:5])}")
        if measurements:
            findings.append(f"Recorded technical parameters: {', '.join(measurements[:5])}")

        # Add factual observation lines from source
        for line in raw_lines[:6]:
            if line not in findings and not line.startswith("---") and not line.startswith("==="):
                findings.append(line[:120])

        if not findings:
            findings = ["Source document ingested; technical details extracted for compliance review."]

        summary_sample = " ".join([l for l in raw_lines[:3] if not l.startswith("---") and not l.startswith("===")])
        if not summary_sample:
            summary_sample = "Technical inspection document ingested for sovereign compliance review."

        return {
            "title": f"Document Analysis: {docs_info[0]['filename'] if docs_info else 'Report'}",
            "executive_summary": summary_sample[:300],
            "findings": findings[:6],
            "identified_risks": [
                {
                    "risk": "Operational risk review required prior to formal approval",
                    "severity": "Medium",
                    "impact": "Potential policy non-conformance if unverified",
                }
            ],
            "compliance_status": "Conditional Approval Required",
            "recommendations": [
                "Execute structured inspection verification checklist",
                "Cross-reference findings against sovereign knowledge repository",
            ],
            "deliverable_type": "approval_note",
            "steps": self._fallback_plan(task)["steps"],
            "verification_criteria": [
                "Document evidence verified against regulatory standard",
                "All safety and compliance checks satisfied",
            ],
        }

    def _normalize_document_analysis(
        self,
        task: str,
        docs_info: List[Dict[str, Any]],
        parsed: Dict[str, Any],
        retrieved_knowledge: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Normalize structured analysis, document statistics, and step details."""
        steps = parsed.get("steps", [])
        if not isinstance(steps, list) or not steps:
            steps = self._fallback_plan(task)["steps"]

        normalized_steps: List[Dict[str, Any]] = []
        for idx, s in enumerate(steps, start=1):
            if not isinstance(s, dict):
                continue
            normalized_steps.append({
                "step_number": idx,
                "action": s.get("action", f"step_{idx}"),
                "title": s.get("title", f"Step {idx}"),
                "description": s.get("description", ""),
                "tool_or_service": s.get("tool_or_service", "content_intelligence"),
                "status": s.get("status", "pending"),
            })

        result: Dict[str, Any] = {
            "status": "success",
            "task": task,
            "title": parsed.get("title", "Document Analysis & Approval Plan"),
            "documents_analyzed": [
                {
                    "filename": d["filename"],
                    "extension": d["extension"],
                    "char_count": d["char_count"],
                    "size_bytes": d["size_bytes"],
                    "source_type": d.get("source_type", "document"),
                    "processing": d.get("processing", "native_text_extraction"),
                    "model_provider": "local",
                    "external_calls": 0,
                }
                for d in docs_info
            ],
            "executive_summary": parsed.get("executive_summary", ""),
            "findings": parsed.get("findings", []),
            "identified_risks": parsed.get("identified_risks", []),
            "compliance_status": parsed.get("compliance_status", "Pending Review"),
            "recommendations": parsed.get("recommendations", []),
            "deliverable_type": parsed.get("deliverable_type", "approval_note"),
            "total_steps": len(normalized_steps),
            "steps": normalized_steps,
            "verification_criteria": parsed.get(
                "verification_criteria",
                ["Evidence corroboration", "Compliance check"],
            ),
            "metadata": {
                "planner_layer": "Avyara Sovereign Agent Planner",
                "processor": "DocumentReader (PyPDF / Python-Docx / PPTX)",
                "model": OLLAMA_MODEL if self.provider == "ollama" else "cloud cascade",
                "provider": self.provider,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        if retrieved_knowledge:
            result["retrieved_knowledge"] = [
                {
                    "document_title": k.get("document_title"),
                    "filename": k.get("filename"),
                    "similarity": round(float(k.get("similarity", 0.0)), 4),
                    "snippet": k.get("content", "")[:200] + "...",
                }
                for k in retrieved_knowledge
            ]

        from services.sovereignty_monitor import sovereignty_monitor
        result["confidentiality"] = sovereignty_monitor.get_confidentiality_metadata()

        return result


INDUSTRIAL_TASK_TEMPLATES = [
    {
        "id": "inspection_report_analysis",
        "title": "Inspection Report Analysis",
        "description": "Examine scanned or native inspection reports, identify defects, evaluate risk severity, and produce a formal compliance summary.",
        "default_prompt": "Perform a rigorous safety and statutory compliance inspection review of this technical report. Identify defects, classify risk severity, and evaluate adherence to applicable SOPs.",
        "recommended_output": "inspection_analysis",
        "output_format": "docx",
    },
    {
        "id": "engineering_drawing_review",
        "title": "Engineering Drawing Review",
        "description": "Analyze industrial blueprints and engineering drawings, verify revision blocks, line specs, and equipment layouts.",
        "default_prompt": "Review this engineering drawing. Extract drawing number, revision status, readable equipment tags, and verify process design integrity against standards.",
        "recommended_output": "document",
        "output_format": "docx",
    },
    {
        "id": "pid_tag_extraction",
        "title": "P&ID Text/Tag Extraction",
        "description": "Extract all readable equipment tags, line numbers, and instrument loops from piping and instrumentation diagrams.",
        "default_prompt": "Extract all readable equipment tags, line numbers, control valves, and process limits from this P&ID diagram without fabricating illegible symbols.",
        "recommended_output": "document",
        "output_format": "docx",
    },
    {
        "id": "equipment_nameplate_extraction",
        "title": "Equipment Nameplate Extraction",
        "description": "Extract technical operating parameters (voltage, pressure rating, serial number, model) from equipment nameplate photographs.",
        "default_prompt": "Inspect this equipment rating plate image. Extract manufacturer, model number, serial number, design pressure, electrical specs, and temperature limits.",
        "recommended_output": "inspection_analysis",
        "output_format": "docx",
    },
    {
        "id": "safety_audit",
        "title": "Safety Audit & Risk Matrix",
        "description": "Perform safety gap analysis across industrial assets, evaluating hazard mitigations and statutory worker safety requirements.",
        "default_prompt": "Conduct an industrial safety audit based on these inspection findings. Construct a risk severity matrix and prescribe mandatory mitigation measures.",
        "recommended_output": "inspection_analysis",
        "output_format": "docx",
    },
    {
        "id": "sop_compliance_check",
        "title": "SOP Compliance Check",
        "description": "Compare field observations and test readings against internal Standard Operating Procedures (SOPs) retrieved via local RAG.",
        "default_prompt": "Cross-reference the reported field measurements and observations against internal SOP standards retrieved from the knowledge base. Detail all non-conformances.",
        "recommended_output": "document",
        "output_format": "docx",
    },
    {
        "id": "approval_note_generation",
        "title": "Approval Note Generation",
        "description": "Synthesize multi-source inspection reports and photos into an executive approval note with sign-off recommendations.",
        "default_prompt": "Synthesize this inspection report and photographic evidence into a formal executive Approval Note recommending technical sign-off and outlining risk mitigations.",
        "recommended_output": "document",
        "output_format": "docx",
    },
    {
        "id": "confidential_document_summary",
        "title": "Confidential Document Summary",
        "description": "Produce an air-gapped confidential executive summary with zero external leakage and complete audit tracking.",
        "default_prompt": "Prepare an executive confidential summary of this sensitive technical document, highlighting key findings, financial impacts, and risk considerations.",
        "recommended_output": "executive_summary",
        "output_format": "docx",
    },
    {
        "id": "maintenance_analysis",
        "title": "Maintenance Analysis",
        "description": "Analyze preventative or corrective maintenance logs, calculate MTBF/MTTR indicators, and formulate overhaul schedules.",
        "default_prompt": "Evaluate equipment maintenance history, wear patterns, and failure logs. Prescribe actionable maintenance interventions and spare part requirements.",
        "recommended_output": "inspection_analysis",
        "output_format": "docx",
    },
    {
        "id": "engineering_calculation",
        "title": "Engineering Calculation",
        "description": "Perform thermodynamic, fluid mechanics, or stress calculations with explicit assumptions, formulas, and verification.",
        "default_prompt": "Perform an engineering calculation for pump head, pressure drop, and thermal expansion limits based on the provided technical parameters. State all formulas and assumptions.",
        "recommended_output": "document",
        "output_format": "docx",
    },
    {
        "id": "spreadsheet_analysis",
        "title": "Spreadsheet Analysis",
        "description": "Parse tabular inspection logs, operational parameters, or chemical assay spreadsheets with statistical validation.",
        "default_prompt": "Analyze this operational dataset/spreadsheet. Summarize column distributions, detect anomalies exceeding statutory thresholds, and formulate data-backed recommendations.",
        "recommended_output": "document",
        "output_format": "docx",
    },
    {
        "id": "coding_task",
        "title": "Code Generation + Verification",
        "description": "Generate Python automation scripts or data processing tools and execute them safely inside the dedicated local sandbox.",
        "default_prompt": "Generate a Python script to compute mechanical stress and hydrostatic test parameters, execute it in the local sandbox, and verify calculation results.",
        "recommended_output": "document",
        "output_format": "docx",
    },
]


def get_industrial_task_templates() -> List[Dict[str, Any]]:
    """Return all predefined industrial task templates."""
    return list(INDUSTRIAL_TASK_TEMPLATES)

