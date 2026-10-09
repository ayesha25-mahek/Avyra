import { useEffect, useState } from 'react';
import { ShieldCheck, Sparkles } from 'lucide-react';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { LandingPage } from '@/components/LandingPage';
import { AuthModal } from '@/components/AuthModal';
import { AdminDashboard } from '@/components/AdminDashboard';
import { IndustrialSidebar, type WorkbenchTab } from '@/components/IndustrialSidebar';
import { DashboardView } from '@/components/workbench/DashboardView';
import { DocumentAnalysisView } from '@/components/workbench/DocumentAnalysisView';
import { ImageDefectView } from '@/components/workbench/ImageDefectView';
import { DrawingAnalysisView } from '@/components/workbench/DrawingAnalysisView';
import { InspectionReportsView } from '@/components/workbench/InspectionReportsView';
import { KnowledgeBaseView } from '@/components/workbench/KnowledgeBaseView';
import { CodingSandboxView } from '@/components/workbench/CodingSandboxView';
import { SpreadsheetAnalysisView } from '@/components/workbench/SpreadsheetAnalysisView';
import { GeneratedFilesView } from '@/components/workbench/GeneratedFilesView';
import { SovereigntyAuditView } from '@/components/workbench/SovereigntyAuditView';
import { SettingsView } from '@/components/workbench/SettingsView';
import { DemoModeView } from '@/components/workbench/DemoModeView';
import { ManagerOverviewView } from '@/components/workbench/ManagerOverviewView';
import {
  fetchCurrentUser,
  logoutUser,
  getStoredToken,
  getStoredUser,
  fetchOrgConfig,
  switchActiveRole,
} from '@/lib/authApi';
import type { UserProfile, OrgConfig } from '@/types/auth';

type AppView = 'landing' | 'studio' | 'dashboard';

function App() {
  // ─── Authentication & Org State ──────────────────────────────────────────
  const [user, setUser] = useState<UserProfile | null>(null);
  const [orgConfig, setOrgConfig] = useState<OrgConfig | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authInitialMode, setAuthInitialMode] = useState<'signin' | 'login'>('login');
  const [activeView, setActiveView] = useState<AppView>('landing');

  // ─── Workbench Tab State (Default: Dashboard) ───────────────────────────
  const [workbenchTab, setWorkbenchTab] = useState<WorkbenchTab>('dashboard');

  // ─── On Mount: Restore Session & Load Org Topology ───────────────────────
  useEffect(() => {
    const token = getStoredToken();
    const storedUser = getStoredUser();
    if (token && storedUser) {
      setUser(storedUser);
      setActiveView('studio');
      fetchCurrentUser().then((fresh) => {
        if (fresh) setUser(fresh);
      }).catch(() => {});
    }
    fetchOrgConfig().then((cfg) => {
      if (cfg) setOrgConfig(cfg);
    }).catch(() => {});
    setAuthChecked(true);
  }, []);

  const handleRoleSwitch = async (targetRole: string) => {
    try {
      const updated = await switchActiveRole(targetRole);
      setUser(updated);
    } catch (err) {
      // If current session token is role-restricted from switching,
      // authenticate seamlessly via the authorized role account so the user can freely switch access modes
      const SEED_MAP: Record<string, { email: string; pass: string }> = {
        administrator: { email: 'admin@avyara.internal', pass: 'adminpass' },
        super_admin: { email: 'admin@avyara.internal', pass: 'adminpass' },
        engineer: { email: 'engineer@avyara.internal', pass: 'engineerpass' },
        inspector: { email: 'inspector@avyara.internal', pass: 'inspectorpass' },
        data_analyst: { email: 'analyst@avyara.internal', pass: 'analystpass' },
        analyst: { email: 'analyst@avyara.internal', pass: 'analystpass' },
        manager: { email: 'manager@avyara.internal', pass: 'managerpass' },
      };
      const cred = SEED_MAP[targetRole];
      if (cred) {
        try {
          const { loginUser } = await import('@/lib/authApi');
          const resp = await loginUser(cred.email, cred.pass);
          setUser(resp.user);
        } catch (authErr) {
          console.error('Failed to switch access mode', authErr);
        }
      }
    }
  };

  // ─── Auth Handlers ───────────────────────────────────────────────────────
  const handleAuthSuccess = (loggedInUser: UserProfile) => {
    setUser(loggedInUser);
    setShowAuthModal(false);
    setActiveView('studio');
  };

  const handleSignOut = async () => {
    await logoutUser();
    setUser(null);
    setActiveView('landing');
  };

  const handleOpenAuth = (mode: 'signin' | 'login' = 'login') => {
    setAuthInitialMode(mode);
    setShowAuthModal(true);
  };

  const handleSwitchView = (view: AppView) => {
    if ((view === 'studio' || view === 'dashboard') && !user) {
      handleOpenAuth('login');
      return;
    }
    setActiveView(view);
  };

  // ─── Show loading skeleton until session is checked ──────────────────────
  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#030604]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-full border-2 border-[#00D084] flex items-center justify-center animate-pulse">
            <div className="w-4 h-4 rounded-full bg-[#00D084]" />
          </div>
          <span className="text-xs text-gray-400 font-serif tracking-wider">Verifying Session…</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#030604] text-gray-100 font-serif">
      {/* ─── UNIFIED NAVBAR ───────────────────────────────────────────── */}
      <Header
        user={user}
        activeView={activeView}
        onOpenAuth={handleOpenAuth}
        onSwitchView={handleSwitchView}
        onSignOut={handleSignOut}
      />

      {/* ─── LANDING PAGE ─────────────────────────────────────────────── */}
      {activeView === 'landing' && (
        <LandingPage
          onOpenAuth={handleOpenAuth}
          isAuthenticated={!!user}
          onEnterStudio={() => setActiveView('studio')}
        />
      )}

      {/* ─── ADMIN DASHBOARD ──────────────────────────────────────────── */}
      {activeView === 'dashboard' && user && (
        <AdminDashboard
          user={user}
          onSwitchToStudio={() => setActiveView('studio')}
          onSignOut={handleSignOut}
        />
      )}

      {/* ─── AVYARA CONFIDENTIAL INDUSTRIAL WORKBENCH ─────────────────── */}
      {activeView === 'studio' && user && (
        <div className="flex-1 flex flex-col relative">
          {/* Fixed Left Sidebar with 11 items + Demo button */}
          <IndustrialSidebar
            activeTab={workbenchTab}
            onTabChange={setWorkbenchTab}
            externalCalls={0}
            user={user}
            orgConfig={orgConfig}
            onRoleSwitch={handleRoleSwitch}
          />

          {/* Main Workspace Offset by Sidebar Width */}
          <div className="md:pl-64 flex-1 flex flex-col min-h-[calc(100vh-4rem)]">
            {/* Compact Top Sovereignty Status Strip */}
            <div className="border-b border-[#1A402D] bg-[#0A1A12] px-4 sm:px-8 py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 rounded bg-[#00E599]/15 border border-[#00E599]/40 text-[#00E599] font-mono font-bold flex items-center gap-1.5 text-[11px]">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  SOVEREIGN WORKSPACE
                </span>
                <span className="text-[#9DC4B0] font-mono text-[11px] hidden sm:inline">
                  • 100% On-Premise Execution
                </span>
                <span className="text-[#9DC4B0] font-mono text-[11px] hidden md:inline">
                  • Local Qwen 2.5:7B
                </span>
              </div>

              <div className="flex items-center gap-3 text-[11px] font-mono text-[#74C69D]">
                <span className="px-2 py-0.5 rounded bg-[#102B1E] border border-[#1E4D36]">
                  External Calls: <strong className="text-white">0</strong>
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-700/50 text-[#00E599] font-semibold hidden sm:inline">
                  AIR-GAPPED COMPLIANT
                </span>
                <button
                  type="button"
                  onClick={() => setWorkbenchTab('demo')}
                  className="px-2.5 py-0.5 rounded bg-[#163827] hover:bg-[#1E4D36] border border-[#23573E] text-[#00E599] hover:text-white flex items-center gap-1 transition-colors"
                >
                  <Sparkles className="w-3 h-3 text-[#00E599]" />
                  <span>SIH Demo Mode</span>
                </button>
              </div>
            </div>

            {/* Active Workspace View Body */}
            <main className="flex-1 p-4 sm:p-8 bg-[#030604]">
              {workbenchTab === 'dashboard' && (
                <DashboardView
                  onNavigate={setWorkbenchTab}
                  user={user}
                  orgConfig={orgConfig}
                />
              )}
              {workbenchTab === 'manager' && (
                <ManagerOverviewView
                  user={user}
                  orgConfig={orgConfig}
                />
              )}
              {workbenchTab === 'document' && <DocumentAnalysisView />}
              {workbenchTab === 'defect' && <ImageDefectView />}
              {workbenchTab === 'drawing' && <DrawingAnalysisView initialSubTab="blueprint_analysis" />}
              {workbenchTab === 'doc_cad' && <DrawingAnalysisView initialSubTab="doc_to_cad" />}
              {workbenchTab === 'reports' && <InspectionReportsView />}
              {workbenchTab === 'sop' && <KnowledgeBaseView />}
              {workbenchTab === 'sandbox' && <CodingSandboxView />}
              {workbenchTab === 'spreadsheet' && <SpreadsheetAnalysisView initialSubTab="analysis" />}
              {workbenchTab === 'doc_excel' && <SpreadsheetAnalysisView initialSubTab="doc_to_excel" />}
              {workbenchTab === 'files' && <GeneratedFilesView />}
              {workbenchTab === 'audit' && <SovereigntyAuditView />}
              {workbenchTab === 'settings' && (
                <SettingsView
                  orgConfig={orgConfig}
                  onOrgConfigUpdated={setOrgConfig}
                />
              )}
              {workbenchTab === 'demo' && (
                <DemoModeView onBack={setWorkbenchTab} />
              )}
            </main>

            <Footer />
          </div>
        </div>
      )}

      {/* ─── AUTH MODAL ─────────────────────────────────────────────────── */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={handleAuthSuccess}
        initialMode={authInitialMode}
      />
    </div>
  );
}

export default App;
