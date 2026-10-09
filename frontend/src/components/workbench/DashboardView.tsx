import React, { useEffect, useState } from 'react';
import {
  FileText,
  Eye,
  Layers,
  ClipboardCheck,
  BookOpen,
  Terminal,
  Table,
  FolderArchive,
  ShieldCheck,
  Settings,
  Sparkles,
  ArrowRight,
  Cpu,
  HardDrive,
  CheckCircle2,
  Briefcase,
} from 'lucide-react';
import type { WorkbenchTab } from '@/components/IndustrialSidebar';
import { fetchGeneratedFiles, fetchModelRegistry, type GeneratedFileInfo } from '@/lib/api';
import {
  ROLE_DISPLAY_NAMES,
  ROLE_BADGE_COLORS,
  ROLE_ALLOWED_MODULES,
  type UserProfile,
  type OrgConfig,
  type UserRole,
} from '@/types/auth';
import { Building, UserCheck } from 'lucide-react';

interface DashboardViewProps {
  onNavigate: (tab: WorkbenchTab) => void;
  user?: UserProfile | null;
  orgConfig?: OrgConfig | null;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate, user, orgConfig }) => {
  const [recentFiles, setRecentFiles] = useState<GeneratedFileInfo[]>([]);
  const [modelInfo, setModelInfo] = useState<any>(null);

  useEffect(() => {
    let mounted = true;
    Promise.all([fetchGeneratedFiles(), fetchModelRegistry()]).then(([files, models]) => {
      if (mounted) {
        setRecentFiles(files.slice(0, 5));
        setModelInfo(models);
      }
    }).catch(() => {});
    return () => { mounted = false; };
  }, []);

  const TOOLS = [
    {
      tab: 'manager' as WorkbenchTab,
      title: 'Manager Overview',
      desc: 'Executive summaries, evidence-grounded action priorities, and pending human sign-offs.',
      icon: Briefcase,
      badge: 'Executive',
    },
    {
      tab: 'document' as WorkbenchTab,
      title: 'Document Analysis',
      desc: 'Local OCR on scanned inspection records & engineering specifications.',
      icon: FileText,
      badge: 'Local OCR',
    },
    {
      tab: 'defect' as WorkbenchTab,
      title: 'Image Defect Analysis',
      desc: 'Multimodal vision inspection for cracks, corrosion, and structural wear.',
      icon: Eye,
      badge: 'Local Vision',
    },
    {
      tab: 'drawing' as WorkbenchTab,
      title: 'Engineering Drawing / P&ID',
      desc: 'Extract equipment tags, lines, and instrument specs from schematics.',
      icon: Layers,
      badge: 'P&ID Parser',
    },
    {
      tab: 'doc_cad' as WorkbenchTab,
      title: 'Document-to-CAD Generator',
      desc: 'Synthesize deterministic AutoCAD DXF & vector SVG drawings directly from technical text & documents.',
      icon: Layers,
      badge: 'AutoCAD DXF',
    },
    {
      tab: 'reports' as WorkbenchTab,
      title: 'Inspection Reports',
      desc: 'Produce formal statutory inspection reports, risk matrices & sign-offs.',
      icon: ClipboardCheck,
      badge: 'DOCX / PPTX',
    },
    {
      tab: 'sop' as WorkbenchTab,
      title: 'Knowledge Base / SOPs',
      desc: 'Semantic retrieval over on-premise industrial standards via SQLite RAG.',
      icon: BookOpen,
      badge: 'Local RAG',
    },
    {
      tab: 'sandbox' as WorkbenchTab,
      title: 'Coding Sandbox',
      desc: 'Execute deterministic Python engineering computations in isolation.',
      icon: Terminal,
      badge: 'Python Runner',
    },
    {
      tab: 'spreadsheet' as WorkbenchTab,
      title: 'Spreadsheet Analysis',
      desc: 'Ingest operational datasets and compute threshold anomaly deviations.',
      icon: Table,
      badge: 'Tabular AI',
    },
    {
      tab: 'doc_excel' as WorkbenchTab,
      title: 'Document-to-Excel Generator',
      desc: 'Extract multi-sheet asset inventories and maintenance registers into genuine styled Excel workbooks.',
      icon: Table,
      badge: 'Multi-Sheet XLSX',
    },
    {
      tab: 'files' as WorkbenchTab,
      title: 'Generated Files',
      desc: 'Review and download synthesized inspection reports and presentations.',
      icon: FolderArchive,
      badge: 'Catalog',
    },
    {
      tab: 'audit' as WorkbenchTab,
      title: 'Sovereignty & Audit',
      desc: 'Cryptographic proof, zero-external-call monitoring and audit logs.',
      icon: ShieldCheck,
      badge: 'Air-Gapped',
    },
    {
      tab: 'settings' as WorkbenchTab,
      title: 'Workbench Settings',
      desc: 'Model routing parameters, local Ollama detection, and air-gap policy.',
      icon: Settings,
      badge: 'Config',
    },
  ];

  const userRole = (user?.role || 'administrator') as UserRole;
  const badgeStyle = ROLE_BADGE_COLORS[userRole] || ROLE_BADGE_COLORS.administrator;
  const allowedModules = ROLE_ALLOWED_MODULES[userRole] || ROLE_ALLOWED_MODULES.administrator;
  const filteredTools = TOOLS.filter((t) => allowedModules.includes(t.tab));
  const activeWorkspace = orgConfig?.workspaces?.find(
    (w) => w.id === orgConfig.active_workspace_id
  );

  return (
    <div className="space-y-8 font-serif text-gray-100">
      {/* Organization & Role Context Strip */}
      <div className="p-4 rounded-xl bg-[#091D13] border border-[#183D2B] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center text-[#00E599]">
            <Building className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-bold text-white">
                {orgConfig?.org_name || 'Mangalore Refinery & Petrochemicals (MRPL)'}
              </span>
              <span className="text-xs text-[#74C69D] font-mono">
                • {orgConfig?.industry || 'Refinery & Petrochemicals'}
              </span>
            </div>
            <p className="text-xs text-[#9DC4B0] font-mono mt-0.5">
              Active Unit: <strong className="text-white">{activeWorkspace ? activeWorkspace.name : 'Crude Distillation Unit (CDU-1)'}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-xs font-mono text-[#9DC4B0] flex items-center gap-1">
            <UserCheck className="w-3.5 h-3.5 text-[#00E599]" />
            Active Role:
          </span>
          <span className={`text-xs font-mono font-bold px-2.5 py-1 rounded border ${badgeStyle.bg} ${badgeStyle.text} ${badgeStyle.border}`}>
            {ROLE_DISPLAY_NAMES[userRole] || userRole.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#1A402D]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#00E599]/15 border border-[#00E599]/40 text-[#00E599]">
              SOVEREIGN WORKSPACE
            </span>
            <span className="text-xs text-[#74C69D] font-mono">
              {ROLE_DISPLAY_NAMES[userRole] || userRole.toUpperCase()} Workspace
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            {userRole === 'engineer' && 'Plant Engineering & Technical Workspace'}
            {userRole === 'inspector' && 'Field Inspection & Quality Workspace'}
            {userRole === 'data_analyst' && 'Operations Telemetry & Data Analytics'}
            {userRole === 'manager' && 'Asset Management & Executive Overview'}
            {(userRole === 'administrator' || userRole === 'super_admin') && 'Industrial Operations & Governance Center'}
          </h1>
          <p className="text-sm text-[#B8D5C6] mt-1 max-w-2xl">
            {userRole === 'engineer' && 'P&ID schematic deconstruction, automated equipment tag extraction, and on-premise calculation workbooks.'}
            {userRole === 'inspector' && 'Multimodal visual defect inspection, field report OCR, and statutory compliance certification.'}
            {userRole === 'data_analyst' && 'Telemetry anomaly detection, threshold exceedance calculations, and multi-sheet XLSX synthesis.'}
            {userRole === 'manager' && 'Cross-unit compliance status, inspection priority tracking, and verifiable executive briefs.'}
            {(userRole === 'administrator' || userRole === 'super_admin') && 'Autonomous multi-modal workbench operating 100% on-premise with zero cloud data transmission.'}
          </p>
        </div>

        {/* Quick Launch Demo */}
        <button
          type="button"
          onClick={() => onNavigate('demo')}
          className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#52B788] hover:bg-[#74C69D] active:scale-[0.98] text-[#07130D] font-bold text-xs sm:text-sm transition-all duration-200 shadow-sm hover:shadow-[0_0_16px_rgba(82,183,136,0.35)] shrink-0"
        >
          <Sparkles className="w-4 h-4 fill-[#07130D]" />
          <span>Launch SIH 26117 Demo</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#0F261B] border border-[#1E4D36] space-y-2">
          <div className="flex items-center justify-between text-[#74C69D] text-xs font-mono">
            <span>Air-Gap Telemetry</span>
            <ShieldCheck className="w-4 h-4 text-[#00E599]" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">0 External Calls</div>
          <div className="text-[11px] text-[#9DC4B0] flex items-center gap-1 font-mono">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#00E599]" />
            <span>Cryptographically Verified</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#0F261B] border border-[#1E4D36] space-y-2">
          <div className="flex items-center justify-between text-[#74C69D] text-xs font-mono">
            <span>Local Reasoning LLM</span>
            <Cpu className="w-4 h-4 text-[#00E599]" />
          </div>
          <div className="text-2xl font-bold text-white font-mono truncate">
            {modelInfo?.default_sovereign_model || 'Qwen 2.5:7B'}
          </div>
          <div className="text-[11px] text-[#9DC4B0] font-mono">
            Ollama On-Premise Engine
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#0F261B] border border-[#1E4D36] space-y-2">
          <div className="flex items-center justify-between text-[#74C69D] text-xs font-mono">
            <span>Local Knowledge Store</span>
            <HardDrive className="w-4 h-4 text-[#00E599]" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">SOP Vector RAG</div>
          <div className="text-[11px] text-[#9DC4B0] font-mono">
            Local SQLite pgvector schema
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#0F261B] border border-[#1E4D36] space-y-2">
          <div className="flex items-center justify-between text-[#74C69D] text-xs font-mono">
            <span>Active Tool Sandbox</span>
            <Terminal className="w-4 h-4 text-[#00E599]" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">Step 11 Sandbox</div>
          <div className="text-[11px] text-[#9DC4B0] font-mono">
            Isolated Python 3.11 Runtime
          </div>
        </div>
      </div>

      {/* Industrial Tools Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white tracking-wide">
            Industrial Analysis &amp; Engineering Modules
          </h2>
          <span className="text-xs text-[#74C69D] font-mono">
            {filteredTools.length} Permitted Modules ({ROLE_DISPLAY_NAMES[userRole] || userRole})
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTools.map((tool) => {
            const Icon = tool.icon;
            return (
              <div
                key={tool.tab}
                onClick={() => onNavigate(tool.tab)}
                className="group p-5 rounded-xl bg-[#0E2419] hover:bg-[#133022] border border-[#1A402D] hover:border-[#00E599]/60 cursor-pointer transition-all duration-150 flex flex-col justify-between space-y-4 shadow-sm"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="w-9 h-9 rounded-lg bg-[#143324] border border-[#23573E] group-hover:border-[#00E599]/60 flex items-center justify-center text-[#00E599] transition-colors">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#102B1E] border border-[#1E4D36] text-[#74C69D]">
                      {tool.badge}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-white group-hover:text-[#00E599] transition-colors">
                    {tool.title}
                  </h3>
                  <p className="text-xs text-[#9DC4B0] leading-relaxed">
                    {tool.desc}
                  </p>
                </div>

                <div className="pt-2 border-t border-[#183B29] flex items-center justify-between text-xs text-[#74C69D] group-hover:text-white font-semibold transition-colors">
                  <span>Open Module</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Deliverables Snapshot */}
      <div className="p-5 rounded-xl bg-[#0F261B] border border-[#1E4D36] space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FolderArchive className="w-4 h-4 text-[#00E599]" />
            <h3 className="text-sm font-bold text-white">Recent Generated Deliverables</h3>
          </div>
          <button
            type="button"
            onClick={() => onNavigate('files')}
            className="text-xs text-[#74C69D] hover:text-white font-mono flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {recentFiles.length === 0 ? (
          <p className="text-xs text-[#82A895] font-mono py-4 text-center">
            No local deliverables synthesized yet. Run an analysis above to generate reports and slides.
          </p>
        ) : (
          <div className="divide-y divide-[#1A402D]">
            {recentFiles.map((f, i) => (
              <div key={i} className="py-2.5 flex items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-[#163827] border border-[#23573E] text-[#00E599] uppercase">
                    {f.extension}
                  </span>
                  <span className="text-[#DCE8E1] font-mono truncate">{f.filename}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-[10px] font-mono text-[#74C69D]">
                    {(f.size_bytes / 1024).toFixed(1)} KB
                  </span>
                  <a
                    href={f.download_url}
                    download={f.filename}
                    className="text-[11px] font-mono text-[#00E599] hover:underline"
                  >
                    Download
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
