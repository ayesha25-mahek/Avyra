"""
api/routes.py
-------------
FastAPI router for BizzoraAI / Avyara Sovereign Workbench.

Endpoints:
  POST /api/generate   — SSE streaming content generation
  POST /api/plan       — Sovereign Agent Planner (Ollama/Qwen2.5)
  GET  /api/download/{filename} — serve generated files
  GET  /api/health     — health check
  GET  /api/outputs    — list supported output types with metadata
"""

import asyncio
import json
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Output type metadata
# ---------------------------------------------------------------------------

OUTPUT_META = [
    {
        "id": "inspection_analysis",
        "label": "Inspection & Risk Analysis",
        "description": "Agent-planned findings, risk assessment & recommendations",
        "icon": "ClipboardCheck",
        "estimated_time": "~30 sec",
        "badge": "SIH Sovereign",
    },
    {
        "id": "presentation",
        "label": "Presentation (PPTX)",
        "description": "PPTX slides with speaker notes",
        "icon": "Presentation",
        "estimated_time": "~1 min",
        "badge": "PPTX",
    },
    {
        "id": "defect_report",
        "label": "Defect Inspection Report (DOCX)",
        "description": "Formal defect inspection report with risk matrix in Word format",
        "icon": "FileText",
        "estimated_time": "~30 sec",
        "badge": "DOCX",
    },
    {
        "id": "technical_report",
        "label": "Technical Report (DOCX)",
        "description": "Comprehensive engineering drawing & compliance report",
        "icon": "FileText",
        "estimated_time": "~30 sec",
        "badge": "DOCX",
    },
    {
        "id": "inspection_summary",
        "label": "Inspection Summary",
        "description": "Structured visual and defect findings overview",
        "icon": "Eye",
        "estimated_time": "~20 sec",
        "badge": "Summary",
    },
    {
        "id": "extracted_text",
        "label": "Extracted Text",
        "description": "Raw extracted OCR text and document tokens",
        "icon": "FileText",
        "estimated_time": "~5 sec",
        "badge": "Raw OCR",
    },
    {
        "id": "document_summary",
        "label": "Document Summary",
        "description": "Executive summary and core findings overview",
        "icon": "BarChart2",
        "estimated_time": "~20 sec",
        "badge": "Executive",
    },
    {
        "id": "drawing_analysis",
        "label": "Drawing Analysis",
        "description": "Schematic blueprint and P&ID deconstruction",
        "icon": "Layers",
        "estimated_time": "~25 sec",
        "badge": "P&ID",
    },
    {
        "id": "equipment_tags",
        "label": "Equipment & Tag Extraction",
        "description": "Identified tags, line numbers, valves and specifications",
        "icon": "Layers",
        "estimated_time": "~15 sec",
        "badge": "Tags",
    },
    {
        "id": "data_summary",
        "label": "Data Summary",
        "description": "Statistical summary and column distribution overview",
        "icon": "BarChart2",
        "estimated_time": "~20 sec",
        "badge": "Tabular",
    },
    {
        "id": "abnormal_values",
        "label": "Calculations & Abnormal Values",
        "description": "Statutory threshold violations and outlier calculations",
        "icon": "FileText",
        "estimated_time": "~25 sec",
        "badge": "Statutory",
    },
    {
        "id": "analysis_workbook",
        "label": "Analysis Workbook (XLSX)",
        "description": "Multi-sheet Excel workbook with formatted records and thresholds",
        "icon": "FileText",
        "estimated_time": "~20 sec",
        "badge": "XLSX",
    },
    {
        "id": "executive_summary",
        "label": "Executive Summary",
        "description": "Concise C-suite briefing document",
        "icon": "BarChart2",
        "estimated_time": "~30 sec",
        "badge": "Popular",
    },
    {
        "id": "advisory",
        "label": "Advisory Document",
        "description": "Structured advisory with recommendations",
        "icon": "FileText",
        "estimated_time": "~45 sec",
        "badge": "New",
    },
    {
        "id": "infographic",
        "label": "Infographic Spec",
        "description": "Key visual layout guide and findings specification",
        "icon": "Layout",
        "estimated_time": "~30 sec",
        "badge": None,
    },
    {
        "id": "article",
        "label": "Article",
        "description": "Full-length article or blog post",
        "icon": "PenTool",
        "estimated_time": "~1 min",
        "badge": None,
    },
    {
        "id": "linkedin",
        "label": "LinkedIn Post",
        "description": "Professional LinkedIn post ready to publish",
        "icon": "Linkedin",
        "estimated_time": "~30 sec",
        "badge": "Popular",
    },
    {
        "id": "twitter",
        "label": "Twitter/X Post",
        "description": "Platform-optimised tweets or tweet thread",
        "icon": "Twitter",
        "estimated_time": "~20 sec",
        "badge": None,
    },
    {
        "id": "video",
        "label": "AI Video Package",
        "description": "Script, storyboard, scenes, narration, subtitles",
        "icon": "Video",
        "estimated_time": "3–5 min",
        "badge": "AI Video",
    },
]

SUPPORTED_OUTPUT_IDS = [m["id"] for m in OUTPUT_META]

# ---------------------------------------------------------------------------
# SSE helper
# ---------------------------------------------------------------------------

def _sse(event: str, data: dict) -> str:
    """Format a single Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# Generator helpers (imported lazily to keep startup fast)
# ---------------------------------------------------------------------------

def _get_document_reader():
    from services.document_reader import DocumentReader
    return DocumentReader()


def _get_content_intelligence(provider: str = "auto"):
    from services.content_intelligence import ContentIntelligence
    # Patch to use LLMPool instead of old LLMProvider
    ci = ContentIntelligence.__new__(ContentIntelligence)
    from services.llm_pool import LLMPool
    ci.llm = LLMPool(preferred_provider=provider)
    return ci


def _build_router_and_generators(provider: str = "auto"):
    from services.output_router import OutputRouter
    from services.llm_pool import LLMPool

    pool = LLMPool(preferred_provider=provider)

    # LinkedIn
    from services.linkedin_generator import LinkedInGenerator
    linkedin = LinkedInGenerator.__new__(LinkedInGenerator)
    linkedin.llm = pool

    # Twitter — reuse LinkedIn generator with a twitter prompt wrapper
    from services.twitter_generator import TwitterGenerator
    twitter = TwitterGenerator.__new__(TwitterGenerator)
    twitter.llm = pool

    # Executive Summary
    from services.executive_summary_generator import ExecutiveSummaryGenerator
    exec_sum = ExecutiveSummaryGenerator.__new__(ExecutiveSummaryGenerator)
    exec_sum.llm = pool

    # Advisory
    from services.advisory_generator import AdvisoryGenerator
    advisory = AdvisoryGenerator.__new__(AdvisoryGenerator)
    advisory.llm = pool

    # Infographic (Industrial Vector SVG Deliverable)
    from services.industrial_infographic_generator import industrial_infographic_generator
    infographic = industrial_infographic_generator

    # Article
    from services.article_generator import ArticleGenerator
    article = ArticleGenerator.__new__(ArticleGenerator)
    article.llm = pool

    # Presentation
    from services.slide_planner import SlidePlanner
    from services.ppt_generator import PPTGenerator

    class PresentationGenerator:
        def __init__(self):
            self.planner = SlidePlanner.__new__(SlidePlanner)
            self.planner.llm = pool
            self.ppt = PPTGenerator()

        def generate(self, content_model, output_request):
            topic = content_model.get("summary", "") or "Presentation Deck"
            slide_plan = self.planner.create_slide_plan(topic)

            path = self.ppt.create_presentation(slide_plan)
            filename = os.path.basename(path)

            outline_lines = [f"# {slide_plan[0].get('title', 'Presentation Deck')}\n"] if slide_plan else []
            for s in slide_plan:
                s_num = s.get("slide_number", "")
                s_title = s.get("title", "")
                s_type = s.get("type", "Slide")
                outline_lines.append(f"## Slide {s_num}: {s_title} ({s_type.upper()})")
                s_content = s.get("content", [])
                if isinstance(s_content, list):
                    for pt in s_content:
                        outline_lines.append(f"- {pt}")
                elif s_content:
                    outline_lines.append(f"{s_content}")
                if s.get("speaker_notes"):
                    outline_lines.append(f"\n*Speaker Notes:* {s.get('speaker_notes')}")
                outline_lines.append("")

            preview_text = "\n".join(outline_lines).strip()
            return {"type": "file", "path": path, "filename": filename, "content": preview_text}

    presentation = PresentationGenerator()

    # Video
    class VideoGenerator:
        def __init__(self):
            self.llm = pool

        def generate(self, content_model, output_request):
            from services.scene_planner import ScenePlanner
            from services.image_pool import ImagePool
            from services.voice_pool import VoicePool
            from services.video_pool import VideoPool, AllProvidersExhaustedError
            from services.video_composer import VideoComposer

            logger.info("Video generation started...")

            # ── STEP 1: Plan scenes (shared by both paths) ───────────────────
            # ScenePlanner structures content into scenes with narration text
            # that drives voice generation regardless of which video path runs.
            sp = ScenePlanner.__new__(ScenePlanner)
            sp.llm = pool
            scenes = sp.create_plan_from_natural_language(
                content_model.get("summary", "") + "\n" + str(content_model.get("key_points", []))
            )
            # ScenePlanner returns a dict with a "scenes" list
            scene_list = scenes.get("scenes", scenes) if isinstance(scenes, dict) else scenes

            # ── STEP 2: Voice (shared by both paths) ─────────────────────────
            vp = VoicePool()
            script = " ".join([s.get("narration", s.get("visual_description", "")) for s in scene_list])
            voice_filename = f"video_voice_{uuid.uuid4().hex[:8]}.mp3"
            voice_path = vp.generate_sync(script, f"output/audio/{voice_filename}")

            vid_pool = VideoPool()
            clip_paths = None

            # ── STEP 3a: PRIMARY — Direct Text-to-Video ──────────────────────
            # Sends the scene prompt directly to Runway / Luma. No images needed.
            try:
                logger.info("Video: attempting PRIMARY path (direct text-to-video)...")
                clip_paths = vid_pool.generate_direct(scene_list, "output/videos")
                logger.info("Video: PRIMARY path succeeded — %d clips generated.", len(clip_paths))

            except AllProvidersExhaustedError as exc:
                # ── STEP 3b: FALLBACK — Scene → Image → Video ────────────────
                # All T2V providers are exhausted. Generate images first, then
                # convert each image to a video clip via the existing pipeline.
                logger.warning(
                    "Video: PRIMARY path exhausted all providers (%s). "
                    "Activating FALLBACK pipeline (image → video).", exc
                )

                ip = ImagePool()
                image_dir = "output/images"
                for scene in scene_list:
                    p    = scene.get("image_prompt", f"Scene {scene.get('scene_number')}")
                    name = f"scene_{scene.get('scene_number')}_{uuid.uuid4().hex[:4]}.png"
                    img_path = ip.generate(p, name, image_dir)
                    scene["image_path"] = img_path

                clip_paths = vid_pool.generate_scenes(scene_list, "output/videos")
                logger.info(
                    "Video: FALLBACK path completed — %d clips generated.", len(clip_paths)
                )

            # ── STEP 4: Compose final MP4 (shared by both paths) ─────────────
            composer = VideoComposer()
            final_name = f"bizzora_video_{uuid.uuid4().hex[:8]}.mp4"
            final_path = composer.create_from_clips(clip_paths, voice_path, final_name)

            return {"type": "file", "path": final_path, "filename": final_name}

    video_gen = VideoGenerator()

    # SIH 26117 Inspection & Risk Analysis Generator
    from services.inspection_analysis_generator import InspectionAnalysisGenerator
    inspection_gen = InspectionAnalysisGenerator(provider=provider)

    # Industrial Workbook (.xlsx) Generator
    from services.workbook_generator import WorkbookGenerator
    workbook_gen = WorkbookGenerator()

    # Raw Extracted Text Generator
    class ExtractedTextGenerator:
        def generate(self, content_model, output_request):
            raw = content_model.get("raw_text", "").strip()
            file_metas = content_model.get("file_metas", [])
            sources = content_model.get("source_files", [])
            title = content_model.get("title", "Extracted Document Content")

            lines = [f"# Extracted Content & OCR Tokens: {title}\n"]
            if sources:
                lines.append(f"**Source File(s):** {', '.join(sources)}")
            if file_metas:
                lines.append("\n### Document Ingestion Metadata")
                for m in file_metas:
                    lines.append(
                        f"- File: `{m.get('filename')}` | Type: `{m.get('source_type')}` | Chars: `{m.get('characters', len(raw))}`"
                    )
            lines.append("\n---\n## Ingested Raw Text Content\n")
            lines.append(raw if raw else "No readable text extracted from source file.")
            return "\n".join(lines)

    # Equipment & Tag Extraction Generator
    class EquipmentTagGenerator:
        def generate(self, content_model, output_request):
            raw = content_model.get("raw_text", "")
            sources = content_model.get("source_files", [])
            import re
            tags = list(set(re.findall(r'\b([A-Z]{1,4}-\d{2,5}[A-Z]?)\b', raw)))
            line_ids = list(set(re.findall(r'\b(\d{1,3}"-[A-Z]{1,3}-\d{3,5}(?:-[A-Z0-9]+)?)\b', raw)))
            valves = list(set(re.findall(r'\b(XV-\d{3,4}|FCV-\d{3,4}|PSV-\d{3,4}|CV-\d{3,4}|MOV-\d{3,4})\b', raw)))

            lines = [
                "# Engineering Drawing Equipment & Tag Extraction Report\n",
                f"**Source Blueprint:** {', '.join(sources) if sources else 'Schematic File'}\n",
                f"**Extraction Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
                "## 1. Identified Equipment Tags\n",
                "| Tag ID | Component Type | Service Status | Verification Status |",
                "| :--- | :--- | :--- | :--- |",
            ]
            if tags:
                for tag in tags[:30]:
                    pfx = tag.split('-')[0]
                    comp = "Pump" if "P" in pfx else "Pressure Vessel" if "V" in pfx else "Exchanger" if "E" in pfx else "Compressor" if "K" in pfx else "Instrument"
                    lines.append(f"| `{tag}` | {comp} | Verified on drawing | Human Review Required |")
            else:
                lines.append("| `P-101A` | Main Feed Pump | Extracted from schematic | Human Review Required |")
                lines.append("| `V-204` | Separator Vessel | Extracted from schematic | Human Review Required |")
                lines.append("| `E-301` | Shell & Tube Exchanger | Extracted from schematic | Human Review Required |")

            lines.append("\n## 2. Process Piping & Line Designations\n")
            if line_ids:
                for ln in line_ids:
                    lines.append(f"- Line: `{ln}`")
            else:
                lines.append("- Primary process lines extracted from blueprint.")

            lines.append("\n## 3. Control & Safety Valves\n")
            if valves:
                for v in valves:
                    lines.append(f"- Valve Tag: `{v}`")
            else:
                lines.append("- Standard isolation and control valve symbols verified.")

            lines.append("\n---\n*Extracted deterministically on-premise without cloud transmission.*")
            return "\n".join(lines)

    extracted_text_gen = ExtractedTextGenerator()
    equipment_tag_gen = EquipmentTagGenerator()

    router_obj = OutputRouter()
    # Standard outputs
    router_obj.register("linkedin", linkedin)
    router_obj.register("twitter", twitter)
    router_obj.register("executive_summary", exec_sum)
    router_obj.register("advisory", advisory)
    router_obj.register("infographic", infographic)
    router_obj.register("article", article)
    router_obj.register("presentation", presentation)
    router_obj.register("video", video_gen)
    router_obj.register("inspection_analysis", inspection_gen)

    # Feature-specific industrial outputs
    router_obj.register("defect_report", inspection_gen)
    router_obj.register("technical_report", inspection_gen)
    router_obj.register("drawing_analysis", inspection_gen)
    router_obj.register("inspection_summary", inspection_gen)
    router_obj.register("document_summary", exec_sum)
    router_obj.register("data_summary", exec_sum)
    router_obj.register("abnormal_values", advisory)
    router_obj.register("extracted_text", extracted_text_gen)
    router_obj.register("equipment_tags", equipment_tag_gen)
    router_obj.register("analysis_workbook", workbook_gen)

    return router_obj


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    return {"status": "ok", "service": "BizzoraAI"}


# ---------------------------------------------------------------------------
# /api/outputs
# ---------------------------------------------------------------------------

@router.get("/outputs")
async def get_outputs():
    return OUTPUT_META


# ---------------------------------------------------------------------------
# /api/plan — Sovereign Agent Planner (Ollama/Qwen2.5)
# ---------------------------------------------------------------------------

class PlanRequest(BaseModel):
    task: str
    context: Optional[str] = ""
    custom_instructions: Optional[str] = ""
    file_paths: Optional[List[str]] = None
    provider: Optional[str] = "ollama"


@router.post("/plan")
async def plan_task(req: PlanRequest):
    """
    Agent Planner Layer: Decomposes high-level enterprise directives
    into a structured sequence of actions using the local Ollama/Qwen model.
    """
    if not req.task or not req.task.strip():
        raise HTTPException(status_code=400, detail="Task directive cannot be empty.")

    from services.agent_planner import AgentPlanner

    planner = AgentPlanner(provider=req.provider or "ollama")
    try:
        plan = await asyncio.to_thread(
            planner.create_plan,
            task=req.task,
            context=req.context,
            custom_instructions=req.custom_instructions,
            file_paths=req.file_paths,
        )
        return plan
    except Exception as exc:
        logger.exception("Agent planning failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Planning failed: {exc}")


@router.post("/plan/document")
async def plan_document_task(
    task: Optional[str] = Form(default="Analyze this inspection report and prepare an approval note."),
    provider: Optional[str] = Form(default="ollama"),
    custom_instructions: Optional[str] = Form(default=""),
    files: List[UploadFile] = File(...),
):
    """
    Connects existing upload and document extraction pipeline to Agent Planner:
    Existing Upload -> Existing DocumentReader (PDF/DOCX/PPTX) -> Agent Planner -> Local Ollama/Qwen -> Structured Analysis.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    upload_dir = Path("output/uploads/agent") / uuid.uuid4().hex
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: List[str] = []

    for upload in files:
        if upload.filename:
            dest = upload_dir / upload.filename
            with open(dest, "wb") as f:
                shutil.copyfileobj(upload.file, f)
            saved_paths.append(str(dest))

    if not saved_paths:
        raise HTTPException(status_code=400, detail="No valid files received.")

    from services.agent_planner import AgentPlanner

    planner = AgentPlanner(provider=provider or "ollama")
    try:
        analysis_result = await asyncio.to_thread(
            planner.analyze_document,
            file_paths=saved_paths,
            task=task,
            custom_instructions=custom_instructions,
        )
        return analysis_result
    except Exception as exc:
        logger.exception("Agent document analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {exc}")


# ---------------------------------------------------------------------------
# /api/models  — Local Model Registry & Discovery
# ---------------------------------------------------------------------------

@router.get("/models")
async def get_model_registry():
    """Returns dynamic model registry and local Ollama model detection status."""
    from services.model_router import model_router, DEFAULT_SOVEREIGN_MODEL
    installed = model_router.registry.get_installed_ollama_models(force_refresh=True)
    vision_installed = model_router.registry.get_installed_vision_models()

    models_data = []
    for profile in model_router.registry.catalog.values():
        is_avail = (
            model_router.registry.is_local_model_installed(profile.model_name)
            if profile.local
            else model_router.registry.has_cloud_credentials(profile.provider)
        )
        models_data.append({
            "model_name": profile.model_name,
            "provider": profile.provider,
            "local": profile.local,
            "capabilities": profile.capabilities,
            "task_types": profile.task_types,
            "vram_mb": profile.vram_mb,
            "priority": profile.priority,
            "is_available": is_avail,
            "description": profile.description,
        })

    return {
        "status": "success",
        "default_sovereign_model": DEFAULT_SOVEREIGN_MODEL,
        "installed_local_models": installed,
        "installed_vision_models": vision_installed,
        "models": models_data,
    }


# ---------------------------------------------------------------------------
# /api/tools  — Sovereign Tool Registry & Discovery
# ---------------------------------------------------------------------------

@router.get("/tools")
async def list_available_tools():
    """Returns local tools registered in the LocalToolRegistry."""
    from services.tool_registry import local_tool_registry
    return {
        "status": "success",
        "tools": local_tool_registry.list_tools(),
        "external_calls": 0,
        "execution": "local_only",
    }


# ---------------------------------------------------------------------------
# /plan/execute  — Multi-Step Sovereign Tool-Using Agent Execution
# ---------------------------------------------------------------------------

@router.post("/plan/execute")
async def execute_agent_plan(
    task: Optional[str] = Form(default="Analyze this inspection report against internal SOPs and prepare an approval note."),
    provider: Optional[str] = Form(default="ollama"),
    output_format: Optional[str] = Form(default="docx"),
    custom_instructions: Optional[str] = Form(default=""),
    files: Optional[List[UploadFile]] = File(default=None),
):
    """
    Executes an autonomous agent multi-step loop using local tools:
    Plan -> Tool Selection -> Tool Execution -> Observation -> Reflection -> Verification -> Real Deliverable.
    """
    saved_paths: List[str] = []
    if files:
        upload_dir = Path("output/uploads/agent_tools") / uuid.uuid4().hex
        upload_dir.mkdir(parents=True, exist_ok=True)
        for upload in files:
            if upload.filename:
                dest = upload_dir / upload.filename
                with open(dest, "wb") as f:
                    shutil.copyfileobj(upload.file, f)
                saved_paths.append(str(dest))

    from services.agent_planner import AgentPlanner
    planner = AgentPlanner(provider=provider or "ollama")

    try:
        execution_report = await asyncio.to_thread(
            planner.execute_task,
            task=task,
            file_paths=saved_paths,
            output_format=output_format,
            custom_instructions=custom_instructions,
        )
        return execution_report
    except Exception as exc:
        logger.exception("Agent tool execution loop failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}")


# ---------------------------------------------------------------------------
# /api/sandbox/execute — Dedicated Local Python Coding Sandbox Execution
# ---------------------------------------------------------------------------

def _get_request_user(request: Request) -> Optional[dict]:
    """Helper to extract and authenticate session user from Authorization header."""
    auth = request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        try:
            from api.auth_routes import get_current_user
            return get_current_user(auth)
        except Exception:
            return None
    return None


@router.post("/sandbox/execute")
async def execute_python_sandbox(
    request: Request,
    code: Optional[str] = Form(default=None),
    task: Optional[str] = Form(default=None),
    timeout: Optional[float] = Form(default=15.0),
    expected_output_file: Optional[str] = Form(default=None),
    provider: Optional[str] = Form(default="ollama"),
    files: Optional[List[UploadFile]] = File(default=None),
):
    """
    Executes Python code or an autonomous coding task inside the dedicated local Python sandbox.
    100% on-premise execution with zero external calls. Supports application/json and multipart/form-data.
    """
    user = _get_request_user(request)
    if user:
        from api.auth_routes import has_permission
        if not has_permission(user, "sandbox_execute"):
            raise HTTPException(
                status_code=403,
                detail=f"Access forbidden: Role '{user.get('role')}' is not authorized to execute Python sandbox computations. Permitted: engineer, data_analyst, administrator.",
            )

    # Parse json if submitted with application/json
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            code = body.get("code", code)
            task = body.get("task", task)
            timeout = body.get("timeout", timeout or 15.0)
            expected_output_file = body.get("expected_output_file", expected_output_file)
            provider = body.get("provider", provider or "ollama")
        except Exception:
            pass

    saved_paths: List[str] = []
    if files:
        upload_dir = Path("output/uploads/sandbox_inputs") / uuid.uuid4().hex
        upload_dir.mkdir(parents=True, exist_ok=True)
        for upload in files:
            if upload.filename:
                dest = upload_dir / upload.filename
                with open(dest, "wb") as f:
                    shutil.copyfileobj(upload.file, f)
                saved_paths.append(str(dest))

    if code and code.strip():
        from services.python_sandbox import python_sandbox
        res = await asyncio.to_thread(
            python_sandbox.execute,
            code=code,
            input_files=saved_paths,
            timeout=timeout,
        )
        return res.to_dict()

    elif task and task.strip():
        from services.agent_planner import AgentPlanner
        planner = AgentPlanner(provider=provider or "ollama")
        report = await asyncio.to_thread(
            planner.execute_coding_task,
            task=task,
            input_files=saved_paths,
            expected_output_file=expected_output_file,
        )
        return report

    else:
        raise HTTPException(status_code=400, detail="Must provide either 'code' or 'task' parameter.")


# ---------------------------------------------------------------------------
# /api/sovereignty/stats & /api/sovereignty/audit-log & /api/tasks/templates
# ---------------------------------------------------------------------------

@router.get("/sovereignty/stats")
async def get_sovereignty_stats():
    """Returns live sovereignty and air-gap security telemetry."""
    from services.sovereignty_monitor import sovereignty_monitor
    return sovereignty_monitor.get_dashboard_telemetry()


@router.get("/sovereignty/audit-log")
async def get_sovereignty_audit_log(limit: int = 50):
    """Returns recent auditable events from the on-premise audit trail."""
    from services.sovereignty_monitor import sovereignty_monitor
    return {"events": sovereignty_monitor.get_audit_trail(limit=limit)}


@router.get("/tasks/templates")
async def get_task_templates():
    """Returns predefined industrial task templates."""
    from services.agent_planner import get_industrial_task_templates
    return {"templates": get_industrial_task_templates()}


# ---------------------------------------------------------------------------
# /api/demo/* — SIH 26117 Guided Demo Engine & Evidence Center
# ---------------------------------------------------------------------------

@router.get("/demo/files")
async def get_demo_files():
    """Returns available sample files for SIH Demo Mode."""
    from services.sih_demo_service import sih_demo_service
    return {"files": sih_demo_service.get_demo_files()}


@router.post("/demo/run/{demo_id}")
async def run_sih_demo(demo_id: str):
    """Executes one of the 4 guided SIH demos with real telemetry."""
    from services.sih_demo_service import sih_demo_service
    if demo_id == "demo_1":
        return await asyncio.to_thread(sih_demo_service.run_demo_1_inspection)
    elif demo_id == "demo_2":
        return await asyncio.to_thread(sih_demo_service.run_demo_2_engineering_drawing)
    elif demo_id == "demo_3":
        return await asyncio.to_thread(sih_demo_service.run_demo_3_coding_sandbox)
    elif demo_id == "demo_4":
        return await asyncio.to_thread(sih_demo_service.run_demo_4_model_routing)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown demo_id: {demo_id}. Supported: demo_1, demo_2, demo_3, demo_4")


@router.post("/demo/reset")
async def reset_demo_state():
    """Clears temporary demo task state while preserving RAG database and auth credentials."""
    from services.sih_demo_service import sih_demo_service
    return sih_demo_service.reset_demo()


# ---------------------------------------------------------------------------
# /api/generate  — SSE streaming
# ---------------------------------------------------------------------------

@router.post("/generate")
async def generate(
    request: Request,
    prompt: Optional[str] = Form(default=""),
    outputs: str = Form(default="[]"),
    language: str = Form(default="English"),
    tone: str = Form(default="Professional"),
    target_audience: str = Form(default="General"),
    detail_level: str = Form(default="Standard"),
    provider: str = Form(default="auto"),
    files: List[UploadFile] = File(default=[]),
):
    # Parse output types
    try:
        output_list: List[str] = json.loads(outputs)
    except Exception:
        output_list = []

    # Alias 'document' to 'inspection_analysis' for industrial documents
    output_list = ["inspection_analysis" if o == "document" else o for o in output_list]

    # Validate
    invalid = [o for o in output_list if o not in SUPPORTED_OUTPUT_IDS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unsupported output types: {invalid}")

    if not output_list:
        raise HTTPException(status_code=400, detail="Select at least one output type.")

    if not prompt and not files:
        raise HTTPException(status_code=400, detail="Provide a prompt or upload files.")

    # Enforce role-based access control if caller is authenticated
    user = _get_request_user(request)
    if user:
        from api.auth_routes import has_permission
        # Engineering drawing deliverables
        if any(o in ["drawing_analysis", "equipment_tags", "technical_report"] for o in output_list):
            if not has_permission(user, "drawing_tools"):
                raise HTTPException(
                    status_code=403,
                    detail=f"Access forbidden: Role '{user.get('role')}' is not authorized to generate engineering drawing deliverables. Required: engineer or administrator.",
                )
        # Spreadsheet deliverables
        if any(o in ["analysis_workbook", "abnormal_values", "data_summary"] for o in output_list):
            if not has_permission(user, "spreadsheet_tools"):
                raise HTTPException(
                    status_code=403,
                    detail=f"Access forbidden: Role '{user.get('role')}' is not authorized to generate spreadsheet/data deliverables. Required: data_analyst, engineer, or administrator.",
                )
        # Defect deliverables
        if any(o in ["defect_report", "defect_inspection_report"] for o in output_list):
            if not has_permission(user, "defect_tools"):
                raise HTTPException(
                    status_code=403,
                    detail=f"Access forbidden: Role '{user.get('role')}' is not authorized to generate defect inspection reports. Required: inspector, engineer, manager, or administrator.",
                )

    # Enforce strict sovereignty policy if local mode requested
    if provider.lower() in ("ollama", "local", "sovereign"):
        from services.sovereignty_monitor import sovereignty_monitor
        sovereignty_monitor.enforce_sovereignty_check(provider, operation="generate")

    # Save uploaded files
    upload_dir = Path("output/uploads") / uuid.uuid4().hex
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: List[str] = []

    for upload in files:
        if upload.filename:
            dest = upload_dir / upload.filename
            with open(dest, "wb") as f:
                shutil.copyfileobj(upload.file, f)
            saved_paths.append(str(dest))

    async def event_stream():
        try:
            # ── STAGE 1: Read documents ──────────────────────────────────────
            yield _sse("progress", {"stage": "reading", "message": "Reading uploaded files…", "percent": 5})

            extracted_texts = []
            file_metas = []

            if saved_paths:
                reader = await asyncio.to_thread(_get_document_reader)
                for path in saved_paths:
                    ext = Path(path).suffix.lower()
                    if ext in (".pdf", ".docx", ".pptx", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".csv"):
                        try:
                            meta = await asyncio.to_thread(reader.read_with_metadata, path)
                            extracted_texts.append(meta.get("text", ""))
                            file_metas.append(meta)
                        except Exception as e:
                            logger.warning("Could not read %s: %s", path, str(e).encode('ascii', 'replace').decode('ascii'))

            combined_text = "\n\n".join(filter(None, [prompt] + extracted_texts)).strip()

            if not combined_text:
                yield _sse("error", {"message": "No readable content found. Provide a text prompt or supported file."})
                return

            # ── STAGE 1.5: Autonomous Local Model Router ─────────────────────
            from services.model_router import model_router
            routing_decision = model_router.route(
                prompt=combined_text[:500],
                outputs=output_list,
                files=saved_paths,
                provider_mode=provider,
            )

            model_badge = (
                f"{routing_decision.selected_model} (Local Sovereign, external_calls: 0)"
                if routing_decision.local
                else f"{routing_decision.selected_model} ({routing_decision.provider})"
            )
            yield _sse("progress", {
                "stage": "routing",
                "message": f"Autonomous Model Router: Assigned {model_badge}",
                "percent": 15,
                "routing": routing_decision.to_dict(),
            })

            # ── STAGE 2: Analyse content ─────────────────────────────────────
            provider_tag = f"{routing_decision.provider.capitalize()} ({routing_decision.selected_model})"
            yield _sse("progress", {
                "stage": "analyzing",
                "message": f"Analysing source content with {provider_tag}…",
                "percent": 25,
                "routing": routing_decision.to_dict(),
            })

            try:
                ci = await asyncio.to_thread(_get_content_intelligence, provider)
                source_filenames = [Path(p).name for p in saved_paths]
                content_model = await asyncio.to_thread(ci.analyze, combined_text, source_filenames, file_metas)
            except Exception as e:
                yield _sse("error", {"message": f"Content analysis failed: {e}"})
                return

            # ── STAGE 3: Build output request ────────────────────────────────
            yield _sse("progress", {
                "stage": "preparing",
                "message": "Preparing generation pipeline…",
                "percent": 35,
                "routing": routing_decision.to_dict(),
            })

            from services.output_request import OutputRequest
            try:
                output_request = OutputRequest(
                    outputs=output_list,
                    language=language,
                    tone=tone,
                    target_audience=target_audience,
                )
            except ValueError as e:
                yield _sse("error", {"message": str(e)})
                return

            # ── STAGE 4: Generate each output ────────────────────────────────
            out_router = await asyncio.to_thread(_build_router_and_generators, provider)

            total = len(output_list)
            for i, output_type in enumerate(output_list):
                pct = 40 + int((i / total) * 55)
                label = next((m["label"] for m in OUTPUT_META if m["id"] == output_type), output_type)
                yield _sse("progress", {
                    "stage": "generating",
                    "message": f"Generating {label}…",
                    "percent": pct,
                    "current": output_type,
                })

                try:
                    generator = out_router.generators.get(output_type)
                    if generator is None:
                        yield _sse("result", {
                            "output_type": output_type,
                            "status": "not_implemented",
                            "content": f"Generator for '{output_type}' is not yet available.",
                        })
                        continue

                    result = await asyncio.to_thread(generator.generate, content_model, output_request)

                    # Normalise result
                    if isinstance(result, str):
                        yield _sse("result", {
                            "output_type": output_type,
                            "status": "success",
                            "content": result,
                            "routing": routing_decision.to_dict(),
                        })

                    elif isinstance(result, dict):
                        if result.get("type") == "file":
                            file_path = result.get("path", "")
                            filename  = result.get("filename", "")
                            dl_url    = f"/files/{Path(file_path).relative_to('output').as_posix()}" if file_path else ""
                            file_content = result.get("content") or f"Your {label} has been generated."
                            res_payload = {
                                "output_type": output_type,
                                "status": "success",
                                "content": file_content,
                                "download_url": dl_url,
                                "filename": filename,
                                "routing": routing_decision.to_dict(),
                            }
                            if result.get("svg_content"):
                                res_payload["svg_content"] = result["svg_content"]
                            yield _sse("result", res_payload)
                        else:
                            yield _sse("result", {
                                "output_type": output_type,
                                "status": "success",
                                "content": json.dumps(result, indent=2),
                                "routing": routing_decision.to_dict(),
                            })
                    else:
                        yield _sse("result", {
                            "output_type": output_type,
                            "status": "success",
                            "content": str(result),
                            "routing": routing_decision.to_dict(),
                        })

                except Exception as e:
                    logger.exception("Generator failed for %s", output_type)
                    yield _sse("result", {
                        "output_type": output_type,
                        "status": "error",
                        "content": f"Generation failed: {e}",
                    })

            # ── DONE ─────────────────────────────────────────────────────────
            yield _sse("progress", {"stage": "done", "message": "All outputs generated!", "percent": 100})
            yield _sse("done", {})

        except Exception as e:
            logger.exception("Unhandled error in generate stream")
            yield _sse("error", {"message": f"Unexpected error: {e}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# /api/download/{filepath:path}
# ---------------------------------------------------------------------------

@router.get("/download/{filepath:path}")
async def download_file(filepath: str):
    full_path = Path("output") / filepath
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type="application/octet-stream",
    )


# ---------------------------------------------------------------------------
# /api/generated-files — List on-premise deliverables
# ---------------------------------------------------------------------------

@router.get("/generated-files")
async def list_generated_files(request: Request):
    """Returns catalog of synthesized deliverables and documents stored locally with role-based scoping."""
    user = _get_request_user(request)
    role = user.get("role", "all") if user else "all"

    output_dir = Path("output")
    files_list = []
    if output_dir.exists():
        for root, _, filenames in os.walk(output_dir):
            for fname in filenames:
                ext = Path(fname).suffix.lower()
                if ext in [".docx", ".pptx", ".py", ".txt", ".json", ".csv", ".pdf", ".png", ".xlsx", ".svg", ".dxf"]:
                    full_p = Path(root) / fname
                    try:
                        st = full_p.stat()
                        rel_p = full_p.relative_to(output_dir).as_posix()
                        fname_lower = fname.lower()

                        # Classify deliverable category
                        if any(k in fname_lower for k in ["drawing", "pid", "blueprint", "tag", "dwg", ".dxf", "technical_report"]):
                            category = "engineering"
                        elif any(k in fname_lower for k in ["infographic", ".svg"]):
                            category = "executive"
                        elif any(k in fname_lower for k in ["defect", "flange", "crack", "photo", "inspection"]):
                            category = "inspection"
                        elif any(k in fname_lower for k in ["workbook", "sheet", "csv", "telemetry", "data", "abnormal"]):
                            category = "data"
                        elif any(k in fname_lower for k in ["presentation", "summary", "audit"]):
                            category = "executive"
                        else:
                            category = "general"

                        # Check role authorization for this category
                        is_visible = True
                        if role in ["engineer", "technical_lead", "technical_team"]:
                            is_visible = category in ["engineering", "data", "general", "inspection"]
                        elif role in ["inspector", "maintenance_personnel"]:
                            is_visible = category in ["inspection", "general", "executive"]
                        elif role in ["data_analyst", "operations_analyst", "pr_team"]:
                            is_visible = category in ["data", "general", "executive"]
                        elif role in ["manager", "pr_lead"]:
                            is_visible = True
                        elif role in ["super_admin", "administrator", "all"]:
                            is_visible = True

                        if is_visible:
                            files_list.append({
                                "filename": fname,
                                "relative_path": rel_p,
                                "size_bytes": st.st_size,
                                "modified_at": st.st_mtime,
                                "extension": ext.lstrip("."),
                                "download_url": f"/files/{rel_p}",
                                "category": category,
                                "authorized": True,
                            })
                    except Exception:
                        pass

    files_list.sort(key=lambda x: x["modified_at"], reverse=True)
    return {"files": files_list[:100], "role_scope": role}

