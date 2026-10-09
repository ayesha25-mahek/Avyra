import React, { useState } from 'react';
import {
  Eye,
  Zap,
  RotateCcw,
  Download,
  Copy,
  Check,
  AlertCircle,
  Camera,
  ChevronDown,
  ChevronUp,
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

const DEFECT_OUTPUT_OPTIONS: OutputOption[] = [
  {
    id: 'inspection_summary',
    label: 'Inspection Summary',
    badge: 'Visual Profile',
    desc: 'Structured 8-section visual defect analysis & findings',
    icon: Eye,
  },
  {
    id: 'defect_report',
    label: 'Defect Inspection Report (DOCX)',
    badge: 'DOCX Deliverable',
    desc: 'Formal compliance inspection document for sign-off',
    icon: FileText,
  },
  {
    id: 'presentation',
    label: 'Management Presentation (PPTX)',
    badge: 'PPTX Slides',
    desc: 'Executive briefing slide deck with defect severity notes',
    icon: Presentation,
  },
  {
    id: 'infographic',
    label: 'Visual Findings Spec',
    badge: 'Optional Layout',
    desc: 'Infographic layout & visual callout specification',
    icon: Layout,
  },
];

export const ImageDefectView: React.FC = () => {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [prompt, setPrompt] = useState(
    'Inspect this physical equipment photograph for defects. Detect visible cracks, corrosion, voiding, mechanical distortion, or wear. Report findings using the 8-section visual defect profile, noting exact locations and separating observed facts from preliminary assessments.'
  );
  const [selectedOutputs, setSelectedOutputs] = useState<OutputFormat[]>([
    'inspection_summary',
    'defect_report',
  ]);

  const [isProcessing, setIsProcessing] = useState(false);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);
  const [progressPct, setProgressPct] = useState(0);
  const [results, setResults] = useState<Partial<Record<OutputFormat, ResultEvent>>>({});
  const [activeOutputTab, setActiveOutputTab] = useState<OutputFormat>('inspection_summary');
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showTechDetails, setShowTechDetails] = useState(false);

  // Revision state
  const [revisionPrompts, setRevisionPrompts] = useState<Partial<Record<OutputFormat, string>>>({});
  const [revisingType, setRevisingType] = useState<OutputFormat | null>(null);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImageFile(file);
      setPreviewUrl(URL.createObjectURL(file));
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
    if (!imageFile) return;
    if (selectedOutputs.length === 0) return;

    setIsProcessing(true);
    setProgressMsg('Scanning image with local multimodal vision…');
    setProgressPct(15);
    setResults({});
    setError(null);

    const formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('outputs', JSON.stringify(selectedOutputs));
    formData.append('provider', 'ollama');
    formData.append('files', imageFile);

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
      setError(err?.message || 'Visual defect inspection failed');
      setIsProcessing(false);
    }
  };

  const handleRevise = async (outputType: OutputFormat) => {
    const revPrompt = revisionPrompts[outputType]?.trim();
    if (!imageFile || !revPrompt) return;

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
    formData.append('files', imageFile);

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
    setImageFile(null);
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

  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-6xl mx-auto">
      {/* Page Heading */}
      <div className="pb-4 border-b border-[#1A402D]">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#143324] border border-[#23573E] text-[#00E599]">
            MODULE 03
          </span>
          <span className="text-xs text-[#74C69D] font-mono">Multimodal Defect Vision</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Image Defect &amp; Surface Integrity Analysis
        </h1>
        <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
          High-precision optical inspection on equipment photographs, welds, pipelines, and mechanical components. Identifies visible anomalies and maps spatial defect coordinates without cloud transmission.
        </p>
      </div>

      {/* Main Workspace Grid: Controls + Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Upload & Output Controls (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-5 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
            {/* 1. File Upload */}
            <div>
              <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
                1. Select Equipment Photograph (PNG, JPG, WEBP)
              </label>
              <div className="border border-dashed border-[#1E4D36] hover:border-[#00E599]/60 rounded-xl p-4 text-center bg-[#091A11] transition-colors relative">
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/jpg,image/webp"
                  onChange={handleImageSelect}
                  disabled={isProcessing}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                />
                <div className="w-10 h-10 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center mx-auto mb-2 text-[#00E599]">
                  <Camera className="w-4 h-4" />
                </div>
                {imageFile ? (
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-[#00E599] truncate">{imageFile.name}</p>
                    <p className="text-[10px] text-[#74C69D] font-mono">
                      {(imageFile.size / 1024).toFixed(1)} KB • {imageFile.type || 'image'}
                    </p>
                  </div>
                ) : (
                  <>
                    <p className="text-xs font-semibold text-white">Click or drag inspection photograph</p>
                    <p className="text-[11px] text-[#74C69D] mt-0.5 font-mono">Surface wear, weld, or component image</p>
                  </>
                )}
              </div>
            </div>

            {/* 2. Target Output Selection */}
            <div>
              <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono flex items-center justify-between">
                <span>2. Select Deliverable Formats</span>
                <span className="text-[10px] text-[#74C69D] lowercase">({selectedOutputs.length} selected)</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {DEFECT_OUTPUT_OPTIONS.map((opt) => {
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

            {/* 3. Task Prompt */}
            <div>
              <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
                3. Inspection Instructions
              </label>
              <textarea
                rows={3}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isProcessing}
                className="w-full rounded-xl bg-[#08170F] border border-[#1E4D36] p-3 text-xs text-gray-200 focus:outline-none focus:border-[#00E599] transition-colors font-serif leading-relaxed"
              />
            </div>

            {/* Execution Buttons */}
            <div className="flex items-center gap-2 pt-1">
              {imageFile && !isProcessing && (
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
                disabled={isProcessing || !imageFile || selectedOutputs.length === 0}
                className="flex-1 py-3 px-4 rounded-xl bg-[#00E599] hover:bg-[#00C070] text-black font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-black" />
                    <span>Analyzing Vision ({progressPct}%)…</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 fill-black" />
                    <span>Analyze Image Defect ({selectedOutputs.length})</span>
                  </>
                )}
              </button>
            </div>

            {isProcessing && (
              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between text-xs font-mono text-[#74C69D]">
                  <span>{progressMsg || 'Inspecting image…'}</span>
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

        {/* Right Column: Image Preview + Spatial Overlay (7 cols) */}
        <div className="lg:col-span-7">
          <div className="p-5 rounded-xl bg-[#0E2419] border border-[#1A402D] h-full flex flex-col justify-between space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#1A402D]">
              <span className="text-xs font-bold text-white flex items-center gap-2">
                <ZoomIn className="w-4 h-4 text-[#00E599]" />
                Optical Image Preview &amp; Spatial Localization
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#102B1E] border border-[#1E4D36] text-[#74C69D]">
                3x3 Grid Ready
              </span>
            </div>

            {previewUrl ? (
              <div className="relative rounded-lg overflow-hidden border border-[#23573E] bg-black flex items-center justify-center min-h-[300px] max-h-[440px]">
                <img
                  src={previewUrl}
                  alt="Equipment inspection target"
                  className="max-h-[420px] w-auto object-contain mx-auto"
                />
                {/* 3x3 Grid Overlay Lines */}
                <div className="absolute inset-0 pointer-events-none grid grid-cols-3 grid-rows-3 border border-[#00E599]/30">
                  <div className="border-r border-b border-[#00E599]/20" />
                  <div className="border-r border-b border-[#00E599]/20" />
                  <div className="border-b border-[#00E599]/20" />
                  <div className="border-r border-b border-[#00E599]/20" />
                  <div className="border-r border-b border-[#00E599]/20" />
                  <div className="border-b border-[#00E599]/20" />
                  <div className="border-r border-b border-[#00E599]/20" />
                  <div className="border-r border-b border-[#00E599]/20" />
                  <div />
                </div>
              </div>
            ) : (
              <div className="rounded-lg border border-[#1A402D] bg-[#07170E] min-h-[300px] flex flex-col items-center justify-center p-8 text-center text-[#6B8F7B] space-y-2">
                <Eye className="w-10 h-10 opacity-40 text-[#00E599]" />
                <p className="text-xs font-mono">No equipment image selected</p>
                <p className="text-[11px] text-[#527361] max-w-xs">
                  Upload an image to activate high-resolution optical inspection and defect localization.
                </p>
              </div>
            )}

            <div className="text-[11px] font-mono text-[#74C69D] flex items-center justify-between pt-1">
              <span>Vision Status: {imageFile ? 'Target Loaded' : 'Awaiting Image'}</span>
              <span>Model: Local Vision Parser</span>
            </div>
          </div>
        </div>
      </div>

      {/* Results View: Multi-Output Tabs + Follow-up Revision */}
      {Object.keys(results).length > 0 && (
        <div className="p-5 sm:p-6 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-4">
          {/* Output Selector Tabs */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1A402D]">
            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-thin">
              {Object.keys(results).map((fmtKey) => {
                const fmt = fmtKey as OutputFormat;
                const opt = DEFECT_OUTPUT_OPTIONS.find((o) => o.id === fmt);
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
              Follow-up Revision for {DEFECT_OUTPUT_OPTIONS.find((o) => o.id === activeOutputTab)?.label || activeOutputTab}
            </label>
            <div className="flex flex-col sm:flex-row items-center gap-2">
              <input
                type="text"
                placeholder="e.g. Focus on root-cause mitigation, tighten inspection intervals, or add human approval sign-off note…"
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

          {/* Collapsible Technical Details */}
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
    </div>
  );
};
