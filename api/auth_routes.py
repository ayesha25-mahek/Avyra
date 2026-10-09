"""
api/auth_routes.py
------------------
Enterprise Authentication & Role-Based Access Control (RBAC) service for Avyra.
Supports secure salted PBKDF2-HMAC-SHA256 password verification, Supabase integration,
role-gated access control, and session token issuance.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["authentication"])

# Secret used to sign session tokens
TOKEN_SECRET = os.getenv("AUTH_TOKEN_SECRET", secrets.token_hex(32))

# ---------------------------------------------------------------------------
# Password Hashing Utilities (PBKDF2-HMAC-SHA256 with cryptographically random salt)
# ---------------------------------------------------------------------------
def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hashes a password with PBKDF2-HMAC-SHA256 using a 32-byte salt."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
        dklen=32
    )
    return key.hex(), salt


def verify_password(provided_password: str, stored_hash: str, salt: str) -> bool:
    """Securely verifies password using constant-time comparison."""
    computed_hash, _ = hash_password(provided_password, salt)
    return hmac.compare_digest(computed_hash, stored_hash)


# ---------------------------------------------------------------------------
# Pre-seeded Authorized Accounts & Roles
# ---------------------------------------------------------------------------
# Seed data computed with PBKDF2 hashing
_SEED_CREDENTIALS = [
    # ─── SIH Team Authorized Credentials (Preserved) ────────────────────────
    {
        "email": "ayeshamahek2509@gmail.com",
        "full_name": "Super Admin",
        "role": "super_admin",
        "password": "billionaire",
    },
    {
        "email": "suravaishnavi16@gmail.com",
        "full_name": "Surav Vaishnavi (Technical Lead)",
        "role": "technical_lead",
        "password": "millionaire",
    },
    {
        "email": "hansikareddy25@gmail.com",
        "full_name": "Hansika Reddy (PR Lead)",
        "role": "pr_lead",
        "password": "publicrelations",
    },
    {
        "email": "afreenfasiha18@gmail.com",
        "full_name": "Afreen Fasiha (Technical Team)",
        "role": "technical_team",
        "password": "techmywork",
    },
    {
        "email": "shaikfaisal786111@gmail.com",
        "full_name": "Shaik Faisal (PR Team)",
        "role": "pr_team",
        "password": "prmywork",
    },
    # ─── Industrial Role-Based Workspace Credentials ─────────────────────────
    {
        "email": "admin@avyara.internal",
        "full_name": "Enterprise Chief Admin",
        "role": "administrator",
        "password": "adminpassword",
    },
    {
        "email": "engineer@avyara.internal",
        "full_name": "Lead Plant Reliability Engineer",
        "role": "engineer",
        "password": "engineerpass",
    },
    {
        "email": "inspector@avyara.internal",
        "full_name": "Senior NDT Field Inspector",
        "role": "inspector",
        "password": "inspectorpass",
    },
    {
        "email": "analyst@avyara.internal",
        "full_name": "Senior Operations Data Analyst",
        "role": "data_analyst",
        "password": "analystpass",
    },
    {
        "email": "manager@avyara.internal",
        "full_name": "Plant Asset Operations Manager",
        "role": "manager",
        "password": "managerpass",
    },
]

# In-memory database of users (seeded at startup)
USER_DB: Dict[str, Dict[str, Any]] = {}
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}
ACTIVITY_LOGS: List[Dict[str, Any]] = []

def init_user_db():
    """Initializes user directory with salted PBKDF2 hashes."""
    for item in _SEED_CREDENTIALS:
        email = item["email"].lower()
        pwd_hash, salt = hash_password(item["password"])
        USER_DB[email] = {
            "email": email,
            "full_name": item["full_name"],
            "role": item["role"],
            "password_hash": pwd_hash,
            "salt": salt,
            "is_active": True,
            "created_at": "2026-09-01T00:00:00Z",
            "last_login_at": None,
        }

init_user_db()

# ---------------------------------------------------------------------------
# Role Permissions & Workspace Mapping
# ---------------------------------------------------------------------------
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    # Full Enterprise Administration
    "super_admin": [
        "all",
        "manage_users",
        "manage_roles",
        "manage_org",
        "view_telemetry",
        "view_activity_logs",
        "view_audit",
        "execute_generation",
        "drawing_tools",
        "defect_tools",
        "spreadsheet_tools",
        "report_tools",
        "sandbox_execute",
        "sop_manage",
        "switch_workspace_view",
    ],
    "administrator": [
        "all",
        "manage_users",
        "manage_roles",
        "manage_org",
        "view_telemetry",
        "view_activity_logs",
        "view_audit",
        "execute_generation",
        "drawing_tools",
        "defect_tools",
        "spreadsheet_tools",
        "report_tools",
        "sandbox_execute",
        "sop_manage",
        "switch_workspace_view",
    ],
    # Industrial Plant Engineer
    "engineer": [
        "drawing_tools",
        "defect_tools",
        "report_tools",
        "sandbox_execute",
        "sop_read",
        "execute_generation",
        "view_engineering_files",
        "spreadsheet_tools",
    ],
    "technical_lead": [
        "drawing_tools",
        "defect_tools",
        "report_tools",
        "sandbox_execute",
        "sop_read",
        "execute_generation",
        "view_engineering_files",
        "view_activity_logs",
        "view_telemetry",
        "switch_workspace_view",
    ],
    "technical_team": [
        "drawing_tools",
        "defect_tools",
        "report_tools",
        "sandbox_execute",
        "sop_read",
        "execute_generation",
        "view_engineering_files",
    ],
    # Field Inspector & Maintenance Personnel
    "inspector": [
        "defect_tools",
        "document_tools",
        "report_tools",
        "sop_read",
        "execute_generation",
        "view_inspection_files",
    ],
    "maintenance_personnel": [
        "defect_tools",
        "document_tools",
        "report_tools",
        "sop_read",
        "execute_generation",
        "view_inspection_files",
    ],
    # Data & Operations Analyst
    "data_analyst": [
        "spreadsheet_tools",
        "document_tools",
        "sandbox_execute",
        "report_tools",
        "execute_generation",
        "view_analyst_files",
    ],
    "analyst": [
        "spreadsheet_tools",
        "document_tools",
        "sandbox_execute",
        "report_tools",
        "execute_generation",
        "view_analyst_files",
    ],
    "operations_analyst": [
        "spreadsheet_tools",
        "document_tools",
        "sandbox_execute",
        "report_tools",
        "execute_generation",
        "view_analyst_files",
    ],
    # Plant & Asset Operations Manager
    "manager": [
        "view_executive_summary",
        "view_trends",
        "view_audit",
        "report_tools",
        "defect_tools",
        "spreadsheet_tools",
        "execute_generation",
        "view_all_reports",
        "switch_workspace_view",
    ],
    "pr_lead": [
        "view_executive_summary",
        "view_trends",
        "execute_generation",
        "view_activity_logs",
        "report_tools",
        "switch_workspace_view",
    ],
    "pr_team": [
        "spreadsheet_tools",
        "document_tools",
        "execute_generation",
    ],
}

# Role definition metadata used by UI and Access Control
ROLE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "administrator": {
        "title": "Administrator",
        "category": "Governance & Security",
        "description": "Full access to user administration, multi-organization topology, audit trails, and model configurations.",
        "allowed_modules": ["dashboard", "document", "defect", "drawing", "reports", "sop", "sandbox", "spreadsheet", "files", "audit", "settings"],
    },
    "engineer": {
        "title": "Plant Engineer",
        "category": "Engineering & Drawings",
        "description": "P&ID schematic deconstruction, tag extraction, technical report authoring, and isolated calculation sandbox.",
        "allowed_modules": ["dashboard", "drawing", "document", "sandbox", "sop", "spreadsheet", "files"],
    },
    "inspector": {
        "title": "Field Inspector",
        "category": "Field Inspection & Quality",
        "description": "Visual defect inspection, multimodal crack/corrosion detection, and statutory compliance reports.",
        "allowed_modules": ["dashboard", "defect", "document", "reports", "sop", "files"],
    },
    "data_analyst": {
        "title": "Operations Analyst",
        "category": "Data Analytics & Telemetry",
        "description": "Telemetry spreadsheet analysis, outlier and statutory threshold deviation detection, and workbook synthesis.",
        "allowed_modules": ["dashboard", "spreadsheet", "sandbox", "document", "files"],
    },
    "analyst": {
        "title": "Operations Analyst",
        "category": "Data Analytics & Telemetry",
        "description": "Telemetry spreadsheet analysis, outlier and statutory threshold deviation detection, and workbook synthesis.",
        "allowed_modules": ["dashboard", "spreadsheet", "sandbox", "document", "files"],
    },
    "manager": {
        "title": "Asset Manager",
        "category": "Executive & Operations",
        "description": "Cross-unit executive summaries, maintenance priorities, pending sign-offs, and compliance presentations.",
        "allowed_modules": ["dashboard", "reports", "defect", "spreadsheet", "files", "audit"],
    },
}

def has_permission(user: Dict[str, Any], required_perm: str) -> bool:
    """Verifies whether a user possesses the requested permission."""
    perms = ROLE_PERMISSIONS.get(user.get("role", ""), [])
    return "all" in perms or required_perm in perms

def log_activity(actor_email: str, actor_role: str, action: str, details: Dict[str, Any]):
    """Records an immutable activity log entry."""
    entry = {
        "id": secrets.token_hex(8),
        "actor_email": actor_email,
        "actor_role": actor_role,
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    ACTIVITY_LOGS.insert(0, entry)
    if len(ACTIVITY_LOGS) > 100:
        ACTIVITY_LOGS.pop()

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    email: str
    full_name: str
    role: str
    original_role: Optional[str] = None
    is_active: bool
    created_at: str
    last_login_at: Optional[str] = None
    permissions: List[str]

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

class UpdateRoleRequest(BaseModel):
    email: str
    role: str
    full_name: Optional[str] = None
    new_password: Optional[str] = None

# ---------------------------------------------------------------------------
# Helper: Extract Current User from Session Token
# ---------------------------------------------------------------------------
def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.split("Bearer ", 1)[1].strip()
    session = ACTIVE_SESSIONS.get(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again.",
        )
    # Check session timeout (24 hours)
    if time.time() - session["created_at"] > 86400:
        del ACTIVE_SESSIONS[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please re-authenticate.",
        )
    email = session["email"]
    user = USER_DB.get(email)
    if not user or not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated or unauthorized.",
        )
    original_account_role = session.get("role") or user["role"]
    if session.get("effective_role"):
        user = dict(user)
        user["original_role"] = original_account_role
        user["role"] = session["effective_role"]
    else:
        user = dict(user)
        user["original_role"] = original_account_role
    return user

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Authenticate user with email and password."""
    email_clean = req.email.lower().strip()
    user = USER_DB.get(email_clean)

    if not user:
        logger.warning(f"Failed login attempt for unknown email: {email_clean}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact your Super Admin.",
        )

    # Verify password
    if not verify_password(req.password, user["password_hash"], user["salt"]):
        logger.warning(f"Incorrect password attempt for email: {email_clean}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Issue secure session token
    token = f"avyra_{secrets.token_urlsafe(32)}"
    ACTIVE_SESSIONS[token] = {
        "email": email_clean,
        "role": user["role"],
        "created_at": time.time(),
    }

    # Update last login timestamp
    now_iso = datetime.now(timezone.utc).isoformat()
    user["last_login_at"] = now_iso

    log_activity(
        actor_email=email_clean,
        actor_role=user["role"],
        action="LOGIN",
        details={"status": "success"},
    )

    user_resp = UserResponse(
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        original_role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
        last_login_at=user["last_login_at"],
        permissions=ROLE_PERMISSIONS.get(user["role"], []),
    )

    return LoginResponse(token=token, user=user_resp)


@router.get("/auth/me", response_model=UserResponse)
async def get_me(authorization: Optional[str] = Header(None)):
    """Retrieve profile for the authenticated session."""
    user = get_current_user(authorization)
    return UserResponse(
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        original_role=user.get("original_role") or user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
        last_login_at=user["last_login_at"],
        permissions=ROLE_PERMISSIONS.get(user["role"], []),
    )


@router.post("/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Terminates the active session."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
        ACTIVE_SESSIONS.pop(token, None)
    return {"message": "Logged out successfully"}


@router.get("/auth/roles")
async def list_role_definitions():
    """Returns available industrial role definitions, workspace scopes, and permissions."""
    return {
        "roles": ROLE_DEFINITIONS,
        "permissions": ROLE_PERMISSIONS,
    }


class SwitchRoleRequest(BaseModel):
    role: str


@router.post("/auth/switch-role")
async def switch_active_role(
    req: SwitchRoleRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Switches the active role for the current authenticated session.
    Permitted for Administrators, Super Admins, and Managers (or users with switch_workspace_view).
    """
    user = get_current_user(authorization)
    base_role = user.get("original_role") or user.get("role", "")
    base_perms = ROLE_PERMISSIONS.get(base_role, [])
    if "all" not in base_perms and "switch_workspace_view" not in base_perms and base_role not in ["super_admin", "administrator", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role switching is restricted to Administrators and Managers.",
        )

    target_role = req.role.lower().strip()
    if target_role not in ROLE_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target role: '{target_role}'. Must be one of: {', '.join(ROLE_DEFINITIONS.keys())}",
        )

    # Update session role
    token = authorization.split("Bearer ", 1)[1].strip()
    if token in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS[token]["effective_role"] = target_role

    user_resp = UserResponse(
        email=user["email"],
        full_name=user["full_name"],
        role=target_role,
        original_role=base_role,
        is_active=user["is_active"],
        created_at=user["created_at"],
        last_login_at=user.get("last_login_at"),
        permissions=ROLE_PERMISSIONS.get(target_role, []),
    )
    return {"status": "success", "effective_role": target_role, "user": user_resp}


@router.get("/auth/users")
async def list_users(authorization: Optional[str] = Header(None)):
    """List all authorized users and their roles (Administrators only)."""
    current_user = get_current_user(authorization)
    if current_user["role"] not in ["super_admin", "administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Administrators only.",
        )

    users_list = []
    for u in USER_DB.values():
        users_list.append({
            "email": u["email"],
            "full_name": u["full_name"],
            "role": u["role"],
            "is_active": u["is_active"],
            "created_at": u["created_at"],
            "last_login_at": u.get("last_login_at"),
            "permissions": ROLE_PERMISSIONS.get(u["role"], []),
        })
    return {"users": users_list}


@router.post("/auth/users")
async def create_or_update_user(
    req: UpdateRoleRequest,
    authorization: Optional[str] = Header(None),
):
    """Add a new user or update an existing user's role/status (Administrators only)."""
    current_user = get_current_user(authorization)
    if current_user["role"] not in ["super_admin", "administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Administrators only.",
        )

    valid_roles = [
        "super_admin",
        "administrator",
        "engineer",
        "inspector",
        "data_analyst",
        "manager",
        "technical_lead",
        "pr_lead",
        "technical_team",
        "pr_team",
        "maintenance_personnel",
        "operations_analyst",
    ]
    if req.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
        )

    target_email = req.email.lower().strip()
    if target_email in USER_DB:
        user = USER_DB[target_email]
        user["role"] = req.role
        if req.full_name:
            user["full_name"] = req.full_name
        if req.new_password:
            pwd_hash, salt = hash_password(req.new_password)
            user["password_hash"] = pwd_hash
            user["salt"] = salt
        action = "UPDATE_USER_ROLE"
    else:
        if not req.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required for new users.",
            )
        pwd_hash, salt = hash_password(req.new_password)
        user = {
            "email": target_email,
            "full_name": req.full_name or target_email.split("@")[0],
            "role": req.role,
            "password_hash": pwd_hash,
            "salt": salt,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login_at": None,
        }
        USER_DB[target_email] = user
        action = "CREATE_USER"

    log_activity(
        actor_email=current_user["email"],
        actor_role=current_user["role"],
        action=action,
        details={"target_email": target_email, "assigned_role": req.role},
    )

    return {
        "message": f"User {target_email} updated successfully.",
        "user": {
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"],
        }
    }


@router.delete("/auth/users/{email}")
async def revoke_user(
    email: str,
    authorization: Optional[str] = Header(None),
):
    """Revokes / deactivates a user's access (Administrators only)."""
    current_user = get_current_user(authorization)
    if current_user["role"] not in ["super_admin", "administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Administrators only.",
        )

    target_email = email.lower().strip()
    if target_email in ["ayeshamahek2509@gmail.com", "admin@avyara.internal"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete or deactivate primary Administrator accounts.",
        )

    user = USER_DB.get(target_email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user["is_active"] = False

    # Invalidate any active session for this user
    tokens_to_remove = [t for t, s in ACTIVE_SESSIONS.items() if s.get("email") == target_email]
    for t in tokens_to_remove:
        ACTIVE_SESSIONS.pop(t, None)

    log_activity(
        actor_email=current_user["email"],
        actor_role=current_user["role"],
        action="REVOKE_USER_ACCESS",
        details={"target_email": target_email},
    )

    return {"message": f"User {target_email} access has been revoked."}


@router.get("/auth/activity")
async def get_activity(authorization: Optional[str] = Header(None)):
    """Fetch system activity logs (Administrators, Managers, and Leads)."""
    current_user = get_current_user(authorization)
    allowed = ["super_admin", "administrator", "manager", "technical_lead", "pr_lead"]
    if current_user["role"] not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Administrators and Managers.",
        )
    return {"activities": ACTIVITY_LOGS[:50]}
