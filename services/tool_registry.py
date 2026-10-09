"""
services/tool_registry.py
--------------------------
Centralized Local Tool Registry & Workspace Safety Boundary for Avyara Sovereign Workbench.
SIH Problem Statement 26117.

Capabilities:
1. Workspace Security Boundary:
   - Validates all file paths against designated project & output directories.
   - Prevents path traversal (../../) and protects system/credential files.
   - Enforces read vs write directory permissions (writes strictly restricted to output/).

2. Tool Registry:
   - Provides standardized schemas and execution wrappers for local tools:
     1. read_file
     2. write_file
     3. list_files
     4. read_document (reuses DocumentReader with OCR/multimodal support)
     5. search_knowledge_base (reuses Sovereign RagService)
     6. create_docx (reuses DocxGenerator)
     7. create_pptx (reuses PPTGenerator)
     8. verify_artifact (validates existence, size, and format integrity)

3. Zero External Leakage:
   - 100% on-premise execution with telemetry: external_calls = 0.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from services.document_reader import DocumentReader
from services.rag_service import RagService
from services.docx_generator import DocxGenerator
from services.ppt_generator import PPTGenerator

logger = logging.getLogger(__name__)

# Base Workspace Paths
BASE_PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_PROJECT_DIR / "output"
UPLOADS_DIR = OUTPUT_DIR / "uploads"
DOCUMENTS_DIR = OUTPUT_DIR / "documents"
PRESENTATIONS_DIR = OUTPUT_DIR / "presentations"

for d in (OUTPUT_DIR, UPLOADS_DIR, DOCUMENTS_DIR, PRESENTATIONS_DIR):
    d.mkdir(parents=True, exist_ok=True)


class WorkspaceSecurity:
    """
    Enforces strict filesystem isolation and directory confinement.
    Prevents path traversal attacks and unauthorized file access.
    """

    ALLOWED_READ_ROOTS = [
        BASE_PROJECT_DIR.resolve(),
    ]

    ALLOWED_WRITE_ROOTS = [
        OUTPUT_DIR.resolve(),
    ]

    DISALLOWED_READ_NAMES = {
        ".env", ".git", "id_rsa", "credentials", "id_ed25519", "config.json"
    }

    @classmethod
    def sanitize_and_validate_read(cls, path_input: Union[str, Path]) -> Path:
        """
        Validate that the target file for reading is safely within the allowed project boundary
        and is not a protected system or credential file.
        """
        target = Path(path_input)
        if not target.is_absolute():
            target = (BASE_PROJECT_DIR / target).resolve()
        else:
            target = target.resolve()

        # Check path traversal
        in_allowed_root = any(
            target == root or root in target.parents for root in cls.ALLOWED_READ_ROOTS
        )
        if not in_allowed_root:
            raise PermissionError(
                f"WorkspaceSecurity: Read path '{path_input}' is outside allowed project boundaries."
            )

        # Block sensitive credential files
        if target.name.lower() in cls.DISALLOWED_READ_NAMES or target.name.startswith(".env"):
            raise PermissionError(
                f"WorkspaceSecurity: Access to protected configuration file '{target.name}' is prohibited."
            )

        return target

    @classmethod
    def sanitize_and_validate_write(cls, path_input: Union[str, Path]) -> Path:
        """
        Validate that the target file for writing is strictly within designated output directories.
        Prevents tampering with codebase or operating system binaries.
        """
        target = Path(path_input)
        if not target.is_absolute():
            norm_str = str(path_input).replace("\\", "/")
            if norm_str.startswith("output/"):
                target = (BASE_PROJECT_DIR / path_input).resolve()
            else:
                target = (OUTPUT_DIR / path_input).resolve()
        else:
            target = target.resolve()

        # Check write confinement: must be under OUTPUT_DIR
        out_root = OUTPUT_DIR.resolve()
        if target != out_root and out_root not in target.parents:
            raise PermissionError(
                f"WorkspaceSecurity: Write path '{path_input}' is outside authorized output directory."
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        return target


@dataclass
class ToolExecutionResult:
    tool: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    external_calls: int = 0
    execution: str = "local"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    execute: Callable[..., Any]
    permission: str  # "read", "write", "execute"
    local_only: bool = True


class LocalToolRegistry:
    """
    Centralized Registry for Sovereign Agent Tools.
    """

    def __init__(self) -> None:
        self.doc_reader = DocumentReader()
        self.rag_service = RagService()
        self.docx_generator = DocxGenerator()
        self.ppt_generator = PPTGenerator()
        self.tools: Dict[str, ToolDefinition] = {}

        self._register_default_tools()

    def _register_default_tools(self) -> None:
        # 1. read_file
        self.register_tool(
            ToolDefinition(
                name="read_file",
                description="Reads the text contents of a file within the allowed workspace boundary.",
                input_schema={"file_path": "str", "max_chars": "Optional[int]"},
                output_schema={"text": "str", "char_count": "int", "path": "str"},
                execute=self._tool_read_file,
                permission="read",
            )
        )

        # 2. write_file
        self.register_tool(
            ToolDefinition(
                name="write_file",
                description="Writes text or structured content to an allowed output file.",
                input_schema={"file_path": "str", "content": "str"},
                output_schema={"path": "str", "bytes_written": "int"},
                execute=self._tool_write_file,
                permission="write",
            )
        )

        # 3. list_files
        self.register_tool(
            ToolDefinition(
                name="list_files",
                description="Lists available files in an authorized directory.",
                input_schema={"directory": "Optional[str]", "pattern": "Optional[str]"},
                output_schema={"files": "List[str]", "count": "int"},
                execute=self._tool_list_files,
                permission="read",
            )
        )

        # 4. read_document
        self.register_tool(
            ToolDefinition(
                name="read_document",
                description="Ingests a document (PDF, scanned PDF via local OCR, DOCX, TXT, image) returning extracted text and metadata.",
                input_schema={"file_path": "str"},
                output_schema={"text": "str", "source_type": "str", "processing": "str", "char_count": "int"},
                execute=self._tool_read_document,
                permission="read",
            )
        )

        # 5. search_knowledge_base
        self.register_tool(
            ToolDefinition(
                name="search_knowledge_base",
                description="Searches local organizational SOP knowledge base using sovereign vector similarity.",
                input_schema={"query": "str", "top_k": "Optional[int]", "threshold": "Optional[float]"},
                output_schema={"matches": "List[Dict]", "count": "int", "formatted_context": "str"},
                execute=self._tool_search_knowledge_base,
                permission="read",
            )
        )

        # 6. create_docx
        self.register_tool(
            ToolDefinition(
                name="create_docx",
                description="Compiles structured findings, analysis, and approval notes into a publication-grade Word (.docx) deliverable.",
                input_schema={"title": "str", "content_markdown": "str", "metadata": "Optional[Dict]", "filename": "Optional[str]"},
                output_schema={"path": "str", "filename": "str", "size_bytes": "int"},
                execute=self._tool_create_docx,
                permission="write",
            )
        )

        # 7. create_pptx
        self.register_tool(
            ToolDefinition(
                name="create_pptx",
                description="Generates an executive presentation (.pptx) summarizing key findings.",
                input_schema={"title": "str", "slide_plan": "Optional[List[Dict]]", "filename": "Optional[str]"},
                output_schema={"path": "str", "filename": "str", "size_bytes": "int"},
                execute=self._tool_create_pptx,
                permission="write",
            )
        )

        # 8. verify_artifact
        self.register_tool(
            ToolDefinition(
                name="verify_artifact",
                description="Verifies that a generated deliverable file exists, is non-empty, and structurally valid.",
                input_schema={"file_path": "str", "expected_type": "Optional[str]", "min_size_bytes": "Optional[int]"},
                output_schema={"valid": "bool", "file_size": "int", "details": "Dict"},
                execute=self._tool_verify_artifact,
                permission="read",
            )
        )

        # 9. execute_python (Dedicated Coding Sandbox)
        self.register_tool(
            ToolDefinition(
                name="execute_python",
                description="Executes Python code in an isolated local sandbox directory with timeout and resource limits, capturing stdout, stderr, and output files.",
                input_schema={"code": "str", "input_files": "Optional[List[str]]", "timeout": "Optional[float]"},
                output_schema={"success": "bool", "exit_code": "int", "stdout": "str", "stderr": "str", "duration_ms": "float", "output_files": "List[str]", "sandbox": "bool"},
                execute=self._tool_execute_python,
                permission="execute",
            )
        )

    def register_tool(self, tool: ToolDefinition) -> None:
        self.tools[tool.name] = tool
        logger.debug("LocalToolRegistry: Registered tool '%s'", tool.name)

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "output_schema": t.output_schema,
                "permission": t.permission,
                "local_only": t.local_only,
            }
            for t in self.tools.values()
        ]

    def execute_tool(self, name: str, params: Dict[str, Any]) -> ToolExecutionResult:
        """
        Executes a registered tool with strict error containment and zero external calls.
        """
        tool = self.get_tool(name)
        if not tool:
            return ToolExecutionResult(
                tool=name,
                success=False,
                error=f"Tool '{name}' is not registered in LocalToolRegistry.",
                external_calls=0,
            )

        try:
            logger.info("LocalToolRegistry: Executing '%s' locally...", name)
            res = tool.execute(**params)
            return ToolExecutionResult(
                tool=name,
                success=True,
                result=res,
                external_calls=0,
                execution="local",
            )
        except Exception as exc:
            logger.warning("LocalToolRegistry: Tool '%s' execution failed: %s", name, exc)
            return ToolExecutionResult(
                tool=name,
                success=False,
                error=str(exc),
                external_calls=0,
                execution="local",
            )

    # ─── TOOL IMPLEMENTATIONS ──────────────────────────────────────────────

    def _tool_read_file(self, file_path: str, max_chars: int = 50000) -> Dict[str, Any]:
        safe_path = WorkspaceSecurity.sanitize_and_validate_read(file_path)
        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: '{file_path}'")

        text = safe_path.read_text(encoding="utf-8", errors="replace")
        truncated = text[:max_chars]
        return {
            "path": str(safe_path),
            "text": truncated,
            "char_count": len(truncated),
            "total_chars": len(text),
            "truncated": len(text) > max_chars,
        }

    def _tool_write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        safe_path = WorkspaceSecurity.sanitize_and_validate_write(file_path)
        safe_path.write_text(content, encoding="utf-8")
        return {
            "path": str(safe_path),
            "bytes_written": safe_path.stat().st_size,
        }

    def _tool_list_files(self, directory: Optional[str] = "output", pattern: Optional[str] = "*") -> Dict[str, Any]:
        target_dir = WorkspaceSecurity.sanitize_and_validate_read(directory or "output")
        if not target_dir.is_dir():
            raise NotADirectoryError(f"Target '{directory}' is not a directory.")

        matched = [
            f.name for f in target_dir.glob(pattern or "*") if f.is_file()
        ]
        return {
            "directory": str(target_dir),
            "files": matched,
            "count": len(matched),
        }

    def _tool_read_document(self, file_path: str) -> Dict[str, Any]:
        safe_path = WorkspaceSecurity.sanitize_and_validate_read(file_path)
        if not safe_path.exists():
            raise FileNotFoundError(f"Document file not found: '{file_path}'")

        meta = self.doc_reader.read_with_metadata(str(safe_path))
        return {
            "path": str(safe_path),
            "filename": safe_path.name,
            "text": meta.get("text", ""),
            "source_type": meta.get("source_type", "document"),
            "processing": meta.get("processing", "native_text_extraction"),
            "char_count": meta.get("char_count", len(meta.get("text", ""))),
            "external_calls": 0,
        }

    def _tool_search_knowledge_base(
        self, query: str, top_k: int = 3, threshold: float = 0.05
    ) -> Dict[str, Any]:
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")

        self.rag_service.ensure_default_sops()
        retrieved = self.rag_service.retrieve(query=query.strip(), top_k=top_k, threshold=threshold)
        formatted = self.rag_service.format_context_for_llm(retrieved)

        cleaned_matches = []
        for r in retrieved:
            cleaned_matches.append({
                "document_title": r.get("document_title") if isinstance(r, dict) else getattr(r, "document_title", ""),
                "similarity": float(r.get("similarity", 0.0)) if isinstance(r, dict) else getattr(r, "similarity", 0.0),
                "snippet": (r.get("content", "") if isinstance(r, dict) else getattr(r, "content", ""))[:200],
            })

        return {
            "count": len(retrieved),
            "matches": cleaned_matches,
            "formatted_context": formatted,
        }

    def _tool_create_docx(
        self,
        title: str,
        content_markdown: str,
        metadata: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        meta = metadata or {}
        meta.setdefault("provider", "Local Ollama Sovereign")
        meta.setdefault("status", "Sovereign Agent Verified")

        res = self.docx_generator.generate_inspection_approval_docx(
            title=title,
            content_markdown=content_markdown,
            metadata=meta,
            filename=filename,
        )
        return res

    def _tool_create_pptx(
        self,
        title: str,
        slide_plan: Optional[List[Dict[str, Any]]] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        slides = slide_plan or [
            {
                "type": "title",
                "title": title,
                "content": ["Autonomous Enterprise Inspection Briefing", "Avyara Sovereign Workbench"],
            },
            {
                "type": "content",
                "title": "Executive Summary & Core Findings",
                "content": [
                    "Key equipment vulnerabilities identified.",
                    "SOP statutory compliance threshold evaluated.",
                    "Mitigation actions and sign-off criteria outlined.",
                ],
            },
            {
                "type": "content",
                "title": "Mitigation Roadmap & Next Actions",
                "content": [
                    "Phase 1: Emergency isolation and containment.",
                    "Phase 2: Corrective maintenance and SOP sign-off.",
                    "Phase 3: Periodic compliance re-audit.",
                ],
            },
        ]

        if not filename:
            import uuid
            clean_name = re.sub(r"[^a-zA-Z0-9_\-]+", "_", title.lower())[:25]
            filename = f"presentation_{clean_name}_{uuid.uuid4().hex[:6]}.pptx"

        dest_file = PRESENTATIONS_DIR / filename
        self.ppt_generator.generate(slide_plan=slides, filename=filename)

        return {
            "type": "file",
            "path": str(dest_file),
            "filename": filename,
            "size_bytes": dest_file.stat().st_size if dest_file.exists() else 0,
        }

    def _tool_verify_artifact(
        self,
        file_path: str,
        expected_type: Optional[str] = None,
        min_size_bytes: int = 100,
    ) -> Dict[str, Any]:
        safe_path = WorkspaceSecurity.sanitize_and_validate_read(file_path)
        if not safe_path.exists():
            return {
                "valid": False,
                "error": f"Deliverable file does not exist: {file_path}",
                "path": str(safe_path),
            }

        size = safe_path.stat().st_size
        if size < min_size_bytes:
            return {
                "valid": False,
                "error": f"File size ({size} bytes) is below minimum threshold ({min_size_bytes} bytes).",
                "path": str(safe_path),
                "size_bytes": size,
            }

        suffix = safe_path.suffix.lower()
        if expected_type and not suffix.endswith(expected_type.lower().lstrip(".")):
            return {
                "valid": False,
                "error": f"File extension '{suffix}' does not match expected '{expected_type}'.",
                "path": str(safe_path),
                "size_bytes": size,
            }

        # Check structural opening integrity for standard office formats
        is_corrupt = False
        format_info = {}
        if suffix == ".docx":
            try:
                from docx import Document
                doc = Document(str(safe_path))
                format_info["paragraphs"] = len(doc.paragraphs)
                format_info["tables"] = len(doc.tables)
            except Exception as err:
                is_corrupt = True
                format_info["error"] = f"DOCX parsing failed: {err}"
        elif suffix == ".pptx":
            try:
                from pptx import Presentation
                prs = Presentation(str(safe_path))
                format_info["slides"] = len(prs.slides)
            except Exception as err:
                is_corrupt = True
                format_info["error"] = f"PPTX parsing failed: {err}"

        return {
            "valid": not is_corrupt,
            "path": str(safe_path),
            "filename": safe_path.name,
            "size_bytes": size,
            "format": suffix,
            "details": format_info,
        }

    def _tool_execute_python(
        self,
        code: str,
        input_files: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        from services.python_sandbox import python_sandbox
        res = python_sandbox.execute(
            code=code,
            task_id=task_id,
            input_files=input_files,
            timeout=timeout,
        )
        return res.to_dict()


# Global tool registry singleton
local_tool_registry = LocalToolRegistry()
