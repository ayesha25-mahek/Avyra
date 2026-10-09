import React from 'react';
import { ConfidentialIndustrialWorkspace } from '@/components/ConfidentialIndustrialWorkspace';

export const SovereigntyAuditView: React.FC = () => {
  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-5xl mx-auto">
      {/* Page Heading */}
      <div className="pb-4 border-b border-[#1A402D]">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#143324] border border-[#23573E] text-[#00E599]">
            MODULE 10
          </span>
          <span className="text-xs text-[#74C69D] font-mono">Air-Gap Verification Center</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Sovereignty Monitor &amp; Real-Time Audit Trail
        </h1>
        <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
          Cryptographic evidence, zero external network call guarantees, and timestamped local audit logs certifying zero data leakage for PSU &amp; refinery compliance.
        </p>
      </div>

      {/* Embedded Confidential Industrial Workspace */}
      <div className="space-y-6">
        <ConfidentialIndustrialWorkspace />
      </div>
    </div>
  );
};
