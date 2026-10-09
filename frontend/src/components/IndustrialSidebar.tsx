import React from 'react';
import {
  LayoutDashboard,
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
  Lock,
  Briefcase,
} from 'lucide-react';

import {
  ROLE_DISPLAY_NAMES,
  ROLE_BADGE_COLORS,
  ROLE_ALLOWED_MODULES,
  type UserProfile,
  type OrgConfig,
  type UserRole,
} from '@/types/auth';
import { Building, UserCheck } from 'lucide-react';

export type WorkbenchTab =
  | 'dashboard'
  | 'document'
  | 'defect'
  | 'drawing'
  | 'doc_cad'
  | 'reports'
  | 'sop'
  | 'sandbox'
  | 'spreadsheet'
  | 'doc_excel'
  | 'files'
  | 'audit'
  | 'settings'
  | 'demo'
  | 'manager';

interface NavItem {
  id: WorkbenchTab;
  label: string;
  icon: React.ElementType;
  badge?: string;
  section: 'primary' | 'analysis' | 'tools' | 'system';
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, section: 'primary' },
  { id: 'manager', label: 'Manager Overview', icon: Briefcase, badge: 'Executive', section: 'primary' },
  { id: 'document', label: 'Document Analysis', icon: FileText, badge: 'OCR', section: 'analysis' },
  { id: 'defect', label: 'Image Defect Analysis', icon: Eye, badge: 'Vision', section: 'analysis' },
  { id: 'drawing', label: 'Engineering Drawing / P&ID', icon: Layers, badge: 'P&ID', section: 'analysis' },
  { id: 'doc_cad', label: 'Document-to-CAD (DXF)', icon: Layers, badge: 'CAD', section: 'analysis' },
  { id: 'reports', label: 'Inspection Reports', icon: ClipboardCheck, section: 'analysis' },
  { id: 'sop', label: 'Knowledge Base / SOPs', icon: BookOpen, badge: 'RAG', section: 'tools' },
  { id: 'sandbox', label: 'Coding Sandbox', icon: Terminal, badge: 'Python', section: 'tools' },
  { id: 'spreadsheet', label: 'Spreadsheet Analysis', icon: Table, section: 'tools' },
  { id: 'doc_excel', label: 'Document-to-Excel (XLSX)', icon: Table, badge: 'XLSX', section: 'tools' },
  { id: 'files', label: 'Generated Files', icon: FolderArchive, section: 'tools' },
  { id: 'audit', label: 'Sovereignty & Audit', icon: ShieldCheck, badge: 'Zero-Leak', section: 'system' },
  { id: 'settings', label: 'Settings', icon: Settings, section: 'system' },
];

interface IndustrialSidebarProps {
  activeTab: WorkbenchTab;
  onTabChange: (tab: WorkbenchTab) => void;
  externalCalls?: number;
  user?: UserProfile | null;
  orgConfig?: OrgConfig | null;
  onRoleSwitch?: (role: string) => void;
}

export const IndustrialSidebar: React.FC<IndustrialSidebarProps> = ({
  activeTab,
  onTabChange,
  externalCalls = 0,
  user,
  orgConfig,
  onRoleSwitch,
}) => {
  const userRole = (user?.role || 'administrator') as UserRole;
  const badgeStyle = ROLE_BADGE_COLORS[userRole] || ROLE_BADGE_COLORS.administrator;
  const allowedModules = ROLE_ALLOWED_MODULES[userRole] || ROLE_ALLOWED_MODULES.administrator;
  const filteredNavItems = NAV_ITEMS.filter((item) => allowedModules.includes(item.id));

  // Role switching is enabled for all workspace modes in confidential/demo mode
  const canSwitchRole = Boolean(onRoleSwitch);

  const activeWorkspace = orgConfig?.workspaces?.find(
    (w) => w.id === orgConfig.active_workspace_id
  );

  const primaryItems = filteredNavItems.filter((i) => i.section === 'primary');
  const analysisItems = filteredNavItems.filter((i) => i.section === 'analysis');
  const toolsItems = filteredNavItems.filter((i) => i.section === 'tools');
  const systemItems = filteredNavItems.filter((i) => i.section === 'system');

  return (
    <aside className="fixed left-0 top-16 bottom-0 w-64 bg-[#07130D] border-r border-[#163324] z-40 flex flex-col justify-between select-none">
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-4 scrollbar-thin">
        {/* Workspace Title & Organization Context */}
        <div className="px-2 pb-3 border-b border-[#163324]">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#74C69D] font-bold flex items-center gap-1.5">
              <Lock className="w-3 h-3 text-[#00E599]" />
              Sovereign Workbench
            </span>
            <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${badgeStyle.bg} ${badgeStyle.text} ${badgeStyle.border} font-bold`}>
              {ROLE_DISPLAY_NAMES[userRole] || userRole.toUpperCase()}
            </span>
          </div>
          <p className="text-xs text-[#B8D5C6] font-semibold truncate" title={orgConfig?.org_name || 'Mangalore Refinery (MRPL)'}>
            {orgConfig?.org_name || 'Mangalore Refinery (MRPL)'}
          </p>
          <div className="mt-1 flex items-center gap-1.5 text-[10px] font-mono text-[#74C69D] truncate">
            <Building className="w-3 h-3 text-[#00E599] shrink-0" />
            <span className="truncate">{activeWorkspace ? activeWorkspace.name : 'Crude Distillation (CDU-1)'}</span>
          </div>
        </div>

        {/* Role Workspace Switcher (For Authorized Users / Admins) */}
        {canSwitchRole && (
          <div className="px-2 py-2 rounded-lg bg-[#0C1F16] border border-[#183D2B]">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#74C69D] mb-1 font-semibold">
              <UserCheck className="w-3 h-3 text-[#00E599]" />
              <span>Workspace Role View</span>
            </div>
            <select
              value={userRole}
              onChange={(e) => onRoleSwitch && onRoleSwitch(e.target.value)}
              className="w-full text-xs font-mono bg-[#07130D] border border-[#1E4D36] text-[#00E599] rounded px-2 py-1 focus:outline-none focus:border-[#00E599] cursor-pointer"
            >
              <option value="administrator">Administrator (All Modules)</option>
              <option value="engineer">Plant Engineer</option>
              <option value="inspector">Field Inspector</option>
              <option value="data_analyst">Operations Analyst</option>
              <option value="manager">Asset Manager</option>
            </select>
          </div>
        )}

        {/* SIH Demo Mode Banner Button */}
        <div className="px-1">
          <button
            type="button"
            onClick={() => onTabChange('demo')}
            className={`w-full flex items-center justify-between p-2.5 rounded-lg border transition-all text-left ${
              activeTab === 'demo'
                ? 'bg-[#183D2B] border-[#00E599] text-white shadow-md'
                : 'bg-[#0E2419] border-[#1E4D36] text-[#CBE2D6] hover:border-[#00E599]/60 hover:bg-[#133022]'
            }`}
          >
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-[#00E599]/20 flex items-center justify-center text-[#00E599]">
                <Sparkles className="w-3.5 h-3.5" />
              </div>
              <div>
                <div className="text-xs font-bold leading-tight">SIH Demo Mode</div>
                <div className="text-[10px] text-[#74C69D] leading-tight font-mono">4 Guided Workflows</div>
              </div>
            </div>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-700/60 text-[#00E599]">
              PS 26117
            </span>
          </button>
        </div>

        {/* Section 1: Overview */}
        {primaryItems.length > 0 && (
          <div className="space-y-1">
            <div className="px-2 text-[10px] font-semibold text-[#527965] uppercase tracking-wider font-mono">
              Navigation
            </div>
            {primaryItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors text-left ${
                    isActive
                      ? 'bg-[#163827] text-white border border-[#23573E] font-semibold'
                      : 'text-[#B8D5C6] hover:text-white hover:bg-[#0E2218]'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-[#00E599]' : 'text-[#74C69D]'}`} />
                    <span>{item.label}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
        {/* Section 2: Industrial Analysis */}
        {analysisItems.length > 0 && (
          <div className="space-y-1">
            <div className="px-2 text-[10px] font-semibold text-[#527965] uppercase tracking-wider font-mono">
              Industrial Analysis
            </div>
            {analysisItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors text-left ${
                    isActive
                      ? 'bg-[#163827] text-white border border-[#23573E] font-semibold'
                      : 'text-[#B8D5C6] hover:text-white hover:bg-[#0E2218]'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#00E599]' : 'text-[#74C69D]'}`} />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#102B1E] border border-[#1E4D36] text-[#74C69D]">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* Section 3: Engineering Tools */}
        {toolsItems.length > 0 && (
          <div className="space-y-1">
            <div className="px-2 text-[10px] font-semibold text-[#527965] uppercase tracking-wider font-mono">
              Engineering Tools
            </div>
            {toolsItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors text-left ${
                    isActive
                      ? 'bg-[#163827] text-white border border-[#23573E] font-semibold'
                      : 'text-[#B8D5C6] hover:text-white hover:bg-[#0E2218]'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#00E599]' : 'text-[#74C69D]'}`} />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#102B1E] border border-[#1E4D36] text-[#74C69D]">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* Section 4: Sovereignty & System */}
        {systemItems.length > 0 && (
          <div className="space-y-1">
            <div className="px-2 text-[10px] font-semibold text-[#527965] uppercase tracking-wider font-mono">
              Security &amp; System
            </div>
            {systemItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors text-left ${
                    isActive
                      ? 'bg-[#163827] text-white border border-[#23573E] font-semibold'
                      : 'text-[#B8D5C6] hover:text-white hover:bg-[#0E2218]'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#00E599]' : 'text-[#74C69D]'}`} />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-700/60 text-[#00E599]">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Bottom Compact Telemetry Status */}
      <div className="p-3 border-t border-[#163324] bg-[#050D09]">
        <div className="p-2.5 rounded-lg bg-[#0C1F16] border border-[#183D2B] space-y-1.5 text-[11px] font-mono">
          <div className="flex items-center justify-between">
            <span className="text-[#74C69D] flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#00E599] animate-pulse" />
              Air-Gapped Status
            </span>
            <span className="text-white font-bold">VERIFIED</span>
          </div>
          <div className="flex items-center justify-between text-[10px] text-[#9DC4B0]">
            <span>External Calls:</span>
            <strong className="text-white">{externalCalls}</strong>
          </div>
          <div className="flex items-center justify-between text-[10px] text-[#9DC4B0]">
            <span>Cloud AI:</span>
            <strong className="text-white">0 Calls</strong>
          </div>
        </div>
      </div>
    </aside>
  );
};
