import React, { useState } from 'react';
import {
  ShieldCheck,
  Sparkles,
  Download,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Table,
} from 'lucide-react';
import { auditSpreadsheetData, applySpreadsheetCorrections, downloadFile } from '@/lib/api';

type Stage = 'upload' | 'audit' | 'cleaned';

export const SafeSpreadsheetCleaner: React.FC = () => {
  const [stage, setStage] = useState<Stage>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [isAuditing, setIsAuditing] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Audit state
  const [auditResult, setAuditResult] = useState<any | null>(null);
  const [rawHeaders, setRawHeaders] = useState<string[]>([]);
  const [rawRows, setRawRows] = useState<any[][]>([]);
  const [selectedCorrectionIds, setSelectedCorrectionIds] = useState<string[]>([]);
  const [previewTab, setPreviewTab] = useState<'corrections' | 'before_after'>('corrections');

  // Cleaned state
  const [cleanedResult, setCleanedResult] = useState<any | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleAudit = async () => {
    if (!file) {
      setError('Please select a spreadsheet or CSV dataset.');
      return;
    }

    setIsAuditing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const resp = await auditSpreadsheetData(formData);
      if (resp.status === 'success' && resp.audit) {
        setAuditResult(resp.audit);
        setRawHeaders(resp.raw_headers || []);
        setRawRows(resp.raw_rows || []);
        // Pre-select all proposed corrections by default
        const allIds = (resp.audit.proposed_corrections || []).map((c: any) => c.id);
        setSelectedCorrectionIds(allIds);
        setStage('audit');
      } else {
        setError('Failed to audit spreadsheet.');
      }
    } catch (err: any) {
      setError(err.message || 'Error communicating with spreadsheet audit service.');
    } finally {
      setIsAuditing(false);
    }
  };

  const toggleCorrection = (id: string) => {
    setSelectedCorrectionIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleAllCorrections = () => {
    if (!auditResult) return;
    const allIds = (auditResult.proposed_corrections || []).map((c: any) => c.id);
    if (selectedCorrectionIds.length === allIds.length) {
      setSelectedCorrectionIds([]);
    } else {
      setSelectedCorrectionIds(allIds);
    }
  };

  const handleApply = async () => {
    if (!auditResult) return;

    setIsApplying(true);
    setError(null);

    const payload = {
      headers: rawHeaders,
      original_rows: rawRows,
      approved_correction_ids: selectedCorrectionIds,
      all_proposed_corrections: auditResult.proposed_corrections || [],
      source_filename: file?.name || 'dataset.csv',
    };

    try {
      const resp = await applySpreadsheetCorrections(payload);
      if (resp.status === 'success') {
        setCleanedResult(resp);
        setStage('cleaned');
      } else {
        setError('Failed to apply corrections.');
      }
    } catch (err: any) {
      setError(err.message || 'Error compiling cleaned workbook.');
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex items-center justify-between p-4 rounded-xl bg-[#091A11] border border-[#1A402D]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center text-[#00E599]">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">Safe Spreadsheet Data Cleaner</h2>
            <p className="text-xs text-[#74C69D] font-mono">
              Audit anomalies, formula glitches, duplicates, and outliers with non-destructive preservation of raw files.
            </p>
          </div>
        </div>

        {/* Stepper indicator */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span
            className={`px-2.5 py-1 rounded-md border ${
              stage === 'upload'
                ? 'bg-[#00E599]/20 text-[#00E599] border-[#00E599]/40 font-bold'
                : 'bg-[#0E2419] text-[#74C69D] border-[#1A402D]'
            }`}
          >
            1. Upload
          </span>
          <span className="text-[#23573E]">→</span>
          <span
            className={`px-2.5 py-1 rounded-md border ${
              stage === 'audit'
                ? 'bg-[#00E599]/20 text-[#00E599] border-[#00E599]/40 font-bold'
                : 'bg-[#0E2419] text-[#74C69D] border-[#1A402D]'
            }`}
          >
            2. Audit &amp; Approve Fixes
          </span>
          <span className="text-[#23573E]">→</span>
          <span
            className={`px-2.5 py-1 rounded-md border ${
              stage === 'cleaned'
                ? 'bg-[#00E599]/20 text-[#00E599] border-[#00E599]/40 font-bold'
                : 'bg-[#0E2419] text-[#74C69D] border-[#1A402D]'
            }`}
          >
            3. Download Cleaned XLSX
          </span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-start gap-3 font-mono">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* STAGE 1: UPLOAD */}
      {stage === 'upload' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-5 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
            <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider font-mono">
              Upload Operational Spreadsheet (CSV or XLSX)
            </label>
            <div className="border border-dashed border-[#1E4D36] hover:border-[#00E599]/60 rounded-xl p-8 text-center bg-[#091A11] transition-colors relative">
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileChange}
                disabled={isAuditing}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
              />
              <div className="w-12 h-12 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center mx-auto mb-3 text-[#00E599]">
                <Table className="w-6 h-6" />
              </div>
              {file ? (
                <div>
                  <p className="text-xs font-bold text-[#00E599]">{file.name}</p>
                  <p className="text-[10px] text-[#74C69D] font-mono mt-1">
                    {(file.size / 1024).toFixed(1)} KB • Ready for automated data hygiene audit
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-xs font-semibold text-white">Click or drag CSV or XLSX file</p>
                  <p className="text-[11px] text-[#74C69D] mt-1 font-mono">
                    Plant operations log, equipment failure data, lab sensor readings
                  </p>
                </div>
              )}
            </div>

            <button
              onClick={handleAudit}
              disabled={isAuditing || !file}
              className="w-full py-3 px-4 bg-[#00E599] hover:bg-[#00c885] disabled:bg-[#143324] disabled:text-gray-500 text-black font-bold rounded-lg text-xs uppercase tracking-wider transition-colors flex items-center justify-center gap-2 font-mono"
            >
              {isAuditing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running Statistical &amp; Structural Audit…
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Run Data Quality Audit
                </>
              )}
            </button>
          </div>

          {/* Safety Principles Card */}
          <div className="p-5 rounded-xl bg-[#091A11] border border-[#1A402D] space-y-4">
            <h3 className="text-xs font-bold text-[#00E599] font-mono uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4" />
              Non-Destructive Industrial Safety Rules
            </h3>
            <ul className="space-y-3 text-xs text-[#B8D5C6]">
              <li className="flex items-start gap-2">
                <span className="text-[#00E599] mt-0.5">•</span>
                <span>
                  <strong>Raw File Preservation:</strong> The original uploaded spreadsheet is never overwritten or altered. It is preserved in an immutable archive.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00E599] mt-0.5">•</span>
                <span>
                  <strong>Engineer Approval Checkpoints:</strong> Every correction (duplicate removal, missing value imputation, formula syntax fix) requires explicit opt-in confirmation.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00E599] mt-0.5">•</span>
                <span>
                  <strong>Statistical Outlier Isolation:</strong> Values exceeding 3-sigma thresholds are highlighted without silent deletion or loss of operational context.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00E599] mt-0.5">•</span>
                <span>
                  <strong>Audit Trail Delivery:</strong> The generated workbook includes a dedicated audit sheet recording every modification made with exact timestamps.
                </span>
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* STAGE 2: AUDIT RESULTS & CORRECTION APPROVAL */}
      {stage === 'audit' && auditResult && (
        <div className="space-y-6">
          {/* Top KPI row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 rounded-lg bg-[#0E2419] border border-[#1A402D]">
              <span className="text-[10px] text-[#74C69D] font-mono uppercase block">Total Rows</span>
              <span className="text-base font-bold text-white font-mono">{auditResult.total_rows}</span>
            </div>
            <div className="p-3 rounded-lg bg-[#0E2419] border border-[#1A402D]">
              <span className="text-[10px] text-[#74C69D] font-mono uppercase block">Total Columns</span>
              <span className="text-base font-bold text-white font-mono">{auditResult.total_columns}</span>
            </div>
            <div className="p-3 rounded-lg bg-[#0E2419] border border-[#1A402D]">
              <span className="text-[10px] text-amber-400 font-mono uppercase block">Duplicates</span>
              <span className="text-base font-bold text-amber-300 font-mono">
                {auditResult.duplicate_rows?.count || 0}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-[#0E2419] border border-[#1A402D]">
              <span className="text-[10px] text-amber-400 font-mono uppercase block">Missing Cells</span>
              <span className="text-base font-bold text-amber-300 font-mono">
                {auditResult.missing_values?.total_missing || 0}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-[#0E2419] border border-[#1A402D]">
              <span className="text-[10px] text-red-400 font-mono uppercase block">Formula Errors</span>
              <span className="text-base font-bold text-red-300 font-mono">
                {auditResult.formula_errors?.total_errors || 0}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-[#0E2419] border border-[#1A402D]">
              <span className="text-[10px] text-[#00E599] font-mono uppercase block">Proposed Fixes</span>
              <span className="text-base font-bold text-[#00E599] font-mono">
                {auditResult.proposed_corrections?.length || 0}
              </span>
            </div>
          </div>

          {/* Subtabs for Corrections vs Before/After preview */}
          <div className="flex items-center justify-between border-b border-[#1A402D] pb-3">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPreviewTab('corrections')}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors border ${
                  previewTab === 'corrections'
                    ? 'bg-[#143324] text-[#00E599] border-[#23573E] font-bold'
                    : 'bg-[#091A11] text-[#9DC4B0] border-[#1A402D] hover:bg-[#0E2419]'
                }`}
              >
                Proposed Corrections ({selectedCorrectionIds.length} approved)
              </button>
              <button
                onClick={() => setPreviewTab('before_after')}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors border ${
                  previewTab === 'before_after'
                    ? 'bg-[#143324] text-[#00E599] border-[#23573E] font-bold'
                    : 'bg-[#091A11] text-[#9DC4B0] border-[#1A402D] hover:bg-[#0E2419]'
                }`}
              >
                Before vs After Preview ({auditResult.before_after_previews?.length || 0} samples)
              </button>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setStage('upload')}
                className="px-3 py-1.5 rounded-lg border border-[#1E4D36] text-xs font-mono text-[#9DC4B0] hover:bg-[#143324]"
              >
                ← Back
              </button>
              <button
                onClick={handleApply}
                disabled={isApplying || selectedCorrectionIds.length === 0}
                className="px-4 py-1.5 bg-[#00E599] hover:bg-[#00c885] disabled:bg-[#143324] text-black font-bold rounded-lg text-xs font-mono flex items-center gap-2"
              >
                {isApplying ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Compiling Cleaned XLSX…
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    Apply {selectedCorrectionIds.length} Approved Corrections
                  </>
                )}
              </button>
            </div>
          </div>

          {/* TAB 1: PROPOSED CORRECTIONS */}
          {previewTab === 'corrections' && (
            <div className="p-4 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-[#1A402D]">
                <span className="text-xs font-bold text-white font-mono uppercase">
                  Select Corrections to Apply
                </span>
                <button
                  onClick={toggleAllCorrections}
                  className="text-xs text-[#00E599] hover:underline font-mono"
                >
                  {selectedCorrectionIds.length === (auditResult.proposed_corrections?.length || 0)
                    ? 'Deselect All'
                    : 'Select All'}
                </button>
              </div>

              {auditResult.proposed_corrections && auditResult.proposed_corrections.length > 0 ? (
                <div className="space-y-2.5">
                  {auditResult.proposed_corrections.map((corr: any) => {
                    const isChecked = selectedCorrectionIds.includes(corr.id);
                    return (
                      <div
                        key={corr.id}
                        onClick={() => toggleCorrection(corr.id)}
                        className={`p-3.5 rounded-lg border cursor-pointer transition-colors flex items-start gap-3 ${
                          isChecked
                            ? 'bg-[#143324]/60 border-[#23573E]'
                            : 'bg-[#091A11] border-[#1A402D] opacity-75'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleCorrection(corr.id)}
                          className="mt-0.5 rounded border-[#1E4D36] text-[#00E599] focus:ring-0 bg-[#07170E]"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#091A11] text-[#00E599] border border-[#1E4D36] uppercase">
                              {corr.type}
                            </span>
                            <span className="text-xs font-bold text-white font-mono truncate">
                              {corr.title}
                            </span>
                          </div>
                          <p className="text-xs text-[#9DC4B0]">{corr.detail}</p>
                          <p className="text-[11px] text-[#74C69D] font-mono mt-1">
                            Action: {corr.action}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-6 text-center text-[#74C69D] font-mono text-xs">
                  Zero critical anomalies detected! Dataset is already clean and within standard operating thresholds.
                </div>
              )}
            </div>
          )}

          {/* TAB 2: BEFORE / AFTER PREVIEW */}
          {previewTab === 'before_after' && (
            <div className="p-4 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
              <span className="text-xs font-bold text-white font-mono uppercase block pb-2 border-b border-[#1A402D]">
                Data Correction Preview Samples
              </span>

              {auditResult.before_after_previews && auditResult.before_after_previews.length > 0 ? (
                <div className="overflow-x-auto border border-[#1A402D] rounded-lg">
                  <table className="w-full text-xs font-mono text-left">
                    <thead className="bg-[#091A11] text-[#00E599] border-b border-[#1A402D]">
                      <tr>
                        <th className="py-2.5 px-3">Field / Column</th>
                        <th className="py-2.5 px-3 text-amber-300">Original (Raw Input)</th>
                        <th className="py-2.5 px-3 text-[#00E599]">Proposed Cleaned Value</th>
                        <th className="py-2.5 px-3">Reason / Rationale</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#143324]">
                      {auditResult.before_after_previews.map((item: any, idx: number) => (
                        <tr key={idx} className="hover:bg-[#143324]/40">
                          <td className="py-2 px-3 font-bold text-white">{item.field}</td>
                          <td className="py-2 px-3 text-red-300 bg-red-950/20">{String(item.before)}</td>
                          <td className="py-2 px-3 text-[#00E599] bg-[#00E599]/10 font-bold">
                            {String(item.after)}
                          </td>
                          <td className="py-2 px-3 text-[#9DC4B0]">{item.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-xs text-[#74C69D] font-mono">No row preview alterations available.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* STAGE 3: CLEANED RESULT */}
      {stage === 'cleaned' && cleanedResult && (
        <div className="p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#1A402D]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center text-[#00E599]">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white font-mono">
                  Cleaned Dataset Successfully Generated
                </h3>
                <p className="text-xs text-[#74C69D] font-mono">
                  All approved corrections applied. Original file preserved untouched in raw storage.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {cleanedResult.raw_preserved_url && (
                <button
                  onClick={() =>
                    downloadFile(cleanedResult.raw_preserved_url, cleanedResult.raw_preserved_filename)
                  }
                  className="px-3.5 py-2 rounded-lg border border-[#1E4D36] text-xs font-mono text-[#9DC4B0] hover:bg-[#143324] flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Raw Source Copy
                </button>
              )}
              <button
                onClick={() => downloadFile(cleanedResult.download_url, cleanedResult.cleaned_filename)}
                className="px-5 py-2.5 bg-[#00E599] hover:bg-[#00c885] text-black font-bold rounded-lg text-xs font-mono uppercase tracking-wider flex items-center gap-2 shadow-lg shadow-[#00E599]/10"
              >
                <Download className="w-4 h-4" />
                Download Cleaned XLSX
              </button>
            </div>
          </div>

          {/* Metric cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-[#091A11] border border-[#1A402D]">
              <span className="text-[10px] text-[#74C69D] font-mono uppercase block">Corrections Applied</span>
              <span className="text-lg font-bold text-[#00E599] font-mono">
                {cleanedResult.corrections_applied_count} Fixes
              </span>
            </div>
            <div className="p-4 rounded-lg bg-[#091A11] border border-[#1A402D]">
              <span className="text-[10px] text-[#74C69D] font-mono uppercase block">Clean Rows</span>
              <span className="text-lg font-bold text-white font-mono">
                {cleanedResult.remaining_rows} Rows
              </span>
            </div>
            <div className="p-4 rounded-lg bg-[#091A11] border border-[#1A402D]">
              <span className="text-[10px] text-[#74C69D] font-mono uppercase block">Raw Original Status</span>
              <span className="text-lg font-bold text-white font-mono">Preserved Intact</span>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-4 border-t border-[#1A402D]">
            <button
              onClick={() => {
                setFile(null);
                setStage('upload');
              }}
              className="px-4 py-2 rounded-lg border border-[#1E4D36] text-xs font-mono text-[#74C69D] hover:bg-[#143324]"
            >
              Clean Another Dataset
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
