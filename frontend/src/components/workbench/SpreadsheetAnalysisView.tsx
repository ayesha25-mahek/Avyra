import React, { useState } from 'react';
import {
  Table,
  Zap,
  RotateCcw,
  Download,
  Copy,
  Check,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet,
  BarChart2,
  AlertTriangle,
  Layout,
  Send,
  Sparkles,
} from 'lucide-react';
import { generateContent, downloadFile } from '@/lib/api';
import type { ProgressEvent, ResultEvent, OutputFormat } from '@/types';

interface OutputOption {
  id: OutputFormat;
  label: string;
  badge: string;
  desc: string;
  icon: React.ElementType;
}

const SPREADSHEET_OUTPUT_OPTIONS: OutputOption[] = [
  {
    id: 'data_summary',
    label: 'Data Summary',
    badge: 'Overview',
    desc: 'Summary statistics, row counts & column distributions',
    icon: BarChart2,
  },
  {
    id: 'abnormal_values',
    label: 'Calculations & Abnormal Values',
    badge: 'Thresholds',
    desc: 'Statutory PSU operating threshold deviations & outliers',
    icon: AlertTriangle,
  },
  {
    id: 'analysis_workbook',
    label: 'Analysis Workbook (XLSX)',
    badge: 'XLSX Deliverable',
    desc: 'Formatted multi-sheet Excel workbook with calculations',
    icon: FileSpreadsheet,
  },
  {
    id: 'infographic',
    label: 'Chart / Infographic Spec',
    badge: 'Optional Layout',
    desc: 'Visual chart layouts and KPI summary specification',
    icon: Layout,
  },
];

import { DocumentToExcelGenerator } from './DocumentToExcelGenerator';
import { SafeSpreadsheetCleaner } from './SafeSpreadsheetCleaner';

type SpreadsheetSubTab = 'analysis' | 'doc_to_excel' | 'safe_cleanup';

interface SpreadsheetAnalysisViewProps {
  initialSubTab?: SpreadsheetSubTab;
}

export const SpreadsheetAnalysisView: React.FC<SpreadsheetAnalysisViewProps> = ({ initialSubTab = 'analysis' }) => {
  const [subTab, setSubTab] = useState<SpreadsheetSubTab>(initialSubTab);

  React.useEffect(() => {
    if (initialSubTab) {
      setSubTab(initialSubTab);
    }
  }, [initialSubTab]);

  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState(
    'Analyze this operational dataset / tabular spreadsheet. Calculate summary statistics, identify outliers exceeding statutory PSU operating thresholds, flag recurring equipment failures, and prescribe maintenance recommendations.'
  );
  const [selectedOutputs, setSelectedOutputs] = useState<OutputFormat[]>([
    'data_summary',
    'abnormal_values',
    'analysis_workbook',
  ]);

  const [isProcessing, setIsProcessing] = useState(false);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);
  const [progressPct, setProgressPct] = useState(0);
  const [results, setResults] = useState<Partial<Record<OutputFormat, ResultEvent>>>({});
  const [activeOutputTab, setActiveOutputTab] = useState<OutputFormat>('data_summary');
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showTechDetails, setShowTechDetails] = useState(false);

  // Revision state
  const [revisionPrompts, setRevisionPrompts] = useState<Partial<Record<OutputFormat, string>>>({});
  const [revisingType, setRevisingType] = useState<OutputFormat | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResults({});
      setError(null);
    }
  };

  const toggleOutput = (id: OutputFormat) => {
    setSelectedOutputs((prev) =>
      prev.includes(id) ? prev.filter((o) => o !== id) : [...prev, id]
    );
  };

  const handleExecute = async () => {
    if (!file && !prompt.trim()) return;
    if (selectedOutputs.length === 0) return;

    setIsProcessing(true);
    setProgressMsg('Ingesting tabular dataset & computing statistical thresholds…');
    setProgressPct(15);
    setResults({});
    setError(null);

    const formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('outputs', JSON.stringify(selectedOutputs));
    formData.append('provider', 'ollama');
    if (file) formData.append('files', file);

    try {
      await generateContent(formData, {
        onProgress: (p: ProgressEvent) => {
          setProgressMsg(p.message);
          setProgressPct(p.percent);
        },
        onResult: (r: ResultEvent) => {
          setResults((prev) => ({ ...prev, [r.output_type]: r }));
          setActiveOutputTab(r.output_type);
        },
        onDone: () => {
          setIsProcessing(false);
          setProgressPct(100);
        },
        onError: (err: string) => {
          setError(err);
          setIsProcessing(false);
        },
      });
    } catch (err: any) {
      setError(err?.message || 'Spreadsheet analysis failed');
      setIsProcessing(false);
    }
  };

  const handleRevise = async (outputType: OutputFormat) => {
    const revPrompt = revisionPrompts[outputType]?.trim();
    if (!file || !revPrompt) return;

    setRevisingType(outputType);
    setError(null);

    const formData = new FormData();
    const contextualPrompt = `[Follow-up Revision for ${outputType.toUpperCase()}]
Original Analysis Directive:
${prompt}

User Revision Instructions:
${revPrompt}`;

    formData.append('prompt', contextualPrompt);
    formData.append('outputs', JSON.stringify([outputType]));
    formData.append('provider', 'ollama');
    formData.append('files', file);

    try {
      await generateContent(formData, {
        onResult: (r: ResultEvent) => {
          setResults((prev) => ({ ...prev, [outputType]: r }));
        },
        onDone: () => {
          setRevisingType(null);
          setRevisionPrompts((prev) => ({ ...prev, [outputType]: '' }));
        },
        onError: (err: string) => {
          setError(`Revision failed: ${err}`);
          setRevisingType(null);
        },
      });
    } catch (err: any) {
      setError(`Revision failed: ${err?.message}`);
      setRevisingType(null);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResults({});
    setError(null);
    setProgressMsg(null);
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const currentResult = results[activeOutputTab];
  const content = currentResult?.content || '';
  const techSplit = content.split('## Technical & Sovereignty Evidence');
  const mainReportText = techSplit[0]?.trim() || content;
  const technicalEvidenceText = techSplit.length > 1 ? techSplit[1]?.trim() : '';

  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-5xl mx-auto">
      {/* Page Heading */}
      <div className="pb-4 border-b border-[#1A402D]">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#143324] border border-[#23573E] text-[#00E599]">
            MODULE 08
          </span>
          <span className="text-xs text-[#74C69D] font-mono">Tabular Anomaly &amp; Generation Engine</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Operational Dataset &amp; Spreadsheet Analysis
        </h1>
        <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
          Ingest operational logs, extract multi-sheet workbooks from documents, or run non-destructive spreadsheet data hygiene audits.
        </p>

        {/* Feature Sub-Navigation Tabs */}
        <div className="flex items-center gap-2 mt-4 pt-3 border-t border-[#1A402D]/60">
          <button
            onClick={() => setSubTab('analysis')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors border ${
              subTab === 'analysis'
                ? 'bg-[#143324] text-[#00E599] border-[#23573E] font-bold'
                : 'bg-[#091A11] text-[#9DC4B0] border-[#1A402D] hover:bg-[#0E2419]'
            }`}
          >
            Spreadsheet Analysis &amp; Outliers
          </button>
          <button
            onClick={() => setSubTab('doc_to_excel')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors border ${
              subTab === 'doc_to_excel'
                ? 'bg-[#143324] text-[#00E599] border-[#23573E] font-bold'
                : 'bg-[#091A11] text-[#9DC4B0] border-[#1A402D] hover:bg-[#0E2419]'
            }`}
          >
            Document-to-Excel Generator
          </button>
          <button
            onClick={() => setSubTab('safe_cleanup')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors border ${
              subTab === 'safe_cleanup'
                ? 'bg-[#143324] text-[#00E599] border-[#23573E] font-bold'
                : 'bg-[#091A11] text-[#9DC4B0] border-[#1A402D] hover:bg-[#0E2419]'
            }`}
          >
            Safe Data Cleanup &amp; Correction
          </button>
        </div>
      </div>

      {subTab === 'doc_to_excel' && <DocumentToExcelGenerator />}

      {subTab === 'safe_cleanup' && <SafeSpreadsheetCleaner />}

      {subTab === 'analysis' && (
        <>
          {/* Input Section */}
          <div className="p-5 sm:p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
            {/* Upload Zone */}
            <div>
              <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
                1. Operational Spreadsheet / Dataset (CSV, XLSX, TXT)
              </label>
          <div className="border border-dashed border-[#1E4D36] hover:border-[#00E599]/60 rounded-xl p-5 text-center bg-[#091A11] transition-colors relative">
            <input
              type="file"
              accept=".csv,.xlsx,.xls,.txt"
              onChange={handleFileChange}
              disabled={isProcessing}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />
            <div className="w-10 h-10 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center mx-auto mb-2 text-[#00E599]">
              <Table className="w-4 h-4" />
            </div>
            {file ? (
              <div className="space-y-0.5">
                <p className="text-sm font-bold text-[#00E599]">{file.name}</p>
                <p className="text-xs text-[#74C69D] font-mono">
                  {(file.size / 1024).toFixed(1)} KB • {file.type || 'spreadsheet'}
                </p>
              </div>
            ) : (
              <>
                <p className="text-sm font-semibold text-white">Select operational spreadsheet</p>
                <p className="text-xs text-[#74C69D] mt-1 font-mono">Upload pump vibration logs, sensor timeseries, or maintenance history</p>
              </>
            )}
          </div>
        </div>

        {/* Output Selector */}
        <div>
          <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono flex items-center justify-between">
            <span>2. Select Deliverable Formats</span>
            <span className="text-[10px] text-[#74C69D] lowercase">({selectedOutputs.length} selected)</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {SPREADSHEET_OUTPUT_OPTIONS.map((opt) => {
              const Icon = opt.icon;
              const isSel = selectedOutputs.includes(opt.id);
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => toggleOutput(opt.id)}
                  disabled={isProcessing}
                  className={`p-2.5 rounded-lg border text-left flex items-start gap-2.5 transition-colors ${
                    isSel
                      ? 'bg-[#183D2B] border-[#00E599] text-white shadow-sm'
                      : 'bg-[#091A11] border-[#1E4D36] text-[#B8D5C6] hover:bg-[#102B1E]'
                  }`}
                >
                  <div className={`w-4 h-4 rounded border flex items-center justify-center mt-0.5 shrink-0 ${
                    isSel ? 'bg-[#00E599] border-[#00E599] text-black' : 'border-[#2D6E4E]'
                  }`}>
                    {isSel && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                  <div className="min-w-0">
                    <div className="text-[11px] font-bold leading-tight truncate flex items-center gap-1">
                      <Icon className="w-3 h-3 text-[#00E599] shrink-0" />
                      <span className="truncate">{opt.label}</span>
                    </div>
                    <div className="text-[9px] text-[#74C69D] font-mono leading-tight truncate">{opt.badge}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Task Prompt */}
        <div>
          <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
            3. Threshold Directives &amp; Statistical Scope
          </label>
          <textarea
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isProcessing}
            className="w-full rounded-xl bg-[#08170F] border border-[#1E4D36] p-3 text-xs sm:text-sm text-gray-200 focus:outline-none focus:border-[#00E599] transition-colors font-serif leading-relaxed"
          />
        </div>

        {/* Execution Bar */}
        <div className="flex items-center gap-3 pt-2">
          {file && !isProcessing && (
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2.5 rounded-xl bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-xs font-medium text-[#B8D5C6] flex items-center gap-2"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset
            </button>
          )}

          <button
            type="button"
            onClick={handleExecute}
            disabled={isProcessing || (!file && !prompt.trim()) || selectedOutputs.length === 0}
            className="flex-1 py-3 px-5 rounded-xl bg-[#00E599] hover:bg-[#00C070] text-black font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-black" />
                <span>Computing Thresholds &amp; Outliers ({progressPct}%)…</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-black" />
                <span>Execute Spreadsheet Analysis ({selectedOutputs.length})</span>
              </>
            )}
          </button>
        </div>

        {isProcessing && (
          <div className="space-y-1.5 pt-2">
            <div className="flex justify-between text-xs font-mono text-[#74C69D]">
              <span>{progressMsg || 'Analyzing dataset…'}</span>
              <span>{progressPct}%</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-[#08170F] overflow-hidden">
              <div
                className="h-full bg-[#00E599] transition-all duration-300"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-lg bg-red-950/60 border border-red-800 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Results Workspace: Multi-Output Tabs + Follow-up Revision */}
      {Object.keys(results).length > 0 && (
        <div className="p-5 sm:p-6 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1A402D]">
            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-thin">
              {Object.keys(results).map((fmtKey) => {
                const fmt = fmtKey as OutputFormat;
                const opt = SPREADSHEET_OUTPUT_OPTIONS.find((o) => o.id === fmt);
                const isActive = activeOutputTab === fmt;
                return (
                  <button
                    key={fmt}
                    type="button"
                    onClick={() => setActiveOutputTab(fmt)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors flex items-center gap-1.5 ${
                      isActive
                        ? 'bg-[#183D2B] border border-[#00E599] text-white font-bold'
                        : 'bg-[#0E2419] border border-[#1E4D36] text-[#B8D5C6] hover:bg-[#143324]'
                    }`}
                  >
                    <span>{opt?.label || fmt}</span>
                  </button>
                );
              })}
            </div>

            <div className="flex items-center gap-2">
              {currentResult?.content && (
                <button
                  type="button"
                  onClick={() => handleCopy(mainReportText)}
                  className="px-3.5 py-1.5 rounded-full bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-xs font-mono text-[#B8D5C6] hover:text-white flex items-center gap-1.5 transition-all active:scale-[0.98]"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-[#52B788]" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              )}

              {currentResult?.download_url && (
                <button
                  type="button"
                  onClick={() => downloadFile(currentResult.download_url!, currentResult.filename)}
                  className="px-4 py-1.5 rounded-full bg-[#52B788] hover:bg-[#74C69D] text-[#07130D] text-xs font-bold font-mono flex items-center gap-1.5 transition-all active:scale-[0.98] shadow-sm hover:shadow-[0_0_12px_rgba(82,183,136,0.35)]"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download {currentResult.filename?.split('.').pop()?.toUpperCase() || 'Workbook'}</span>
                </button>
              )}
            </div>
          </div>

          {/* Formatted Output Content / Vector SVG Preview */}
          {currentResult?.svg_content ? (
            <div className="space-y-3">
              <div
                className="w-full rounded-xl bg-[#020704] border border-[#163826] p-2 overflow-x-auto shadow-2xl flex items-center justify-center min-h-[500px]"
                dangerouslySetInnerHTML={{ __html: currentResult.svg_content }}
              />
              <div className="p-3 rounded-lg bg-[#06120B] border border-[#163827] text-xs font-mono text-[#74C69D] flex items-center justify-between">
                <span>Vector SVG Deliverable: 100% Client Scalable</span>
                {currentResult.download_url && (
                  <button
                    type="button"
                    onClick={() => downloadFile(currentResult.download_url!, currentResult.filename)}
                    className="text-[#00E599] hover:underline flex items-center gap-1 font-bold"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download SVG</span>
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-[#06120B] border border-[#163827] text-xs sm:text-sm text-gray-200 leading-relaxed font-sans whitespace-pre-wrap max-h-[600px] overflow-y-auto scrollbar-thin">
              {mainReportText}
            </div>
          )}

          {/* Follow-up Revision Box */}
          <div className="p-4 rounded-xl bg-[#08170F] border border-[#1E4D36] space-y-2.5">
            <label className="block text-xs font-semibold text-[#74C69D] uppercase tracking-wider font-mono flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#00E599]" />
              Follow-up Revision for {SPREADSHEET_OUTPUT_OPTIONS.find((o) => o.id === activeOutputTab)?.label || activeOutputTab}
            </label>
            <div className="flex flex-col sm:flex-row items-center gap-2">
              <input
                type="text"
                placeholder="e.g. Tighten vibration velocity threshold to 4.0 mm/s, add MTBF projection, or recompute motor load ratio…"
                value={revisionPrompts[activeOutputTab] || ''}
                onChange={(e) =>
                  setRevisionPrompts((prev) => ({ ...prev, [activeOutputTab]: e.target.value }))
                }
                disabled={revisingType === activeOutputTab}
                className="flex-1 w-full rounded-lg bg-[#050F09] border border-[#1E4D36] px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-[#00E599] font-serif"
              />
              <button
                type="button"
                onClick={() => handleRevise(activeOutputTab)}
                disabled={
                  revisingType === activeOutputTab ||
                  !revisionPrompts[activeOutputTab]?.trim()
                }
                className="w-full sm:w-auto px-4 py-2 rounded-lg bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-white text-xs font-mono font-bold flex items-center justify-center gap-1.5 disabled:opacity-40 transition-colors"
              >
                {revisingType === activeOutputTab ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-[#00E599]" />
                    <span>Revising…</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5 text-[#00E599]" />
                    <span>Apply Revision</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-[10px] text-[#587E6B] font-mono">
              Revises this specific deliverable without rerunning the entire pipeline or losing other outputs.
            </p>
          </div>

          {technicalEvidenceText && (
            <div className="border border-[#183B28] rounded-lg overflow-hidden bg-[#07170E]">
              <button
                type="button"
                onClick={() => setShowTechDetails(!showTechDetails)}
                className="w-full p-3 flex items-center justify-between text-xs text-[#74C69D] hover:text-white font-mono"
              >
                <span>Technical &amp; Sovereignty Audit Trail</span>
                {showTechDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
              {showTechDetails && (
                <div className="p-3 border-t border-[#183B28] text-xs font-mono text-[#9DC4B0] whitespace-pre-wrap bg-[#050F09]">
                  {technicalEvidenceText}
                </div>
              )}
            </div>
          )}
        </div>
      )}
        </>
      )}
    </div>
  );
};
