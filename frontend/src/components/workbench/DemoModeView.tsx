import React from 'react';
import { ArrowLeft, Trophy } from 'lucide-react';
import { SihDemoCenter } from '@/components/SihDemoCenter';
import type { WorkbenchTab } from '@/components/IndustrialSidebar';

interface DemoModeViewProps {
  onBack: (tab: WorkbenchTab) => void;
}

export const DemoModeView: React.FC<DemoModeViewProps> = ({ onBack }) => {
  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-5xl mx-auto">
      {/* Page Heading */}
      <div className="pb-4 border-b border-[#1A402D] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#00E599]/20 border border-[#00E599]/40 text-[#00E599] flex items-center gap-1">
              <Trophy className="w-3 h-3 text-[#00E599]" /> SIH PROBLEM STATEMENT 26117
            </span>
            <span className="text-xs text-[#74C69D] font-mono">Guided Evaluation Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            SIH Demo Mode &amp; Evidence Center
          </h1>
          <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
            One-click interactive demonstration of all 4 benchmark flows with real-time provenance, telemetry, and deliverable validation.
          </p>
        </div>

        <button
          type="button"
          onClick={() => onBack('dashboard')}
          className="px-3.5 py-2 rounded-xl bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-xs font-mono text-[#B8D5C6] hover:text-white flex items-center gap-2 transition-colors self-start sm:self-auto"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Dashboard</span>
        </button>
      </div>

      {/* Render SIH Demo Center */}
      <div className="space-y-6">
        <SihDemoCenter />
      </div>
    </div>
  );
};
