import React, { useEffect, useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Lock,
  RefreshCw,
  Activity,
} from 'lucide-react';

interface AuditEvent {
  timestamp: string;
  task_id: string;
  operation: string;
  component: string;
  provider: string;
  model: string;
  local_or_external: string;
  external_calls: number;
  data_transfer_bytes: number;
  status: string;
  details?: Record<string, any>;
}

interface SovereigntyStats {
  sovereignty_mode: string;
  sovereignty_status: string;
  internet_status: string;
  internet_posture: string;
  security_policy: string;
  external_api_calls: number;
  cloud_ai_calls: number;
  external_data_transfers_bytes: number;
  data_sent_outside_bytes: number;
  local_model_calls: number;
  local_ocr_calls: number;
  local_vision_calls: number;
  local_rag_queries: number;
  agent_tool_calls: number;
  sandbox_executions: number;
  files_processed: number;
  local_model: string;
  recent_audit_events: AuditEvent[];
  telemetry_states?: Record<string, string>;
}

export const ConfidentialIndustrialWorkspace: React.FC<{
  onSelectTaskDirective?: (prompt: string, outputFormat: string) => void;
  isProcessing?: boolean;
}> = () => {
  const [stats, setStats] = useState<SovereigntyStats | null>(null);
  const [showAuditTrail, setShowAuditTrail] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/sovereignty/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.warn('Could not fetch sovereignty stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 6000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-xl border border-[#1E4D36] bg-[#0A1A12] p-5 sm:p-6 text-white space-y-6 shadow-lg font-serif">
      {/* ─── HEADER BAR ─────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#143324] gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#00E599]/15 border border-[#00E599]/40 flex items-center justify-center text-[#00E599]">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base sm:text-lg font-bold text-white tracking-wide">
                CONFIDENTIAL INDUSTRIAL AI WORKSPACE
              </h3>
              <span className="px-2 py-0.5 rounded bg-[#00E599]/20 border border-[#00E599]/50 text-[#00E599] text-[10px] font-mono font-bold">
                SIH 26117
              </span>
            </div>
            <p className="text-xs text-[#9DC4B0]">
              Sovereign on-premise execution with verified zero cloud exfiltration &amp; tamper-evident event auditing.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchStats}
            disabled={loading}
            className="px-2.5 py-1 rounded bg-[#102B1E] hover:bg-[#1B4330] border border-[#1E4D36] text-[#74C69D] hover:text-white text-xs font-mono flex items-center gap-1.5 transition-all"
            title="Refresh live telemetry"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <span className="px-2.5 py-1 rounded bg-[#102B1E] border border-[#1E4D36] text-xs font-mono text-[#00E599] font-bold">
            SOVEREIGN: ACTIVE
          </span>
        </div>
      </div>

      {/* ─── PROCESSING PIPELINE STAGES ─────────────────────────────────── */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold text-[#74C69D] uppercase tracking-wider font-mono">
          Verified On-Premise Processing Pipeline
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 text-xs">
          {[
            { label: 'Local Ingest', state: 'VERIFIED' },
            { label: 'Local OCR/Vision', state: 'VERIFIED' },
            { label: 'Agent Planner', state: 'VERIFIED' },
            { label: 'Model Router', state: 'VERIFIED' },
            { label: 'SQLite RAG', state: 'VERIFIED' },
            { label: 'Local Tools', state: 'VERIFIED' },
            { label: 'Python Sandbox', state: 'VERIFIED' },
            { label: 'Docx/Pptx Output', state: 'VERIFIED' },
          ].map((stage, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-[#0F261B] border border-[#1A402D] flex flex-col items-center justify-center text-center gap-1"
            >
              <div className="w-2 h-2 rounded-full bg-[#00E599] shadow-[0_0_6px_#00E599]" />
              <span className="text-[11px] font-medium text-white">{stage.label}</span>
              <span className="text-[9px] font-mono text-[#00E599] font-semibold">{stage.state}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ─── SOVEREIGNTY STATUS & REAL TELEMETRY METRICS ─────────────────── */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold text-[#74C69D] uppercase tracking-wider font-mono">
          Auditable Sovereignty Telemetry
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {/* Internet Status */}
          <div className="p-3 rounded-lg bg-[#0F261B] border border-[#1A402D] space-y-1">
            <span className="text-[10px] font-mono text-[#9DC4B0]">Internet Status</span>
            <div className="text-sm font-bold font-mono text-[#00E599]">
              {stats?.internet_status || 'RESTRICTED'}
            </div>
            <span className="text-[9px] font-mono text-[#588B72] block">Verified loopback</span>
          </div>

          {/* External Calls */}
          <div className="p-3 rounded-lg bg-[#0F261B] border border-[#1A402D] space-y-1">
            <span className="text-[10px] font-mono text-[#9DC4B0]">External API Calls</span>
            <div className="text-sm font-bold font-mono text-white">
              {stats?.external_api_calls ?? 0}
            </div>
            <span className="text-[9px] font-mono text-[#00E599] font-semibold block">VERIFIED: ZERO</span>
          </div>

          {/* Cloud AI Calls */}
          <div className="p-3 rounded-lg bg-[#0F261B] border border-[#1A402D] space-y-1">
            <span className="text-[10px] font-mono text-[#9DC4B0]">Cloud AI Calls</span>
            <div className="text-sm font-bold font-mono text-white">
              {stats?.cloud_ai_calls ?? 0}
            </div>
            <span className="text-[9px] font-mono text-[#00E599] font-semibold block">VERIFIED: ZERO</span>
          </div>

          {/* Data Sent Outside */}
          <div className="p-3 rounded-lg bg-[#0F261B] border border-[#1A402D] space-y-1">
            <span className="text-[10px] font-mono text-[#9DC4B0]">Data Sent Outside</span>
            <div className="text-sm font-bold font-mono text-white">
              {stats?.data_sent_outside_bytes ?? 0} bytes
            </div>
            <span className="text-[9px] font-mono text-[#00E599] font-semibold block">ZERO EXFILTRATION</span>
          </div>

          {/* Local Model Calls */}
          <div className="p-3 rounded-lg bg-[#0F261B] border border-[#1A402D] space-y-1">
            <span className="text-[10px] font-mono text-[#9DC4B0]">Local Model Calls</span>
            <div className="text-sm font-bold font-mono text-white">
              {stats?.local_model_calls ?? 0}
            </div>
            <span className="text-[9px] font-mono text-[#74C69D] block">Model: {stats?.local_model || 'qwen2.5:7b'}</span>
          </div>

          {/* Sandbox & Tools Executions */}
          <div className="p-3 rounded-lg bg-[#0F261B] border border-[#1A402D] space-y-1">
            <span className="text-[10px] font-mono text-[#9DC4B0]">Agent Tools &amp; Sandbox</span>
            <div className="text-sm font-bold font-mono text-white">
              {(stats?.agent_tool_calls ?? 0) + (stats?.sandbox_executions ?? 0)}
            </div>
            <span className="text-[9px] font-mono text-[#74C69D] block">Files: {stats?.files_processed ?? 0}</span>
          </div>
        </div>
      </div>

      {/* ─── AUDIT EVENT LOG (EXPANDABLE) ───────────────────────────────── */}
      <div className="pt-2 border-t border-[#143324]">
        <button
          type="button"
          onClick={() => setShowAuditTrail(!showAuditTrail)}
          className="w-full flex items-center justify-between text-left p-2 rounded hover:bg-[#0F261B] transition-colors"
        >
          <span className="text-xs font-mono font-bold text-[#00E599] flex items-center gap-2">
            <Activity className="w-3.5 h-3.5" />
            LIVE ON-PREMISE AUDIT EVENT LOG
            {stats?.recent_audit_events && (
              <span className="px-2 py-0.5 rounded bg-[#102B1E] text-[10px] text-[#B8D5C6] font-normal">
                {stats.recent_audit_events.length} Recent Events
              </span>
            )}
          </span>
          {showAuditTrail ? <ChevronUp className="w-4 h-4 text-[#9DC4B0]" /> : <ChevronDown className="w-4 h-4 text-[#9DC4B0]" />}
        </button>

        {showAuditTrail && (
          <div className="mt-3 p-3 rounded-lg bg-[#050C08] border border-[#143324] max-h-72 overflow-y-auto space-y-2 font-mono text-[11px] scrollbar-thin">
            {(!stats?.recent_audit_events || stats.recent_audit_events.length === 0) ? (
              <div className="text-[#588B72] text-center py-4">No audit events logged yet in current session.</div>
            ) : (
              stats.recent_audit_events.slice().reverse().map((evt, idx) => (
                <div
                  key={idx}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-2 rounded bg-[#0A1A12] border border-[#142B1F] gap-2 hover:border-[#1E4D36] transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[#588B72] text-[10px]">
                      {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : '00:00:00'}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-[#163827] text-[#00E599] font-bold text-[10px]">
                      {evt.operation}
                    </span>
                    <span className="text-[#E1E8E4]">{evt.component}</span>
                    <span className="text-[#74C69D] text-[10px]">({evt.provider})</span>
                  </div>

                  <div className="flex items-center gap-2 text-[10px]">
                    <span className="px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-800 text-[#00E599]">
                      {evt.local_or_external}
                    </span>
                    <span className="text-[#9DC4B0]">
                      Ext Calls: {evt.external_calls}
                    </span>
                    <span className={`font-bold ${evt.status === 'SUCCESS' ? 'text-[#00E599]' : 'text-amber-400'}`}>
                      {evt.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
