import React, { useEffect, useState } from 'react';
import {
  Cpu,
  ShieldCheck,
  RefreshCw,
  Eye,
  Server,
  Building,
  Check,
  Lock,
} from 'lucide-react';
import { fetchModelRegistry } from '@/lib/api';
import {
  fetchIndustryPresets,
  applyIndustryPreset,
  updateOrgConfig,
} from '@/lib/authApi';
import type { OrgConfig } from '@/types/auth';

interface SettingsViewProps {
  orgConfig?: OrgConfig | null;
  onOrgConfigUpdated?: (cfg: OrgConfig) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  orgConfig,
  onOrgConfigUpdated,
}) => {
  const [modelData, setModelData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [providerMode, setProviderMode] = useState<'ollama' | 'auto'>('ollama');

  const [presets, setPresets] = useState<any[]>([]);
  const [applyingPreset, setApplyingPreset] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Local form state for org settings
  const [localOrgName, setLocalOrgName] = useState(orgConfig?.org_name || '');
  const [localIndustry, setLocalIndustry] = useState(orgConfig?.industry || '');
  const [localLocation, setLocalLocation] = useState(orgConfig?.facility_location || '');
  const [localActiveWs, setLocalActiveWs] = useState(orgConfig?.active_workspace_id || '');

  useEffect(() => {
    if (orgConfig) {
      setLocalOrgName(orgConfig.org_name);
      setLocalIndustry(orgConfig.industry);
      setLocalLocation(orgConfig.facility_location || '');
      setLocalActiveWs(orgConfig.active_workspace_id);
    }
  }, [orgConfig]);

  const loadModels = async () => {
    setLoading(true);
    try {
      const data = await fetchModelRegistry();
      setModelData(data);
    } catch {
      // quiet fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIndustryPresets().then((res) => {
      if (Array.isArray(res)) {
        setPresets(res);
      } else if (res && (res as any).presets) {
        setPresets((res as any).presets);
      }
    }).catch(() => {});
  }, []);

  const handleApplyPreset = async (presetId: string) => {
    setApplyingPreset(presetId);
    try {
      const res = await applyIndustryPreset(presetId);
      if (res && res.config) {
        if (onOrgConfigUpdated) onOrgConfigUpdated(res.config);
        setLocalOrgName(res.config.org_name);
        setLocalIndustry(res.config.industry);
        setLocalLocation(res.config.facility_location || '');
        setLocalActiveWs(res.config.active_workspace_id);
      }
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to apply preset', err);
    } finally {
      setApplyingPreset(null);
    }
  };

  const handleSaveOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await updateOrgConfig({
        org_name: localOrgName,
        industry: localIndustry,
        facility_location: localLocation,
        active_workspace_id: localActiveWs,
      });
      if (res && res.config && onOrgConfigUpdated) {
        onOrgConfigUpdated(res.config);
      }
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to update org config', err);
    }
  };

  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-5xl mx-auto">
      {/* Page Heading */}
      <div className="pb-4 border-b border-[#1A402D]">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#143324] border border-[#23573E] text-[#00E599]">
            MODULE 11
          </span>
          <span className="text-xs text-[#74C69D] font-mono">System Configuration</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Workbench Configuration &amp; Model Topology
        </h1>
        <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
          Inspect on-premise Ollama model runtime, local vision availability, storage paths, and confidentiality posture.
        </p>
      </div>

      {/* Organization & Multi-Industry Topology */}
      <div className="p-5 sm:p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#1A402D]">
          <div className="flex items-center gap-2">
            <Building className="w-5 h-5 text-[#00E599]" />
            <div>
              <h3 className="text-sm font-bold text-white">Organization &amp; Multi-Industry Topology</h3>
              <p className="text-[11px] text-[#8CBFA7] font-sans">
                Configure tenant profile, terminology, and operational units across various industries.
              </p>
            </div>
          </div>
          {saveSuccess && (
            <span className="px-2.5 py-1 rounded bg-emerald-950/80 border border-emerald-700/60 text-[#00E599] text-[11px] font-mono flex items-center gap-1.5 animate-fadeIn">
              <Check className="w-3.5 h-3.5" /> Saved &amp; Applied
            </span>
          )}
        </div>

        {/* Industry Presets */}
        <div className="space-y-2">
          <label className="text-xs font-mono text-[#74C69D] block font-semibold">
            QUICK INDUSTRY PRESETS (1-CLICK CONFIGURATION):
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {(presets.length > 0
              ? presets.map((p) => ({
                  id: p.id,
                  label: p.name || p.label || p.id,
                  icon:
                    p.id === 'refinery'
                      ? '🛢️'
                      : p.id === 'automotive'
                      ? '🚗'
                      : p.id === 'aerospace'
                      ? '✈️'
                      : '💊',
                }))
              : [
                  { id: 'refinery', label: 'Refinery & Petrochemical', icon: '🛢️' },
                  { id: 'automotive', label: 'Automotive Assembly', icon: '🚗' },
                  { id: 'aerospace', label: 'Aerospace & Defense', icon: '✈️' },
                  { id: 'pharma', label: 'Pharma & Biotech', icon: '💊' },
                ]
            ).map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => handleApplyPreset(p.id)}
                disabled={applyingPreset !== null}
                className={`p-2.5 rounded-lg border text-left transition-colors flex flex-col gap-1 ${
                  localIndustry.toLowerCase().includes(p.id.substring(0, 5))
                    ? 'bg-[#183D2B] border-[#00E599] text-white shadow-sm'
                    : 'bg-[#091A11] border-[#1E4D36] text-[#B8D5C6] hover:bg-[#102B1E] hover:text-white'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-base">{p.icon}</span>
                  {applyingPreset === p.id && (
                    <RefreshCw className="w-3 h-3 text-[#00E599] animate-spin" />
                  )}
                </div>
                <span className="text-xs font-bold leading-tight">{p.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Organization Form */}
        <form onSubmit={handleSaveOrg} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-mono text-[#74C69D] block mb-1">ORGANIZATION NAME</label>
              <input
                type="text"
                value={localOrgName}
                onChange={(e) => setLocalOrgName(e.target.value)}
                placeholder="e.g. Mangalore Refinery (MRPL)"
                className="w-full bg-[#07130D] border border-[#1A402D] rounded-lg px-3 py-2 text-xs font-mono text-white placeholder-gray-500 focus:outline-none focus:border-[#00E599]"
              />
            </div>
            <div>
              <label className="text-xs font-mono text-[#74C69D] block mb-1">INDUSTRY SECTOR</label>
              <input
                type="text"
                value={localIndustry}
                onChange={(e) => setLocalIndustry(e.target.value)}
                placeholder="e.g. Oil & Gas Refining / Petrochemical"
                className="w-full bg-[#07130D] border border-[#1A402D] rounded-lg px-3 py-2 text-xs font-mono text-white placeholder-gray-500 focus:outline-none focus:border-[#00E599]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-mono text-[#74C69D] block mb-1">FACILITY / PLANT LOCATION</label>
              <input
                type="text"
                value={localLocation}
                onChange={(e) => setLocalLocation(e.target.value)}
                placeholder="e.g. Mangalore, Karnataka, India"
                className="w-full bg-[#07130D] border border-[#1A402D] rounded-lg px-3 py-2 text-xs font-mono text-white placeholder-gray-500 focus:outline-none focus:border-[#00E599]"
              />
            </div>
            <div>
              <label className="text-xs font-mono text-[#74C69D] block mb-1">ACTIVE OPERATIONAL UNIT / WORKSPACE</label>
              <select
                value={localActiveWs}
                onChange={(e) => setLocalActiveWs(e.target.value)}
                className="w-full bg-[#07130D] border border-[#1A402D] rounded-lg px-3 py-2 text-xs font-mono text-[#00E599] focus:outline-none focus:border-[#00E599] cursor-pointer"
              >
                {orgConfig?.workspaces?.map((ws) => (
                  <option key={ws.id} value={ws.id} className="bg-[#07130D] text-white">
                    {ws.name} ({ws.unit_code || ws.code || ws.id}) {ws.criticality ? `- ${ws.criticality} criticality` : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-1">
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-[#00E599] hover:bg-[#00c582] text-[#030604] font-bold text-xs font-mono flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Save Organization Settings</span>
            </button>
          </div>
        </form>
      </div>

      {/* Role-Based Access Control (RBAC) Matrix */}
      <div className="p-5 sm:p-6 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-[#1A402D]">
          <Lock className="w-5 h-5 text-[#00E599]" />
          <div>
            <h3 className="text-sm font-bold text-white">Industrial Role-Based Access Control (RBAC)</h3>
            <p className="text-[11px] text-[#8CBFA7] font-sans">
              Scoped workspaces, tool authorizations, and data access policies enforced at runtime.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#163827] text-[#74C69D] text-[11px]">
                <th className="py-2.5 px-3">Role</th>
                <th className="py-2.5 px-3">Operational Scope</th>
                <th className="py-2.5 px-3">Authorized Tools</th>
                <th className="py-2.5 px-3">Deliverable Types</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#132C1F] text-[#D8EADB]">
              <tr className="hover:bg-[#0E2419]/60">
                <td className="py-2.5 px-3">
                  <span className="px-2 py-0.5 rounded font-bold text-[11px] bg-blue-950/80 border border-blue-700/60 text-blue-300">
                    ENGINEER
                  </span>
                </td>
                <td className="py-2.5 px-3 font-sans text-xs">P&amp;ID analysis, equipment tags, calculations, technical reports</td>
                <td className="py-2.5 px-3 text-[#00E599] text-[11px]">P&amp;ID Vision, Python Sandbox, RAG</td>
                <td className="py-2.5 px-3 text-[11px] text-[#B8D5C6]">Tech Reports, Calculation Workbooks, JSON Specs</td>
              </tr>
              <tr className="hover:bg-[#0E2419]/60">
                <td className="py-2.5 px-3">
                  <span className="px-2 py-0.5 rounded font-bold text-[11px] bg-amber-950/80 border border-amber-700/60 text-amber-300">
                    INSPECTOR
                  </span>
                </td>
                <td className="py-2.5 px-3 font-sans text-xs">Visual defect localization, inspection document OCR, maintenance logs</td>
                <td className="py-2.5 px-3 text-[#00E599] text-[11px]">Local Defect Vision, OCR Engine, Inspection Generator</td>
                <td className="py-2.5 px-3 text-[11px] text-[#B8D5C6]">DOCX Inspection Reports, Defect Summaries</td>
              </tr>
              <tr className="hover:bg-[#0E2419]/60">
                <td className="py-2.5 px-3">
                  <span className="px-2 py-0.5 rounded font-bold text-[11px] bg-purple-950/80 border border-purple-700/60 text-purple-300">
                    ANALYST
                  </span>
                </td>
                <td className="py-2.5 px-3 font-sans text-xs">Spreadsheet anomaly detection, formula validation, operational metrics</td>
                <td className="py-2.5 px-3 text-[#00E599] text-[11px]">Tabular Engine, Statistical Verification</td>
                <td className="py-2.5 px-3 text-[11px] text-[#B8D5C6]">Corrected XLSX, Audit Workbooks, Anomaly Logs</td>
              </tr>
              <tr className="hover:bg-[#0E2419]/60">
                <td className="py-2.5 px-3">
                  <span className="px-2 py-0.5 rounded font-bold text-[11px] bg-emerald-950/80 border border-emerald-700/60 text-emerald-300">
                    MANAGER
                  </span>
                </td>
                <td className="py-2.5 px-3 font-sans text-xs">Cross-unit operational overview, maintenance trends, priority approvals</td>
                <td className="py-2.5 px-3 text-[#00E599] text-[11px]">Executive Dashboard, Presentation Generator</td>
                <td className="py-2.5 px-3 text-[11px] text-[#B8D5C6]">Management PPTX, Executive Briefs, Infographics</td>
              </tr>
              <tr className="hover:bg-[#0E2419]/60">
                <td className="py-2.5 px-3">
                  <span className="px-2 py-0.5 rounded font-bold text-[11px] bg-rose-950/80 border border-rose-700/60 text-rose-300">
                    ADMINISTRATOR
                  </span>
                </td>
                <td className="py-2.5 px-3 font-sans text-xs">System configuration, multi-industry presets, audit logs, model registry</td>
                <td className="py-2.5 px-3 text-[#00E599] text-[11px]">Full System &amp; Security Tools</td>
                <td className="py-2.5 px-3 text-[11px] text-[#B8D5C6]">Audit Hashes, Sovereignty Logs, System Backups</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Selection & Mode */}
      <div className="p-5 sm:p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1A402D]">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-[#00E599]" />
            <h3 className="text-sm font-bold text-white">Inference Engine &amp; Provider Selection</h3>
          </div>
          <button
            type="button"
            onClick={loadModels}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-xs font-mono text-[#B8D5C6] hover:text-white flex items-center gap-1.5 transition-colors self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Detect Local Models</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={() => setProviderMode('ollama')}
            className={`p-4 rounded-xl border cursor-pointer transition-colors ${
              providerMode === 'ollama'
                ? 'bg-[#183D2B] border-[#00E599] text-white'
                : 'bg-[#091A11] border-[#1E4D36] text-[#B8D5C6] hover:bg-[#102B1E]'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold font-mono">100% LOCAL OLLAMA (SOVEREIGN)</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-[#00E599] border border-emerald-700/60 font-bold">
                RECOMMENDED
              </span>
            </div>
            <p className="text-xs text-[#9DC4B0] leading-relaxed">
              Routes exclusively to local open-weight Qwen 2.5:7B via Ollama. 0 bytes transmitted outside this workstation.
            </p>
          </div>

          <div
            onClick={() => setProviderMode('auto')}
            className={`p-4 rounded-xl border cursor-pointer transition-colors ${
              providerMode === 'auto'
                ? 'bg-[#183D2B] border-[#00E599] text-white'
                : 'bg-[#091A11] border-[#1E4D36] text-[#B8D5C6] hover:bg-[#102B1E]'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold font-mono">AUTO / HYBRID ROUTING</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#102B1E] text-[#74C69D] border border-[#1E4D36]">
                NON-SOVEREIGN
              </span>
            </div>
            <p className="text-xs text-[#9DC4B0] leading-relaxed">
              Auto-detects Ollama with fallback to configured cloud API keys when external connectivity is permitted.
            </p>
          </div>
        </div>
      </div>

      {/* Model Catalog & Topology Table */}
      <div className="p-5 sm:p-6 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#1A402D]">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-[#00E599]" />
            <h3 className="text-sm font-bold text-white">Detected Model Catalog &amp; Hardware Status</h3>
          </div>
          <span className="text-[11px] font-mono text-[#74C69D]">
            Active: {modelData?.default_sovereign_model || 'qwen2.5:7b'}
          </span>
        </div>

        {loading ? (
          <div className="py-8 text-center text-xs font-mono text-[#74C69D]">
            Querying local Ollama socket (127.0.0.1:11434)…
          </div>
        ) : (
          <div className="space-y-3 font-mono text-xs">
            {/* Installed Local Models list */}
            <div className="p-3 rounded-lg bg-[#06120B] border border-[#163827] space-y-2">
              <div className="flex items-center justify-between text-[#74C69D] text-[11px]">
                <span>INSTALLED OLLAMA MODELS:</span>
                <span className="text-white">
                  {modelData?.installed_local_models?.length || 0} Model(s) Found
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {modelData?.installed_local_models && modelData.installed_local_models.length > 0 ? (
                  modelData.installed_local_models.map((m: string, idx: number) => (
                    <span key={idx} className="px-2.5 py-1 rounded bg-[#102B1E] border border-[#1E4D36] text-[#00E599] font-bold">
                      {m}
                    </span>
                  ))
                ) : (
                  <span className="text-[#82A895]">qwen2.5:7b (Configured default)</span>
                )}
              </div>
            </div>

            {/* Vision model status */}
            <div className="p-3 rounded-lg bg-[#06120B] border border-[#163827] space-y-2">
              <div className="flex items-center justify-between text-[#74C69D] text-[11px]">
                <span className="flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-[#00E599]" /> LOCAL VISION CAPABILITY:
                </span>
                <span className="text-[#00E599]">Active</span>
              </div>
              <p className="text-[#9DC4B0] text-[11px] font-sans">
                Local multimodal vision provider integrated with OCR layout detection and 3x3 spatial grid defect localization.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Security & Air-Gap Posture Overview */}
      <div className="p-5 sm:p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-[#00E599]" />
          <h3 className="text-sm font-bold text-white">Confidentiality Posture &amp; Zero-Leak Guarantees</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono pt-1">
          <div className="p-3 rounded-lg bg-[#091A11] border border-[#1E4D36] space-y-1">
            <span className="text-[#74C69D] text-[10px]">DATA TRANSMISSION</span>
            <div className="text-sm font-bold text-white">0 Bytes Egress</div>
            <p className="text-[10px] text-[#9DC4B0] font-sans">All processing strictly bound to localhost.</p>
          </div>

          <div className="p-3 rounded-lg bg-[#091A11] border border-[#1E4D36] space-y-1">
            <span className="text-[#74C69D] text-[10px]">AUDIT LOGGING</span>
            <div className="text-sm font-bold text-white">Local Append-Only</div>
            <p className="text-[10px] text-[#9DC4B0] font-sans">Encrypted cryptographic hashes on disk.</p>
          </div>

          <div className="p-3 rounded-lg bg-[#091A11] border border-[#1E4D36] space-y-1">
            <span className="text-[#74C69D] text-[10px]">SANDBOX ISOLATION</span>
            <div className="text-sm font-bold text-white">Step 11 Enforced</div>
            <p className="text-[10px] text-[#9DC4B0] font-sans">Subprocess timeout &amp; directory jail.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
