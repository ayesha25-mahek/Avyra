import React, { useState } from 'react';
import {
  Layers,
  Zap,
  RotateCcw,
  Download,
  Copy,
  Check,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Tag,
  Loader2,
  ZoomIn,
  FileText,
  Presentation,
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

const DRAWING_OUTPUT_OPTIONS: OutputOption[] = [
  {
    id: 'drawing_analysis',
    label: 'Drawing Analysis',
    badge: 'P&ID Profile',
    desc: 'Structured 8-section schematic & loop deconstruction',
    icon: Layers,
  },
  {
    id: 'equipment_tags',
    label: 'Equipment & Tag Extraction',
    badge: 'Structured Table',
    desc: 'Extracted pump, vessel, valve, and line designations',
    icon: Tag,
  },
  {
    id: 'technical_report',
    label: 'Technical Report (DOCX)',
    badge: 'DOCX Deliverable',
    desc: 'Formal engineering blueprint review deliverable',
    icon: FileText,
  },
  {
    id: 'presentation',
    label: 'Drawing Summary Deck (PPTX)',
    badge: 'PPTX Slides',
    desc: 'Process flow & equipment summary slide deck',
    icon: Presentation,
  },
  {
    id: 'infographic',
    label: 'Tag / Equipment Spec',
    badge: 'Optional Layout',
    desc: 'Visual tag callout & schematic specification',
    icon: Layout,
  },
];

import { DocumentToCadGenerator } from './DocumentToCadGenerator';

type DrawingSubTab = 'blueprint_analysis' | 'doc_to_cad';

interface DrawingAnalysisViewProps {
  initialSubTab?: DrawingSubTab;
}

export const DrawingAnalysisView: React.FC<DrawingAnalysisViewProps> = ({ initialSubTab = 'blueprint_analysis' }) => {
  const [subTab, setSubTab] = useState<DrawingSubTab>(initialSubTab);

  React.useEffect(() => {
    if (initialSubTab) {
      setSubTab(initialSubTab);
    }
  }, [initialSubTab]);

  const [drawingFile, setDrawingFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [prompt, setPrompt] = useState(
    'Review this P&ID / engineering drawing schematic. Extract all readable equipment tags (e.g., pumps, pressure vessels, heat exchangers), pipeline line designations, control valves, and process limits. Explicitly mark illegible or unreadable notations.'
  );
  const [selectedOutputs, setSelectedOutputs] = useState<OutputFormat[]>([
    'drawing_analysis',
    'equipment_tags',
    'technical_report',
  ]);

  const [isProcessing, setIsProcessing] = useState(false);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);
  const [progressPct, setProgressPct] = useState(0);
  const [results, setResults] = useState<Partial<Record<OutputFormat, ResultEvent>>>({});
  const [activeOutputTab, setActiveOutputTab] = useState<OutputFormat>('drawing_analysis');
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showTechDetails, setShowTechDetails] = useState(false);

  // Revision state
  const [revisionPrompts, setRevisionPrompts] = useState<Partial<Record<OutputFormat, string>>>({});
  const [revisingType, setRevisingType] = useState<OutputFormat | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setDrawingFile(file);
      if (file.type.startsWith('image/')) {
        setPreviewUrl(URL.createObjectURL(file));
      } else {
        setPreviewUrl(null);
      }
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
    if (!drawingFile) return;
    if (selectedOutputs.length === 0) return;

    setIsProcessing(true);
    setProgressMsg('Parsing schematic layout & extracting engineering tags…');
    setProgressPct(20);
    setResults({});
    setError(null);

    const formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('outputs', JSON.stringify(selectedOutputs));
    formData.append('provider', 'ollama');
    formData.append('files', drawingFile);

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
      setError(err?.message || 'Drawing analysis failed');
      setIsProcessing(false);
    }
  };

  const handleRevise = async (outputType: OutputFormat) => {
    const revPrompt = revisionPrompts[outputType]?.trim();
    if (!drawingFile || !revPrompt) return;

    setRevisingType(outputType);
    setError(null);

    const formData = new FormData();
    const contextualPrompt = `[Follow-up Revision for ${outputType.toUpperCase()}]
Original Analysis Objective:
${prompt}

User Revision Instructions:
${revPrompt}`;

    formData.append('prompt', contextualPrompt);
    formData.append('outputs', JSON.stringify([outputType]));
    formData.append('provider', 'ollama');
    formData.append('files', drawingFile);

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
    setDrawingFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
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

  // Extract equipment tags from markdown if found
  const tagMatches = Array.from(mainReportText.matchAll(/\b([A-Z]{1,4}-\d{2,5}[A-Z]?)\b/g)).map(m => m[1]);
  const uniqueTags = Array.from(new Set(tagMatches)).slice(0, 8);

  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-6xl mx-auto">
      {/* Page Heading */}
      <div className="pb-4 border-b border-[#1A402D]">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#143324] border border-[#23573E] text-[#00E599]">
            MODULE 04
          </span>
          <span className="text-xs text-[#74C69D] font-mono">P&amp;ID &amp; CAD Generation Suite</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Engineering Drawing &amp; P&amp;ID Analysis
        </h1>
        <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
          Deconstruct piping and instrumentation diagrams, or synthesize deterministic AutoCAD DXF &amp; SVG engineering drawings directly from technical requirements.
        </p>

        {/* Feature Sub-Navigation Tabs */}
        <div className="flex items-center gap-2 mt-4 pt-3 border-t border-[#1A402D]/60">
          <button
            onClick={() => setSubTab('blueprint_analysis')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors border ${
              subTab === 'blueprint_analysis'
                ? 'bg-[#143324] text-[#00E599] border-[#23573E] font-bold'
                : 'bg-[#091A11] text-[#9DC4B0] border-[#1A402D] hover:bg-[#0E2419]'
            }`}
          >
            P&amp;ID Schematic &amp; Blueprint Analysis
          </button>
          <button
            onClick={() => setSubTab('doc_to_cad')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors border ${
              subTab === 'doc_to_cad'
                ? 'bg-[#143324] text-[#00E599] border-[#23573E] font-bold'
                : 'bg-[#091A11] text-[#9DC4B0] border-[#1A402D] hover:bg-[#0E2419]'
            }`}
          >
            Document-to-CAD Generator (SVG &amp; DXF)
          </button>
        </div>
      </div>

      {subTab === 'doc_to_cad' && <DocumentToCadGenerator />}

      {subTab === 'blueprint_analysis' && (
        <>
          {/* Main Workspace Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Input & Prompt (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-5 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
                1. Upload Blueprint / P&amp;ID (PNG, JPG, PDF)
              </label>
              <div className="border border-dashed border-[#1E4D36] hover:border-[#00E599]/60 rounded-xl p-4 text-center bg-[#091A11] transition-colors relative">
                <input
                  type="file"
                  accept=".png,.jpg,.jpeg,.pdf"
                  onChange={handleFileSelect}
                  disabled={isProcessing}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                />
                <div className="w-10 h-10 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center mx-auto mb-2 text-[#00E599]">
                  <Layers className="w-4 h-4" />
                </div>
                {drawingFile ? (
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-[#00E599] truncate">{drawingFile.name}</p>
                    <p className="text-[10px] text-[#74C69D] font-mono">
                      {(drawingFile.size / 1024).toFixed(1)} KB • {drawingFile.type || 'document'}
                    </p>
                  </div>
                ) : (
                  <>
                    <p className="text-xs font-semibold text-white">Click to select blueprint schematic</p>
                    <p className="text-[11px] text-[#74C69D] mt-0.5 font-mono">P&amp;ID, PFD, or GA drawing</p>
                  </>
                )}
              </div>
            </div>

            {/* Output Format Selector */}
            <div>
              <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono flex items-center justify-between">
                <span>2. Select Deliverable Formats</span>
                <span className="text-[10px] text-[#74C69D] lowercase">({selectedOutputs.length} selected)</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {DRAWING_OUTPUT_OPTIONS.map((opt) => {
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

            {/* Prompt */}
            <div>
              <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
                3. Drawing Extraction Directives
              </label>
              <textarea
                rows={3}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isProcessing}
                className="w-full rounded-xl bg-[#08170F] border border-[#1E4D36] p-3 text-xs text-gray-200 focus:outline-none focus:border-[#00E599] transition-colors font-serif leading-relaxed"
              />
            </div>

            <div className="flex items-center gap-2 pt-1">
              {drawingFile && !isProcessing && (
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-3.5 py-2.5 rounded-xl bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-xs font-medium text-[#B8D5C6] flex items-center gap-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Reset
                </button>
              )}

              <button
                type="button"
                onClick={handleExecute}
                disabled={isProcessing || !drawingFile || selectedOutputs.length === 0}
                className="flex-1 py-3 px-4 rounded-xl bg-[#00E599] hover:bg-[#00C070] text-black font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-black" />
                    <span>Parsing Schematic ({progressPct}%)…</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 fill-black" />
                    <span>Analyze Drawing ({selectedOutputs.length})</span>
                  </>
                )}
              </button>
            </div>

            {isProcessing && (
              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between text-xs font-mono text-[#74C69D]">
                  <span>{progressMsg || 'Processing…'}</span>
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
        </div>

        {/* Right: Drawing Preview (7 cols) */}
        <div className="lg:col-span-7">
          <div className="p-5 rounded-xl bg-[#0E2419] border border-[#1A402D] h-full flex flex-col justify-between space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#1A402D]">
              <span className="text-xs font-bold text-white flex items-center gap-2">
                <ZoomIn className="w-4 h-4 text-[#00E599]" />
                Schematic Blueprint Preview
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#102B1E] border border-[#1E4D36] text-[#74C69D]">
                OCR Tag Extraction
              </span>
            </div>

            {previewUrl ? (
              <div className="relative rounded-lg overflow-hidden border border-[#23573E] bg-[#030805] flex items-center justify-center min-h-[300px] max-h-[440px]">
                <img
                  src={previewUrl}
                  alt="Engineering schematic"
                  className="max-h-[420px] w-auto object-contain mx-auto"
                />
              </div>
            ) : (
              <div className="rounded-lg border border-[#1A402D] bg-[#07170E] min-h-[300px] flex flex-col items-center justify-center p-8 text-center text-[#6B8F7B] space-y-2">
                <Layers className="w-10 h-10 opacity-40 text-[#00E599]" />
                <p className="text-xs font-mono">
                  {drawingFile ? `${drawingFile.name} (Blueprint Loaded)` : 'No drawing selected'}
                </p>
                <p className="text-[11px] text-[#527361] max-w-xs">
                  Upload a P&amp;ID image or PDF to inspect line connections, tags, and valves.
                </p>
              </div>
            )}

            {/* Extracted Equipment Tags Bar if any detected */}
            {uniqueTags.length > 0 && (
              <div className="p-2.5 rounded-lg bg-[#0A1A12] border border-[#183B29] space-y-1.5">
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#74C69D] flex items-center gap-1">
                  <Tag className="w-3 h-3 text-[#00E599]" /> Identified Equipment Tags:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {uniqueTags.map((t, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded text-[11px] font-mono bg-[#143324] border border-[#23573E] text-white">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Structured Results Workspace + Multi-output Tabs + Revision */}
      {Object.keys(results).length > 0 && (
        <div className="p-5 sm:p-6 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1A402D]">
            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-thin">
              {Object.keys(results).map((fmtKey) => {
                const fmt = fmtKey as OutputFormat;
                const opt = DRAWING_OUTPUT_OPTIONS.find((o) => o.id === fmt);
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
                  <span>Download {currentResult.filename?.split('.').pop()?.toUpperCase() || 'File'}</span>
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
              Follow-up Revision for {DRAWING_OUTPUT_OPTIONS.find((o) => o.id === activeOutputTab)?.label || activeOutputTab}
            </label>
            <div className="flex flex-col sm:flex-row items-center gap-2">
              <input
                type="text"
                placeholder="e.g. Verify tie-in line connections, clarify safety valve setpoint, or highlight pump tag P-101B…"
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
