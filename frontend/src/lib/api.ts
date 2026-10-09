import type { OutputFormat, ProgressEvent, ResultEvent } from '@/types';

const API_BASE = '/api';

export interface GenerateCallbacks {
  onProgress?: (event: ProgressEvent) => void;
  onResult?: (event: ResultEvent) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}

/**
 * Generate content via SSE stream from the backend.
 * Uses fetch + ReadableStream to handle server-sent events.
 */
export async function generateContent(
  formData: FormData,
  callbacks: GenerateCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const { onProgress, onResult, onDone, onError } = callbacks;

  try {
    const response = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      body: formData,
      signal,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Server error ${response.status}: ${text}`);
    }

    if (!response.body) {
      throw new Error('No response body received');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events from buffer
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? ''; // keep incomplete line

      let currentEvent = '';
      let currentData = '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          currentData = line.slice(6).trim();
        } else if (line === '') {
          // End of event block
          if (currentEvent && currentData) {
            try {
              const parsed = JSON.parse(currentData);
              switch (currentEvent) {
                case 'progress':
                  onProgress?.(parsed as ProgressEvent);
                  break;
                case 'result':
                  onResult?.(parsed as ResultEvent);
                  break;
                case 'done':
                  onDone?.();
                  break;
                case 'error':
                  onError?.((parsed as { message: string }).message ?? 'Unknown error');
                  break;
              }
            } catch {
              // ignore parse errors on individual events
            }
            currentEvent = '';
            currentData = '';
          }
        }
      }
    }
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      return; // cancelled by user
    }
    const message = err instanceof Error ? err.message : 'Network error occurred';
    onError?.(message);
  }
}

/**
 * Download a file from the backend.
 */
export function downloadFile(url: string, filename?: string): void {
  const a = document.createElement('a');
  a.href = url;
  if (filename) a.download = filename;
  a.target = '_blank';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

/**
 * Download all available files.
 */
export function downloadAllFiles(
  results: Partial<Record<OutputFormat, ResultEvent>>
): void {
  Object.values(results).forEach((result) => {
    if (result?.download_url) {
      setTimeout(() => {
        downloadFile(result.download_url!, result.filename);
      }, 100);
    }
  });
}

/**
 * Check backend health.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`, { method: 'GET' });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Fetch available output types from backend.
 */
export async function fetchOutputTypes(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE}/outputs`);
    if (!response.ok) return [];
    const data = await response.json();
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export interface GeneratedFileInfo {
  filename: string;
  relative_path: string;
  size_bytes: number;
  modified_at: number;
  extension: string;
  download_url: string;
}

export async function fetchGeneratedFiles(): Promise<GeneratedFileInfo[]> {
  try {
    const res = await fetch(`${API_BASE}/generated-files`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.files || [];
  } catch {
    return [];
  }
}

export async function executeSandbox(params: { code?: string; task?: string; timeout?: number }) {
  const res = await fetch(`${API_BASE}/sandbox/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Sandbox execution failed');
  }
  return await res.json();
}

export async function retrieveSop(query: string, top_k = 4) {
  const res = await fetch(`${API_BASE}/rag/retrieve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Failed to retrieve SOPs');
  }
  return await res.json();
}

export async function fetchRagDocuments() {
  const res = await fetch(`${API_BASE}/rag/documents`);
  if (!res.ok) return { documents: [] };
  return await res.json();
}

export async function ingestSopDocument(formData: FormData) {
  const res = await fetch(`${API_BASE}/rag/ingest`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'SOP Ingestion failed');
  }
  return await res.json();
}

export async function fetchModelRegistry() {
  try {
    const res = await fetch(`${API_BASE}/models`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// ─── Document-to-Engineering-Drawing API ────────────────────────────────────
export async function extractDrawingRequirements(formData: FormData) {
  const token = localStorage.getItem('avyara_auth_token');
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/drawing/extract-requirements`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to extract drawing requirements' }));
    throw new Error(err.detail || 'Failed to extract drawing requirements');
  }
  return await res.json();
}

export async function generateCadDrawing(spec: any) {
  const token = localStorage.getItem('avyara_auth_token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/drawing/generate-cad`, {
    method: 'POST',
    headers,
    body: JSON.stringify(spec),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'CAD drawing generation failed' }));
    throw new Error(err.detail || 'CAD drawing generation failed');
  }
  return await res.json();
}

// ─── Document-to-Excel Workbook API ─────────────────────────────────────────
export async function extractSpreadsheetFromDoc(formData: FormData) {
  const token = localStorage.getItem('avyara_auth_token');
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/spreadsheet/extract-from-doc`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to extract spreadsheet schema' }));
    throw new Error(err.detail || 'Failed to extract spreadsheet schema');
  }
  return await res.json();
}

export async function generateSpreadsheetWorkbook(schema: any) {
  const token = localStorage.getItem('avyara_auth_token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/spreadsheet/generate-workbook`, {
    method: 'POST',
    headers,
    body: JSON.stringify(schema),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Workbook generation failed' }));
    throw new Error(err.detail || 'Workbook generation failed');
  }
  return await res.json();
}

// ─── Spreadsheet Audit & Safe Data Correction API ────────────────────────────
export async function auditSpreadsheetData(formData: FormData) {
  const token = localStorage.getItem('avyara_auth_token');
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/spreadsheet/audit-clean`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Spreadsheet audit failed' }));
    throw new Error(err.detail || 'Spreadsheet audit failed');
  }
  return await res.json();
}

export async function applySpreadsheetCorrections(payload: any) {
  const token = localStorage.getItem('avyara_auth_token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/spreadsheet/apply-corrections`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to apply spreadsheet corrections' }));
    throw new Error(err.detail || 'Failed to apply spreadsheet corrections');
  }
  return await res.json();
}

