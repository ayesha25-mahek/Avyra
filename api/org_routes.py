"""
api/org_routes.py
-----------------
API Router for Organization & Workspace Configuration in Avyara.

Endpoints:
  GET  /api/org/config            — Get active organization and workspace settings
  POST /api/org/config            — Update organization settings (Administrator only)
  GET  /api/org/presets           — List available industry presets
  POST /api/org/presets/{preset}  — Apply industry preset (Administrator only)
  POST /api/org/workspace/switch  — Switch active project workspace
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from services.org_config_service import org_config_service
from api.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/org", tags=["organization-configuration"])


class UpdateOrgConfigRequest(BaseModel):
    org_name: Optional[str] = None
    industry: Optional[str] = None
    facility_location: Optional[str] = None
    workspaces: Optional[List[Dict[str, Any]]] = None
    active_workspace_id: Optional[str] = None
    terminology: Optional[Dict[str, str]] = None
    enabled_modules: Optional[List[str]] = None


class SwitchWorkspaceRequest(BaseModel):
    workspace_id: str = Field(..., description="Target workspace ID to activate")


@router.get("/config")
async def get_org_config():
    """Retrieve current organization metadata, terminology, and workspaces."""
    return org_config_service.get_config()


@router.post("/config")
async def update_org_config(
    req: UpdateOrgConfigRequest,
    authorization: Optional[str] = Header(None),
):
    """Update organization parameters. Restricted to Administrators."""
    user = get_current_user(authorization)
    allowed_roles = ["super_admin", "administrator"]
    if user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Only Administrators can modify organization configuration.",
        )

    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = org_config_service.update_config(updates)
    return {"status": "success", "config": updated}


@router.get("/presets")
async def list_industry_presets():
    """Returns available industrial presets (Refinery, Automotive, Aerospace, Pharma)."""
    return {"presets": org_config_service.get_presets()}


@router.post("/presets/{preset_id}")
async def apply_industry_preset(
    preset_id: str,
    authorization: Optional[str] = Header(None),
):
    """Applies an industry template. Restricted to Administrators."""
    user = get_current_user(authorization)
    allowed_roles = ["super_admin", "administrator"]
    if user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Only Administrators can apply organization presets.",
        )

    try:
        updated = org_config_service.apply_preset(preset_id)
        return {"status": "success", "preset_applied": preset_id, "config": updated}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/workspace/switch")
async def switch_workspace(
    req: SwitchWorkspaceRequest,
    authorization: Optional[str] = Header(None),
):
    """Switches active workspace context for the current session."""
    # Authenticated user check
    _ = get_current_user(authorization)
    try:
        updated = org_config_service.switch_workspace(req.workspace_id)
        return {"status": "success", "active_workspace_id": req.workspace_id, "config": updated}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
