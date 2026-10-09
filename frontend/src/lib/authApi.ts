import type { UserProfile, AuthResponse, UserRole, ActivityLog } from '@/types/auth';

const TOKEN_KEY = 'avyra_auth_token';
const USER_KEY = 'avyra_auth_user';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): UserProfile | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function storeSession(auth: AuthResponse): void {
  localStorage.setItem(TOKEN_KEY, auth.token);
  localStorage.setItem(USER_KEY, JSON.stringify(auth.user));
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email.trim(), password }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Authentication failed' }));
    throw new Error(errorData.detail || 'Invalid email or password');
  }

  const data: AuthResponse = await res.json();
  storeSession(data);
  return data;
}

export async function fetchCurrentUser(): Promise<UserProfile | null> {
  const token = getStoredToken();
  if (!token) return null;

  try {
    const res = await fetch('/api/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) {
      clearSession();
      return null;
    }

    const user: UserProfile = await res.json();
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    return user;
  } catch {
    return getStoredUser();
  }
}

export async function logoutUser(): Promise<void> {
  const token = getStoredToken();
  if (token) {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      // ignore network errors on logout
    }
  }
  clearSession();
}

export async function fetchUsersList(): Promise<UserProfile[]> {
  const token = getStoredToken();
  if (!token) throw new Error('Not authenticated');

  const res = await fetch('/api/auth/users', {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch users' }));
    throw new Error(err.detail || 'Failed to fetch users');
  }

  const data = await res.json();
  return data.users;
}

export async function createOrUpdateUser(
  email: string,
  role: UserRole,
  fullName?: string,
  newPassword?: string
): Promise<void> {
  const token = getStoredToken();
  if (!token) throw new Error('Not authenticated');

  const res = await fetch('/api/auth/users', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      email,
      role,
      full_name: fullName,
      new_password: newPassword,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to update user' }));
    throw new Error(err.detail || 'Failed to update user');
  }
}

export async function revokeUserAccess(email: string): Promise<void> {
  const token = getStoredToken();
  if (!token) throw new Error('Not authenticated');

  const res = await fetch(`/api/auth/users/${encodeURIComponent(email)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to revoke access' }));
    throw new Error(err.detail || 'Failed to revoke access');
  }
}

export async function fetchActivityLogs(): Promise<ActivityLog[]> {
  const token = getStoredToken();
  if (!token) return [];

  try {
    const res = await fetch('/api/auth/activity', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.activities || [];
  } catch {
    return [];
  }
}

export async function switchActiveRole(role: string): Promise<UserProfile> {
  const token = getStoredToken();
  if (!token) throw new Error('Not authenticated');

  const res = await fetch('/api/auth/switch-role', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ role }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to switch role' }));
    throw new Error(err.detail || 'Failed to switch role');
  }

  const data = await res.json();
  const updatedUser: UserProfile = data.user;
  localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
  return updatedUser;
}

export async function fetchOrgConfig(): Promise<any> {
  const token = getStoredToken();
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch('/api/org/config', { headers });
  if (!res.ok) throw new Error('Failed to fetch organization configuration');
  return res.json();
}

export async function updateOrgConfig(updates: Record<string, any>): Promise<any> {
  const token = getStoredToken();
  if (!token) throw new Error('Not authenticated');

  const res = await fetch('/api/org/config', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to update organization' }));
    throw new Error(err.detail || 'Failed to update organization');
  }

  return res.json();
}

export async function fetchIndustryPresets(): Promise<any[]> {
  const res = await fetch('/api/org/presets');
  if (!res.ok) return [];
  const data = await res.json();
  return data.presets || [];
}

export async function applyIndustryPreset(presetId: string): Promise<any> {
  const token = getStoredToken();
  if (!token) throw new Error('Not authenticated');

  const res = await fetch(`/api/org/presets/${encodeURIComponent(presetId)}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to apply preset' }));
    throw new Error(err.detail || 'Failed to apply preset');
  }

  return res.json();
}

export async function switchWorkspace(workspaceId: string): Promise<any> {
  const token = getStoredToken();
  if (!token) throw new Error('Not authenticated');

  const res = await fetch('/api/org/workspace/switch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ workspace_id: workspaceId }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to switch workspace' }));
    throw new Error(err.detail || 'Failed to switch workspace');
  }

  return res.json();
}

