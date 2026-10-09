"""
main.py  —  BizzoraAI FastAPI application entry point
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import router
from api.rag_routes import router as rag_router
from api.auth_routes import router as auth_router
from api.org_routes import router as org_router
from api.engineering_routes import router as engineering_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="BizzoraAI",
    description="AI-powered content transformation engine",
    version="2.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server and any localhost origin
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(org_router, prefix="/api")
app.include_router(engineering_router, prefix="/api")

# ---------------------------------------------------------------------------
# Static file serving for generated output files
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/files", StaticFiles(directory=str(OUTPUT_DIR)), name="files")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# ---------------------------------------------------------------------------
# Startup: ensure all output sub-directories exist
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def create_output_dirs():
    for sub in ["uploads", "images", "videos", "audio", "plans",
                "presentations", "content", "slide_plans", "drawings", "spreadsheets", "documents", "infographics"]:
        (OUTPUT_DIR / sub).mkdir(parents=True, exist_ok=True)
    logger.info("BizzoraAI started — output directory ready at '%s'", OUTPUT_DIR)


# ---------------------------------------------------------------------------
# Frontend Static Files (Single Unified URL)
# ---------------------------------------------------------------------------
FRONTEND_DIST = Path("frontend/dist")
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {
            "service": "BizzoraAI",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/api/health",
        }


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)