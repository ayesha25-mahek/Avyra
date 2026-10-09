"""
test_role_workspaces_step2.py
-----------------------------
Comprehensive test suite verifying Step 2: Role-Based Industrial Workspaces in Avyara.

Tests:
1. Industrial Seed Credential Authentication (admin, engineer, inspector, analyst, manager)
2. Role Definitions retrieval (GET /api/auth/roles)
3. Role Switching (POST /api/auth/switch-role)
4. Server-Side RBAC Enforcement (403 Forbidden on unauthorized tools & config)
5. Multi-Industry Organization Topology & Presets (GET/POST /api/org/config, /api/org/presets)
6. Workspace Switching (POST /api/org/workspace/switch)
7. Scoped Generated Files Catalog (GET /api/generated-files)
"""

import json
import urllib.error
import urllib.request
import sys

BASE_URL = "http://127.0.0.1:8000"

ROLES_TO_TEST = [
    ("admin@avyara.internal", "adminpassword", "administrator"),
    ("engineer@avyara.internal", "engineerpass", "engineer"),
    ("inspector@avyara.internal", "inspectorpass", "inspector"),
    ("analyst@avyara.internal", "analystpass", "data_analyst"),
    ("manager@avyara.internal", "managerpass", "manager"),
]

def request(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            resp_body = resp.read().decode("utf-8")
            return status_code, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(resp_body)
        except Exception:
            parsed = {"raw": resp_body}
        return e.code, parsed

def post_multipart(path, fields, token=None):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body_bytes = bytearray()
    for k, v in fields.items():
        body_bytes.extend(f"--{boundary}\r\n".encode("utf-8"))
        body_bytes.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
        body_bytes.extend(f"{v}\r\n".encode("utf-8"))
    body_bytes.extend(f"--{boundary}--\r\n".encode("utf-8"))

    url = f"{BASE_URL}{path}"
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=bytes(body_bytes), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(resp_body)
        except Exception:
            parsed = {"raw": resp_body}
        return e.code, parsed

def run_tests():
    print("=" * 70)
    print("AVYARA STEP 2 VERIFICATION: ROLE-BASED INDUSTRIAL WORKSPACES")
    print("=" * 70)

    tokens = {}

    # 1. Authenticate all 5 industrial roles
    print("\n[TEST 1] Authenticating 5 Industrial Seed Accounts...")
    for email, password, expected_role in ROLES_TO_TEST:
        status, data = request("POST", "/api/auth/login", {"email": email, "password": password})
        assert status == 200, f"Login failed for {email}: {status} - {data}"
        assert data["user"]["role"] == expected_role, f"Expected role {expected_role}, got {data['user']['role']}"
        tokens[expected_role] = data["token"]
        print(f"  [OK] {expected_role.upper():<14} logged in ({email}) | Permissions: {len(data['user']['permissions'])}")

    admin_token = tokens["administrator"]
    engineer_token = tokens["engineer"]
    inspector_token = tokens["inspector"]
    analyst_token = tokens["data_analyst"]
    manager_token = tokens["manager"]

    # 2. Test Role Definitions Endpoint
    print("\n[TEST 2] Verifying GET /api/auth/roles...")
    status, roles_data = request("GET", "/api/auth/roles")
    assert status == 200, f"Failed GET /api/auth/roles: {status}"
    roles = roles_data.get("roles", {})
    for r in ["engineer", "inspector", "analyst", "manager", "administrator"]:
        assert r in roles, f"Role {r} missing from /api/auth/roles"
        print(f"  [OK] Found definition for role: {r} (Title: {roles[r]['title']})")

    # 3. Test Role Switching Endpoint
    print("\n[TEST 3] Testing POST /api/auth/switch-role...")
    # Admin can switch to engineer
    status, switch_res = request("POST", "/api/auth/switch-role", {"role": "engineer"}, token=admin_token)
    assert status == 200, f"Admin switch role failed: {status} - {switch_res}"
    assert switch_res["effective_role"] == "engineer", "Admin role switch failed"
    print("  [OK] Admin successfully switched effective role to 'engineer'")

    # Inspector cannot switch role (unauthorized)
    status, fail_switch = request("POST", "/api/auth/switch-role", {"role": "administrator"}, token=inspector_token)
    assert status == 403, f"Inspector should not be allowed to switch role, got status {status}"
    print("  [OK] Inspector forbidden from switching roles (HTTP 403 returned as expected)")

    # Restore Admin back to administrator
    status, _ = request("POST", "/api/auth/switch-role", {"role": "administrator"}, token=admin_token)
    assert status == 200

    # 4. RBAC Authorization Enforcement
    print("\n[TEST 4] Server-Side RBAC Enforcement on Industrial Tools...")
    
    # 4a. Sandbox execution
    # Inspector attempting to execute Python code in sandbox -> HTTP 403 Forbidden
    status, sb_fail = request("POST", "/api/sandbox/execute", {"code": "print('test')"}, token=inspector_token)
    assert status == 403, f"Expected 403 for Inspector on sandbox, got {status} - {sb_fail}"
    print(f"  [OK] Inspector blocked from Python sandbox: HTTP {status} ({sb_fail.get('detail')})")

    # Engineer attempting sandbox execute -> Allowed (status 200)
    status, sb_ok = request("POST", "/api/sandbox/execute", {"code": "x = 40 + 2\nprint(f'VAL={x}')"}, token=engineer_token)
    assert status == 200, f"Expected 200 for Engineer on sandbox, got {status} - {sb_ok}"
    assert "VAL=42" in sb_ok.get("stdout", ""), f"Unexpected sandbox output: {sb_ok}"
    print(f"  [OK] Engineer authorized to execute in Python sandbox: Result = VAL=42")

    # 4b. Output Generation Authorization
    # Inspector requesting drawing analysis -> HTTP 403 Forbidden
    status, gen_fail = post_multipart("/api/generate", {"outputs": json.dumps(["drawing_analysis"]), "prompt": "P&ID"}, token=inspector_token)
    assert status == 403, f"Expected 403 for Inspector requesting drawing_analysis, got {status} - {gen_fail}"
    print(f"  [OK] Inspector blocked from drawing tools: HTTP {status} ({gen_fail.get('detail')})")

    # Analyst requesting defect inspection report -> HTTP 403 Forbidden
    status, gen_fail_analyst = post_multipart("/api/generate", {"outputs": json.dumps(["defect_report"]), "prompt": "Crack"}, token=analyst_token)
    assert status == 403, f"Expected 403 for Analyst requesting defect_report, got {status} - {gen_fail_analyst}"
    print(f"  [OK] Analyst blocked from defect inspection tools: HTTP {status} ({gen_fail_analyst.get('detail')})")

    # 4c. Organization Configuration Authorization
    # Engineer attempting to update org config -> HTTP 403 Forbidden
    status, org_upd_fail = request("POST", "/api/org/config", {"org_name": "Hacked Org"}, token=engineer_token)
    assert status == 403, f"Expected 403 for Engineer updating org config, got {status}"
    print(f"  [OK] Engineer blocked from updating org config: HTTP {status} ({org_upd_fail.get('detail')})")

    # Admin updating org config -> HTTP 200 OK
    status, org_upd_ok = request("POST", "/api/org/config", {"org_name": "MRPL Petrochemical Complex"}, token=admin_token)
    assert status == 200, f"Admin update org config failed: {status} - {org_upd_ok}"
    assert org_upd_ok["config"]["org_name"] == "MRPL Petrochemical Complex"
    print(f"  [OK] Admin authorized to update org config: Updated org_name = '{org_upd_ok['config']['org_name']}'")

    # 5. Multi-Industry Organization Topology & Presets
    print("\n[TEST 5] Testing Multi-Industry Presets & Topology...")
    status, presets_res = request("GET", "/api/org/presets")
    assert status == 200, f"Failed GET /api/org/presets: {status}"
    presets = presets_res.get("presets", [])
    preset_ids = [p["id"] for p in presets]
    assert "refinery" in preset_ids and "automotive" in preset_ids and "aerospace" in preset_ids and "pharma" in preset_ids
    print(f"  [OK] Retrieved {len(presets)} industry presets: {preset_ids}")

    # Apply Automotive Preset (Admin only)
    status, apply_res = request("POST", "/api/org/presets/automotive", token=admin_token)
    assert status == 200, f"Failed to apply automotive preset: {status}"
    assert "Automotive" in apply_res["config"]["industry"]
    print(f"  [OK] Successfully applied 'automotive' preset (Industry: {apply_res['config']['industry']})")

    # Apply Refinery Preset back to maintain MRPL defaults for SIH jury demo
    status, restore_res = request("POST", "/api/org/presets/refinery", token=admin_token)
    assert status == 200, f"Failed to restore refinery preset: {status}"
    assert "Refinery" in restore_res["config"]["industry"]
    print(f"  [OK] Successfully restored 'refinery' preset (Industry: {restore_res['config']['industry']})")

    # 6. Workspace Switching
    print("\n[TEST 6] Testing Operational Workspace Context Switching...")
    status, ws_res = request("POST", "/api/org/workspace/switch", {"workspace_id": "ws_utilities"}, token=engineer_token)
    assert status == 200, f"Workspace switch failed: {status}"
    assert ws_res["active_workspace_id"] == "ws_utilities"
    print("  [OK] Successfully switched active operational unit to 'ws_utilities' (Plant Utilities & Power Block)")

    # Restore workspace to ws_cdu1
    status, _ = request("POST", "/api/org/workspace/switch", {"workspace_id": "ws_cdu1"}, token=engineer_token)
    assert status == 200

    # 7. Scoped Generated Files Catalog
    print("\n[TEST 7] Testing Generated Files Catalog Role Scoping...")
    status, all_files = request("GET", "/api/generated-files?role=all")
    assert status == 200, f"Failed to get all files: {status}"
    status, eng_files = request("GET", "/api/generated-files?role=engineer")
    assert status == 200, f"Failed to get engineer files: {status}"
    status, insp_files = request("GET", "/api/generated-files?role=inspector")
    assert status == 200, f"Failed to get inspector files: {status}"

    print(f"  [OK] Catalog returned {len(all_files)} total files, {len(eng_files)} engineer-relevant files, {len(insp_files)} inspector-relevant files")

    print("\n" + "=" * 70)
    print("ALL STEP 2 ROLE-BASED WORKSPACE TESTS PASSED SUCCESSFULLY! (100% OK)")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
