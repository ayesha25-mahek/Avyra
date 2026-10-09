import React, { useState } from 'react';
import {
  ClipboardCheck,
  Upload,
  Zap,
  RotateCcw,
  Download,
  Copy,
  Check,
  AlertCircle,
  Presentation,
  FileText,
  BarChart2,
  Loader2,
} from 'lucide-react';
import { generateContent, downloadFile } from '@/lib/api';
import type { ProgressEvent, ResultEvent, OutputFormat } from '@/types';

export const InspectionReportsView: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [prompt, setPrompt] = useState(
    'Synthesize this field inspection evidence into an official statutory inspection report. Evaluate observed wear against safety standards, assign risk severity ratings, prescribe mandatory mitigating controls, and format for executive engineering sign-off.'
  );
  const [selectedOutputs, setSelectedOutputs] = useState<OutputFormat[]>([
    'inspection_analysis',
    'presentation',
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);
  const [progressPct, setProgressPct] = useState(0);
  const [results, setResults] = useState<Partial<Record<OutputFormat, ResultEvent>>>({});
  const [error, setError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const toggleOutput = (fmt: OutputFormat) => {
    setSelectedOutputs((prev) =>
      prev.includes(fmt) ? prev.filter((f) => f !== fmt) : [...prev, fmt]
    );
  };

  const handleExecute = async () => {
    if (files.length === 0 && !prompt.trim()) return;
    if (selectedOutputs.length === 0) return;

    setIsProcessing(true);
    setProgressMsg('Initiating statutory report synthesis pipeline…');
    setProgressPct(10);
    setResults({});
    setError(null);

    const formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('outputs', JSON.stringify(selectedOutputs));
    formData.append('provider', 'ollama');
    files.forEach((f) => formData.append('files', f));

    try {
      await generateContent(formData, {
        onProgress: (p: ProgressEvent) => {
          setProgressMsg(p.message);
          setProgressPct(p.percent);
        },
        onResult: (r: ResultEvent) => {
          setResults((prev) => ({ ...prev, [r.output_type]: r }));
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
      setError(err?.message || 'Inspection report synthesis failed');
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setFiles([]);
    setResults({});
    setError(null);
    setProgressMsg(null);
  };

  const handleCopy = async (key: string, text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-5xl mx-auto">
      {/* Page Heading */}
      <div className="pb-4 border-b border-[#1A402D]">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#143324] border border-[#23573E] text-[#00E599]">
            MODULE 05
          </span>
          <span className="text-xs text-[#74C69D] font-mono">Statutory &amp; Safety Compliance</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Statutory Inspection Reports &amp; Presentations
        </h1>
        <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
          Generate formal engineering deliverables, compliance audit reports, and slide decks from field logs and physical inspection data.
        </p>
      </div>

      {/* Input Section */}
      <div className="p-5 sm:p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
        {/* Upload Zone */}
        <div>
          <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
            1. Field Inspection Records &amp; Logs
          </label>
          <div className="border border-dashed border-[#1E4D36] hover:border-[#00E599]/60 rounded-xl p-5 text-center bg-[#091A11] transition-colors relative">
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.doc,.txt,.csv,.png,.jpg"
              onChange={handleFileChange}
              disabled={isProcessing}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />
            <div className="w-10 h-10 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center mx-auto mb-2 text-[#00E599]">
              <Upload className="w-4 h-4" />
            </div>
            {files.length === 0 ? (
              <>
                <p className="text-sm font-semibold text-white">Click or drag field logs &amp; records</p>
                <p className="text-xs text-[#74C69D] mt-1 font-mono">Upload sensor sheets, inspection logs or checklists</p>
              </>
            ) : (
              <div className="space-y-1">
                <p className="text-sm font-bold text-[#00E599]">
                  {files.length} Document{files.length > 1 ? 's' : ''} Attached
                </p>
                <div className="flex flex-wrap justify-center gap-2 mt-2">
                  {files.map((f, i) => (
                    <span key={i} className="text-xs font-mono px-2 py-0.5 rounded bg-[#163827] border border-[#23573E] text-white">
                      {f.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Deliverable Format Selector */}
        <div>
          <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
            2. Required Deliverable Formats
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: 'inspection_analysis' as OutputFormat, label: 'Statutory Report (.docx)', icon: FileText, desc: 'Detailed 10-section compliance file' },
              { id: 'presentation' as OutputFormat, label: 'Slide Deck (.pptx)', icon: Presentation, desc: 'Executive visual slides with notes' },
              { id: 'executive_summary' as OutputFormat, label: 'Approval Brief', icon: BarChart2, desc: 'Decision matrix for leadership' },
            ].map((fmt) => {
              const Icon = fmt.icon;
              const isSel = selectedOutputs.includes(fmt.id);
              return (
                <button
                  key={fmt.id}
                  type="button"
                  onClick={() => toggleOutput(fmt.id)}
                  disabled={isProcessing}
                  className={`p-3 rounded-lg border text-left flex items-start gap-3 transition-colors ${
                    isSel
                      ? 'bg-[#183D2B] border-[#00E599] text-white'
                      : 'bg-[#091A11] border-[#1E4D36] text-[#B8D5C6] hover:bg-[#102B1E]'
                  }`}
                >
                  <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${isSel ? 'text-[#00E599]' : 'text-[#74C69D]'}`} />
                  <div className="min-w-0">
                    <div className="text-xs font-bold truncate">{fmt.label}</div>
                    <div className="text-[10px] text-[#74C69D] truncate font-mono">{fmt.desc}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Prompt */}
        <div>
          <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
            3. Synthesis Scope &amp; Audit Focus
          </label>
          <textarea
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isProcessing}
            className="w-full rounded-xl bg-[#08170F] border border-[#1E4D36] p-3 text-xs text-gray-200 focus:outline-none focus:border-[#00E599] transition-colors font-serif leading-relaxed"
          />
        </div>

        {/* Execution Bar */}
        <div className="flex items-center gap-3 pt-2">
          {files.length > 0 && !isProcessing && (
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
            disabled={isProcessing || selectedOutputs.length === 0}
            className="flex-1 py-3 px-5 rounded-xl bg-[#00E599] hover:bg-[#00C070] text-black font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-black" />
                <span>Synthesizing Deliverables ({progressPct}%)…</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-black" />
                <span>Generate Inspection Deliverables ({selectedOutputs.length})</span>
              </>
            )}
          </button>
        </div>

        {isProcessing && (
          <div className="space-y-1.5 pt-2">
            <div className="flex justify-between text-xs font-mono text-[#74C69D]">
              <span>{progressMsg || 'Generating reports…'}</span>
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

      {/* Results Deliverables Cards */}
      {Object.keys(results).length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <ClipboardCheck className="w-5 h-5 text-[#00E599]" />
              Synthesized Statutory Deliverables ({Object.keys(results).length})
            </h3>
            <span className="text-xs text-[#74C69D] font-mono">100% On-Premise Storage</span>
          </div>

          <div className="space-y-4">
            {Object.entries(results).map(([key, res]) => {
              if (!res) return null;
              const content = res.content || '';
              const techSplit = content.split('## Technical & Sovereignty Evidence');
              const mainText = techSplit[0]?.trim() || content;

              return (
                <div key={key} className="p-5 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-[#1A402D]">
                    <div>
                      <h4 className="text-sm font-bold text-white uppercase font-mono">
                        {key.replace('_', ' ')}
                      </h4>
                      <span className="text-[10px] text-[#74C69D] font-mono">
                        {res.filename || `${key}_output`}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleCopy(key, mainText)}
                        className="px-2.5 py-1 rounded bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-xs font-mono text-[#B8D5C6] hover:text-white flex items-center gap-1.5"
                      >
                        {copiedKey === key ? <Check className="w-3 h-3 text-[#00E599]" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedKey === key ? 'Copied' : 'Copy'}</span>
                      </button>

                      {res.download_url && (
                        <button
                          type="button"
                          onClick={() => downloadFile(res.download_url!, res.filename)}
                          className="px-3 py-1 rounded bg-[#00E599] hover:bg-[#00C070] text-black text-xs font-bold font-mono flex items-center gap-1.5"
                        >
                          <Download className="w-3 h-3" />
                          <span>Download File</span>
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-[#06120B] border border-[#163827] text-xs sm:text-sm text-gray-200 leading-relaxed font-sans whitespace-pre-wrap max-h-80 overflow-y-auto scrollbar-thin">
                    {mainText}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
