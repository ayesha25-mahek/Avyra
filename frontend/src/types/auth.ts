export type UserRole =
  | 'super_admin'
  | 'administrator'
  | 'engineer'
  | 'inspector'
  | 'data_analyst'
  | 'manager'
  | 'technical_lead'
  | 'pr_lead'
  | 'technical_team'
  | 'pr_team'
  | 'maintenance_personnel'
  | 'operations_analyst';

export interface UserProfile {
  email: string;
  full_name: string;
  role: UserRole;
  original_role?: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string | null;
  permissions: string[];
}

export interface AuthResponse {
  token: string;
  user: UserProfile;
}

export interface ActivityLog {
  id: string;
  actor_email: string;
  actor_role: string;
  action: string;
  details: Record<string, unknown>;
  timestamp: string;
}

export interface WorkspaceUnit {
  id: string;
  name: string;
  description: string;
  unit_code?: string;
  code?: string;
  criticality?: string;
}

export interface OrgTerminology {
  asset_label: string;
  inspection_label: string;
  drawing_label: string;
  standard_label: string;
  defect_label?: string;
  telemetry_label?: string;
}

export interface OrgConfig {
  org_id: string;
  org_name: string;
  industry: string;
  facility_location?: string;
  active_workspace_id: string;
  workspaces: WorkspaceUnit[];
  terminology: OrgTerminology;
  enabled_modules: string[];
}

export const ROLE_DISPLAY_NAMES: Record<UserRole, string> = {
  administrator: 'Administrator',
  super_admin: 'Super Admin',
  engineer: 'Plant Engineer',
  inspector: 'Field Inspector',
  data_analyst: 'Operations Analyst',
  manager: 'Asset Manager',
  technical_lead: 'Technical Lead',
  pr_lead: 'PR Lead',
  technical_team: 'Technical Team Member',
  pr_team: 'PR Team Member',
  maintenance_personnel: 'Maintenance Personnel',
  operations_analyst: 'Operations Analyst',
};

export const ROLE_BADGE_COLORS: Record<UserRole, { bg: string; text: string; border: string }> = {
  administrator: { bg: 'bg-[#183D2B]', text: 'text-[#00E599]', border: 'border-[#23573E]' },
  super_admin: { bg: 'bg-[#183D2B]', text: 'text-[#00E599]', border: 'border-[#23573E]' },
  engineer: { bg: 'bg-[#102B3F]', text: 'text-[#38BDF8]', border: 'border-[#1E4E6D]' },
  inspector: { bg: 'bg-[#3B2910]', text: 'text-[#FBBF24]', border: 'border-[#61451B]' },
  data_analyst: { bg: 'bg-[#2E183B]', text: 'text-[#C084FC]', border: 'border-[#4D2863]' },
  manager: { bg: 'bg-[#163827]', text: 'text-[#74C69D]', border: 'border-[#1E4D36]' },
  technical_lead: { bg: 'bg-[#102B3F]', text: 'text-[#38BDF8]', border: 'border-[#1E4E6D]' },
  technical_team: { bg: 'bg-[#102B3F]', text: 'text-[#38BDF8]', border: 'border-[#1E4E6D]' },
  pr_lead: { bg: 'bg-[#163827]', text: 'text-[#74C69D]', border: 'border-[#1E4D36]' },
  pr_team: { bg: 'bg-[#2E183B]', text: 'text-[#C084FC]', border: 'border-[#4D2863]' },
  maintenance_personnel: { bg: 'bg-[#3B2910]', text: 'text-[#FBBF24]', border: 'border-[#61451B]' },
  operations_analyst: { bg: 'bg-[#2E183B]', text: 'text-[#C084FC]', border: 'border-[#4D2863]' },
};

export const ROLE_ALLOWED_MODULES: Record<UserRole, string[]> = {
  administrator: ['dashboard', 'manager', 'document', 'defect', 'drawing', 'doc_cad', 'reports', 'sop', 'sandbox', 'spreadsheet', 'doc_excel', 'files', 'audit', 'settings'],
  super_admin: ['dashboard', 'manager', 'document', 'defect', 'drawing', 'doc_cad', 'reports', 'sop', 'sandbox', 'spreadsheet', 'doc_excel', 'files', 'audit', 'settings'],
  engineer: ['dashboard', 'drawing', 'doc_cad', 'document', 'sandbox', 'sop', 'spreadsheet', 'doc_excel', 'files'],
  technical_lead: ['dashboard', 'drawing', 'doc_cad', 'document', 'sandbox', 'sop', 'spreadsheet', 'doc_excel', 'files', 'audit'],
  technical_team: ['dashboard', 'drawing', 'doc_cad', 'document', 'sandbox', 'sop', 'spreadsheet', 'doc_excel', 'files'],
  inspector: ['dashboard', 'defect', 'document', 'reports', 'sop', 'files'],
  maintenance_personnel: ['dashboard', 'defect', 'document', 'reports', 'sop', 'files'],
  data_analyst: ['dashboard', 'spreadsheet', 'doc_excel', 'sandbox', 'document', 'files'],
  operations_analyst: ['dashboard', 'spreadsheet', 'doc_excel', 'sandbox', 'document', 'files'],
  manager: ['dashboard', 'manager', 'reports', 'defect', 'spreadsheet', 'doc_excel', 'files', 'audit'],
  pr_lead: ['dashboard', 'manager', 'reports', 'defect', 'spreadsheet', 'doc_excel', 'files', 'audit'],
  pr_team: ['dashboard', 'spreadsheet', 'doc_excel', 'document', 'files'],
};
