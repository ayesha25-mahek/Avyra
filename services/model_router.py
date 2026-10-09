"""
services/model_router.py
-------------------------
Local Model Router & Dynamic Task-Model Selection for Avyara Sovereign AI Workbench.
SIH Problem Statement 26117.

Capabilities:
1. Model Registry:
   - Centralized catalog of local (Ollama) and cloud (Gemini, Groq) models.
   - Dynamically discovers installed models in Ollama via /api/tags without auto-downloading large weights.
   - Resource-aware attributes (VRAM, capabilities, priorities).

2. Task Classifier:
   - Identifies task categories: general_reasoning, document_analysis, inspection_analysis,
     approval_note_generation, multimodal, coding, spreadsheet, summarization, presentation_generation.
   - Reuses deterministic rules, Agent Planner metadata, requested output formats, and ingested file types.

3. Automatic Model Selection:
   - Selects the best available model for the identified task.
   - When Sovereign/Ollama mode is active, strictly enforces local routing with external_calls = 0.
   - Implements graceful fallback (e.g. multimodal fallback to Local OCR + Qwen 2.5 7B when no local vision LLM is installed).
   - Preserves existing cloud cascades when cloud mode is explicitly active.
"""

import logging
import os
import time
import urllib.error
import urllib.request
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from services.sovereignty_monitor import sovereignty_monitor, SovereignViolationError

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_SOVEREIGN_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


@dataclass
class ModelProfile:
    model_name: str
    provider: str  # "ollama", "gemini", "groq"
    local: bool
    capabilities: List[str]
    task_types: List[str]
    vram_mb: int = 0
    priority: int = 50
    is_installed: bool = False
    description: str = ""


@dataclass
class RoutingDecision:
    task_type: str
    selected_model: str
    provider: str
    local: bool
    reason: str
    fallback_used: bool = False
    fallback: Optional[str] = None
    vision_model: Optional[str] = None
    external_calls: int = 0
    vram_mb: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["confidentiality"] = sovereignty_monitor.get_confidentiality_metadata()
        return d


class ModelRegistry:
    """
    Centralized Model Registry with dynamic local installation discovery.
    """

    def __init__(self, ollama_url: str = OLLAMA_BASE_URL) -> None:
        self.ollama_url = ollama_url.rstrip("/")
        self._installed_cache: List[str] = []
        self._cache_timestamp: float = 0.0
        self._cache_ttl_seconds: float = 30.0

        # Catalog of known model profiles
        self.catalog: Dict[str, ModelProfile] = {
            # --- Local Sovereign Models ---
            "qwen2.5:7b": ModelProfile(
                model_name="qwen2.5:7b",
                provider="ollama",
                local=True,
                capabilities=["reasoning", "document_analysis", "planning", "inspection_analysis", "approval_note_generation"],
                task_types=["general_reasoning", "document_analysis", "inspection_analysis", "approval_note_generation", "presentation_generation", "coding"],
                vram_mb=4800,
                priority=100,
                description="Primary sovereign reasoning & industrial inspection model.",
            ),
            "gemma3:1b": ModelProfile(
                model_name="gemma3:1b",
                provider="ollama",
                local=True,
                capabilities=["fast_summarization", "lightweight_text"],
                task_types=["summarization", "general_reasoning"],
                vram_mb=1200,
                priority=60,
                description="Ultra-fast, low-footprint local text model.",
            ),
            "qwen2.5-coder:7b": ModelProfile(
                model_name="qwen2.5-coder:7b",
                provider="ollama",
                local=True,
                capabilities=["coding", "scripting", "debugging"],
                task_types=["coding"],
                vram_mb=4800,
                priority=90,
                description="Specialized local code synthesis model.",
            ),
            "qwen2.5-vl": ModelProfile(
                model_name="qwen2.5-vl",
                provider="ollama",
                local=True,
                capabilities=["vision", "multimodal", "diagram_reading"],
                task_types=["multimodal", "inspection_analysis"],
                vram_mb=6000,
                priority=95,
                description="Local vision-language model for image inspection.",
            ),
            "llava": ModelProfile(
                model_name="llava",
                provider="ollama",
                local=True,
                capabilities=["vision", "multimodal"],
                task_types=["multimodal"],
                vram_mb=4800,
                priority=85,
                description="Local multimodal vision model.",
            ),
            "bakllava": ModelProfile(
                model_name="bakllava",
                provider="ollama",
                local=True,
                capabilities=["vision", "multimodal"],
                task_types=["multimodal"],
                vram_mb=4800,
                priority=80,
                description="Local multimodal vision model.",
            ),
            # --- Cloud Models (Preserved) ---
            "gemini-3.6-flash": ModelProfile(
                model_name="gemini-3.6-flash",
                provider="gemini",
                local=False,
                capabilities=["reasoning", "multimodal", "general_text"],
                task_types=["general_reasoning", "document_analysis", "presentation_generation"],
                priority=90,
                description="High-speed cloud multimodal foundation model.",
            ),
            "gemini-3.5-flash-lite": ModelProfile(
                model_name="gemini-3.5-flash-lite",
                provider="gemini",
                local=False,
                capabilities=["fast_text"],
                task_types=["summarization", "general_reasoning"],
                priority=80,
                description="Low-latency cloud fallback model.",
            ),
            "openai/gpt-oss-120b": ModelProfile(
                model_name="openai/gpt-oss-120b",
                provider="groq",
                local=False,
                capabilities=["deep_reasoning"],
                task_types=["general_reasoning", "document_analysis"],
                priority=85,
                description="Groq high-throughput cloud model.",
            ),
            "qwen/qwen3.6-27b": ModelProfile(
                model_name="qwen/qwen3.6-27b",
                provider="groq",
                local=False,
                capabilities=["reasoning"],
                task_types=["general_reasoning", "inspection_analysis"],
                priority=82,
                description="Groq enterprise reasoning model.",
            ),
        }

    def get_installed_ollama_models(self, force_refresh: bool = False) -> List[str]:
        """
        Query Ollama /api/tags to detect models actually installed locally.
        Cached for 30 seconds to prevent query bottlenecks.
        """
        now = time.time()
        if not force_refresh and self._installed_cache and (now - self._cache_timestamp < self._cache_ttl_seconds):
            return list(self._installed_cache)

        installed: List[str] = []
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", headers={"User-Agent": "AvyaraModelRouter/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("models", []):
                    name = item.get("name", "")
                    if name:
                        installed.append(name)
                        # Also register bare name without :latest if present
                        if ":" in name:
                            installed.append(name.split(":")[0])
        except Exception as exc:
            logger.debug("ModelRegistry: Could not poll Ollama /api/tags (%s). Using fallback tag list.", exc)
            # If Ollama responded previously, reuse cache
            if self._installed_cache:
                return list(self._installed_cache)
            # Default assumption
            installed = [DEFAULT_SOVEREIGN_MODEL]

        self._installed_cache = list(set(installed))
        self._cache_timestamp = now
        return list(self._installed_cache)

    def is_local_model_installed(self, model_name: str) -> bool:
        """Check if a specific model is installed in local Ollama."""
        installed = self.get_installed_ollama_models()
        # Direct match or prefix match (e.g. 'qwen2.5:7b' matches 'qwen2.5:7b')
        for inst in installed:
            if model_name == inst or model_name.split(":")[0] == inst.split(":")[0]:
                return True
        return False

    def get_installed_vision_models(self) -> List[str]:
        """Detect any local vision model currently installed in Ollama."""
        vision_candidates = ["qwen2.5-vl", "llava", "bakllava", "minicpm-v"]
        installed = self.get_installed_ollama_models()
        found: List[str] = []
        for cand in vision_candidates:
            for inst in installed:
                if cand in inst.lower():
                    found.append(inst)
        return list(set(found))

    def has_cloud_credentials(self, provider: str) -> bool:
        """Verify if environment credentials exist for a cloud provider."""
        if provider == "gemini":
            return any(os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 6))
        if provider == "groq":
            return any(os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 6))
        return False


class TaskClassifier:
    """
    Deterministic & Context-Aware Task Classifier.
    """

    TASK_CATEGORIES = [
        "inspection_analysis",
        "approval_note_generation",
        "multimodal",
        "document_analysis",
        "presentation_generation",
        "summarization",
        "coding",
        "spreadsheet",
        "general_reasoning",
    ]

    @classmethod
    def classify(
        cls,
        prompt: str = "",
        outputs: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        task_hint: Optional[str] = None,
    ) -> str:
        """
        Classifies task type without requiring a secondary LLM call.
        """
        # 1. Respect explicit task hint if already valid
        if task_hint and task_hint in cls.TASK_CATEGORIES:
            return task_hint

        outputs = outputs or []
        files = files or []
        p_lower = (prompt or "").lower()

        # 2. Check for uploaded multimodal artifacts (images or scanned PDFs)
        has_images = any(
            Path(f).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")
            for f in files
        )

        if has_images or "photo" in p_lower or "photograph" in p_lower or "diagram" in p_lower or "scanned" in p_lower:
            return "multimodal"

        # 3. Check requested output types
        if "inspection_analysis" in outputs:
            return "inspection_analysis"
        if "presentation" in outputs:
            return "presentation_generation"
        if "executive_summary" in outputs and len(outputs) == 1:
            return "summarization"

        # 4. Check prompt keywords & contents
        inspection_keywords = [
            "inspection", "technical audit", "field audit", "equipment defect",
            "flange leak", "flange", "oil breakdown", "dielectric", "safety audit",
            "hazard inspection", "plant audit", "plant inspection", "equipment failure"
        ]
        if any(kw in p_lower for kw in inspection_keywords):
            return "inspection_analysis"

        if "approval note" in p_lower or "sign-off" in p_lower or "statutory signoff" in p_lower:
            return "approval_note_generation"

        code_keywords = ["python", "function", "script", "algorithm", "debug", "refactor", "code sandbox"]
        if any(kw in p_lower for kw in code_keywords):
            return "coding"

        sheet_keywords = ["spreadsheet", "excel", "csv", "table", "rows", "columns", "financial sheet"]
        if any(kw in p_lower for kw in sheet_keywords):
            return "spreadsheet"

        if any(kw in p_lower for kw in ["summarize", "executive summary", "briefing", "tldr"]):
            return "summarization"

        if any(kw in p_lower for kw in ["slide", "slideshow", "presentation", "deck"]):
            return "presentation_generation"

        # 5. File-based fallback
        if files:
            return "document_analysis"

        return "general_reasoning"


class LocalModelRouter:
    """
    Local Model Router for Avyara Sovereign AI Workbench.
    Automatically selects the most appropriate local/cloud model based on task,
    resource availability, and user provider mode.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None) -> None:
        self.registry = registry or ModelRegistry()
        self.classifier = TaskClassifier()

    def route(
        self,
        task_type: Optional[str] = None,
        requirements: Optional[Dict[str, Any]] = None,
        provider_mode: str = "auto",
        prompt: str = "",
        outputs: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
    ) -> RoutingDecision:
        """
        Main routing function: select_model(task_type, requirements, provider_mode).
        """
        requirements = requirements or {}
        mode = (provider_mode or "auto").lower().strip()
        is_sovereign_mode = mode in ("ollama", "local", "local_ollama", "sovereign")

        # 1. Identify Task Category
        final_task_type = task_type or self.classifier.classify(
            prompt=prompt,
            outputs=outputs,
            files=files,
            task_hint=requirements.get("task_hint"),
        )

        logger.info(
            "LocalModelRouter: Routing task '%s' (mode: %s, attached files: %d)...",
            final_task_type,
            mode,
            len(files or []),
        )

        # 2. Check installed local models in Ollama
        installed_local_models = self.registry.get_installed_ollama_models()
        primary_sovereign = DEFAULT_SOVEREIGN_MODEL

        # Ensure primary sovereign model is identified
        if primary_sovereign not in installed_local_models and installed_local_models:
            # Pick first available installed model
            primary_sovereign = installed_local_models[0]

        # ─────────────────────────────────────────────────────────────────
        # SOVEREIGN / LOCAL ROUTING (100% on-premise, zero external calls)
        # ─────────────────────────────────────────────────────────────────
        if is_sovereign_mode:
            # Enforce strict sovereignty policy (no silent cloud fallback)
            sovereignty_monitor.enforce_sovereignty_check(provider_mode, operation=f"route({final_task_type})")

            if not installed_local_models:
                logger.error("LocalModelRouter: No local Ollama models detected while in Sovereign Mode.")
                raise SovereignViolationError(
                    "Required local capability unavailable. No external provider was used."
                )

            # A) MULTIMODAL TASK
            if final_task_type == "multimodal" or requirements.get("needs_vision"):
                installed_vision = self.registry.get_installed_vision_models()
                if installed_vision:
                    selected_vision = installed_vision[0]
                    return RoutingDecision(
                        task_type=final_task_type,
                        selected_model=selected_vision,
                        provider="ollama",
                        local=True,
                        reason="Installed local vision-language model selected for image understanding.",
                        fallback_used=False,
                        vision_model=selected_vision,
                        external_calls=0,
                        vram_mb=6000,
                    )
                else:
                    # Fallback to Local OCR + Qwen 2.5 7B
                    return RoutingDecision(
                        task_type=final_task_type,
                        selected_model=primary_sovereign,
                        provider="ollama",
                        local=True,
                        reason="No local vision LLM installed; routed to Qwen 2.5 7B with on-premise OCR fallback.",
                        fallback_used=True,
                        fallback="local_ocr",
                        vision_model=None,
                        external_calls=0,
                        vram_mb=4800,
                        details={"ocr_engine": "winocr_native", "cloud_calls_prevented": True},
                    )

            # B) CODING TASK
            elif final_task_type == "coding":
                if self.registry.is_local_model_installed("qwen2.5-coder:7b"):
                    return RoutingDecision(
                        task_type="coding",
                        selected_model="qwen2.5-coder:7b",
                        provider="ollama",
                        local=True,
                        reason="Dedicated local code synthesis model selected.",
                        fallback_used=False,
                        external_calls=0,
                        vram_mb=4800,
                    )
                else:
                    return RoutingDecision(
                        task_type="coding",
                        selected_model=primary_sovereign,
                        provider="ollama",
                        local=True,
                        reason="Specialized coding model not installed; routed to primary local reasoning model.",
                        fallback_used=True,
                        fallback="primary_local_reasoning",
                        external_calls=0,
                        vram_mb=4800,
                    )

            # C) LIGHTWEIGHT SUMMARIZATION TASK
            elif final_task_type == "summarization" and requirements.get("prefer_fast"):
                if self.registry.is_local_model_installed("gemma3:1b"):
                    return RoutingDecision(
                        task_type="summarization",
                        selected_model="gemma3:1b",
                        provider="ollama",
                        local=True,
                        reason="Resource-efficient local model selected for fast briefing summarization.",
                        fallback_used=False,
                        external_calls=0,
                        vram_mb=1200,
                    )
                else:
                    return RoutingDecision(
                        task_type="summarization",
                        selected_model=primary_sovereign,
                        provider="ollama",
                        local=True,
                        reason="Best available local reasoning model selected.",
                        fallback_used=False,
                        external_calls=0,
                        vram_mb=4800,
                    )

            # D) INSPECTION ANALYSIS / APPROVAL NOTE / DOCUMENT ANALYSIS / GENERAL REASONING
            else:
                reason = "Best available local reasoning model for grounded sovereign synthesis."
                if final_task_type == "inspection_analysis":
                    reason = "Best available local reasoning model with RAG SOP grounding & DOCX generator."
                elif final_task_type == "approval_note_generation":
                    reason = "Best available local reasoning model for statutory sign-off and approval note."

                return RoutingDecision(
                    task_type=final_task_type,
                    selected_model=primary_sovereign,
                    provider="ollama",
                    local=True,
                    reason=reason,
                    fallback_used=False,
                    external_calls=0,
                    vram_mb=4800,
                    details={"sovereign_rag_active": True},
                )

        # ─────────────────────────────────────────────────────────────────
        # CLOUD / AUTO ROUTING (Preserves existing cascade)
        # ─────────────────────────────────────────────────────────────────
        has_gemini = self.registry.has_cloud_credentials("gemini")
        has_groq = self.registry.has_cloud_credentials("groq")

        if has_gemini:
            return RoutingDecision(
                task_type=final_task_type,
                selected_model="gemini-3.6-flash",
                provider="gemini",
                local=False,
                reason="Standard cloud foundation model (Gemini Cascade active).",
                fallback_used=False,
                external_calls=1,
            )
        elif has_groq:
            return RoutingDecision(
                task_type=final_task_type,
                selected_model="openai/gpt-oss-120b",
                provider="groq",
                local=False,
                reason="Groq high-throughput cloud model active.",
                fallback_used=False,
                external_calls=1,
            )
        else:
            # Fall back to local Ollama if no cloud keys exist
            return RoutingDecision(
                task_type=final_task_type,
                selected_model=primary_sovereign,
                provider="ollama",
                local=True,
                reason="Cloud API keys not configured; seamlessly fallen back to local sovereign model.",
                fallback_used=True,
                fallback="local_ollama",
                external_calls=0,
                vram_mb=4800,
            )


# Global router singleton
model_router = LocalModelRouter()
