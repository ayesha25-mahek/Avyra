import React, { useState } from 'react';
import {
  X, Download, Copy, CheckCheck, Edit3, Loader2, Video,
  Linkedin, Twitter, Presentation, FileText, BarChart2,
  Layout, PenTool, AlertCircle, History, Send, Eye, ClipboardCheck
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { downloadFile } from '@/lib/api';
import { cn } from '@/lib/utils';
import type { OutputFormat, ResultEvent } from '@/types';
import { OUTPUT_FORMATS } from '@/components/OutputFormatSelector';

const ICON_MAP: Record<string, React.FC<{ className?: string }>> = {
  Video,
  Linkedin,
  Twitter,
  Presentation,
  FileText,
  BarChart2,
  Layout,
  PenTool,
  ClipboardCheck,
};

interface OutputModalProps {
  isOpen: boolean;
  outputType: OutputFormat | null;
  currentResult: ResultEvent | null;
  history: ResultEvent[];
  isRevising: boolean;
  revisionError: string | null;
  onClose: () => void;
  onRevise: (outputType: OutputFormat, revisionPrompt: string) => Promise<void>;
  onSelectVersion?: (version: ResultEvent) => void;
}

export const OutputModal: React.FC<OutputModalProps> = ({
  isOpen,
  outputType,
  currentResult,
  history,
  isRevising,
  revisionError,
  onClose,
  onRevise,
}) => {
  const [copied, setCopied] = useState(false);
  const [showEditBox, setShowEditBox] = useState(false);
  const [editPrompt, setEditPrompt] = useState('');
  const [selectedVersionIndex, setSelectedVersionIndex] = useState<number | null>(null);

  if (!isOpen || !outputType || !currentResult) return null;

  const meta = OUTPUT_FORMATS.find((f) => f.id === outputType);
  const IconComponent = ICON_MAP[meta?.icon ?? 'FileText'] ?? FileText;

  // Compile version list including historical versions and current
  const allVersions: ResultEvent[] = history.length > 0
    ? [...history, currentResult]
    : [currentResult];

  const activeDisplayResult = selectedVersionIndex !== null && allVersions[selectedVersionIndex]
    ? allVersions[selectedVersionIndex]
    : currentResult;

  const activeIndex = selectedVersionIndex !== null ? selectedVersionIndex : allVersions.length - 1;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(activeDisplayResult.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard fallback
    }
  };

  const handleDownload = () => {
    if (activeDisplayResult.download_url) {
      downloadFile(activeDisplayResult.download_url, activeDisplayResult.filename);
    }
  };

  const handleApplyRevision = async () => {
    if (!editPrompt.trim() || isRevising) return;
    await onRevise(outputType, editPrompt.trim());
    setEditPrompt('');
    setShowEditBox(false);
    setSelectedVersionIndex(null);
  };

  const isVideo = outputType === 'video' && activeDisplayResult.download_url;
  const isPresentation = outputType === 'presentation';
  const isError = activeDisplayResult.status === 'error';
  const hasDownload = !!activeDisplayResult.download_url;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/85 backdrop-blur-md animate-in fade-in duration-150 font-serif">
      <div
        className="relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-md border border-[#173826] bg-[#040D08] shadow-2xl overflow-hidden text-gray-100"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#173826] bg-[#06150D] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-sm bg-[#00D084]/20 border border-[#00D084]/40 flex items-center justify-center">
              <IconComponent className="w-4 h-4 text-[#00D084]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white font-serif tracking-tight">
                  {meta?.label ?? outputType} Preview
                </h3>
                <Badge
                  variant={isError ? 'destructive' : 'success'}
                  className="text-[9px] font-sans rounded-sm px-1.5 py-0"
                >
                  {isError ? 'ERROR' : 'SYNTHESIZED'}
                </Badge>
              </div>
              <p className="text-[11px] font-mono text-gray-400">
                Pipeline: {outputType.toUpperCase()} {allVersions.length > 1 && `· Version ${activeIndex + 1} of ${allVersions.length}`}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 rounded-sm flex items-center justify-center text-gray-400 hover:text-white hover:bg-[#0E1E16] border border-transparent hover:border-[#173826] transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Version History Tab Bar */}
        {allVersions.length > 1 && (
          <div className="flex items-center gap-1 px-5 py-2 border-b border-[#173826] bg-[#030A06] overflow-x-auto text-xs font-serif shrink-0">
            <span className="text-gray-400 flex items-center gap-1 mr-2 text-[11px]">
              <History className="w-3 h-3 text-[#00D084]" /> History:
            </span>
            {allVersions.map((_, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setSelectedVersionIndex(idx)}
                className={cn(
                  'px-2.5 py-1 rounded-sm text-xs transition-all',
                  activeIndex === idx
                    ? 'bg-[#00D084] text-black font-bold'
                    : 'bg-[#06150D] text-gray-300 border border-[#173826] hover:bg-[#0A1F13]'
                )}
              >
                {idx === 0 ? 'v1 (Original)' : `v${idx + 1} (Revised)`}
              </button>
            ))}
          </div>
        )}

        {/* Revision In-Progress Banner */}
        {isRevising && (
          <div className="flex items-center gap-2.5 px-5 py-2.5 bg-[#00D084]/15 border-b border-[#00D084]/30 text-xs text-[#00D084] font-serif shrink-0 animate-pulse">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Autonomous engine is synthesizing your revision request…</span>
          </div>
        )}

        {/* Revision Error Alert */}
        {revisionError && (
          <div className="flex items-start gap-2 px-5 py-2.5 bg-red-500/10 border-b border-red-500/30 text-xs text-red-300 font-serif shrink-0">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-bold">Revision Failed: </span>
              <span>{revisionError}</span>
            </div>
          </div>
        )}

        {/* Modal Main Body (Scrollable with Dark Green Styling) */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 font-serif">
          {/* Video Preview if applicable */}
          {isVideo && (
            <div className="rounded-md border border-[#173826] overflow-hidden bg-black space-y-2">
              <video
                src={activeDisplayResult.download_url}
                controls
                className="w-full max-h-80 object-contain bg-black"
              >
                Your browser does not support HTML5 video preview.
              </video>
            </div>
          )}

          {/* Presentation Slide Deck Preview Card */}
          {isPresentation && (
            <div className="rounded-md border border-[#173826] bg-[#06150D] p-3.5 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <Presentation className="w-5 h-5 text-[#00D084]" />
                <div>
                  <p className="text-xs font-bold text-white tracking-wide">
                    {activeDisplayResult.filename ?? 'Enterprise Slide Deck Presentation.pptx'}
                  </p>
                  <p className="text-[11px] text-gray-400 font-serif">
                    Structured slides with title, bullet breakdown, and executive speaker notes.
                  </p>
                </div>
              </div>
              {hasDownload && (
                <Button
                  onClick={handleDownload}
                  size="sm"
                  className="gap-1.5 font-serif text-xs rounded-sm bg-[#00D084] text-black hover:bg-[#05E594] font-bold shrink-0"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download PPTX
                </Button>
              )}
            </div>
          )}

          {/* Document / File Banner for non-video downloads */}
          {hasDownload && !isVideo && !isPresentation && (
            <div className="flex items-center justify-between p-3.5 rounded-md bg-[#06150D] border border-[#173826]">
              <div className="flex items-center gap-2.5">
                <FileText className="w-5 h-5 text-[#00D084]" />
                <div>
                  <p className="text-xs font-bold text-white tracking-wide">
                    {activeDisplayResult.filename ?? `${meta?.label ?? outputType} Deliverable`}
                  </p>
                  <p className="text-[10px] text-gray-400 font-mono">Ready for download and team distribution</p>
                </div>
              </div>
              <Button
                onClick={handleDownload}
                size="sm"
                className="gap-1.5 font-serif text-xs rounded-sm bg-[#00D084] text-black hover:bg-[#05E594] font-bold"
              >
                <Download className="w-3 h-3" />
                Download
              </Button>
            </div>
          )}

          {/* Content Preview Container */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono text-[#00D084] uppercase tracking-wider flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5" />
                Live Content Preview
              </span>
              <span className="text-[10px] font-mono text-gray-400">
                {activeDisplayResult.content.length.toLocaleString()} characters
              </span>
            </div>

            <div className="p-4 sm:p-5 rounded-md bg-[#020805] border border-[#173826] text-gray-200 font-serif leading-relaxed max-h-[420px] overflow-y-auto whitespace-pre-wrap text-xs sm:text-sm selection:bg-[#00D084] selection:text-black">
              {activeDisplayResult.content}
            </div>
          </div>

          {/* Inline Edit Prompt Panel */}
          {showEditBox && (
            <div className="p-4 rounded-md bg-[#06150D] border border-[#00D084]/50 space-y-3 animate-in fade-in duration-150">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-white flex items-center gap-1.5 font-serif">
                  <Edit3 className="w-3.5 h-3.5 text-[#00D084]" />
                  Describe changes for re-generation:
                </label>
                <span className="text-[10px] font-mono text-gray-400">Routes through Avyra Engine</span>
              </div>

              <Textarea
                value={editPrompt}
                onChange={(e) => setEditPrompt(e.target.value)}
                disabled={isRevising}
                placeholder="Example: 'Make tone more urgent, add 3 bullet points with enterprise ROI numbers', 'Shorten to 150 words', 'Emphasize cloud architecture'..."
                className="min-h-[85px] text-xs font-serif bg-[#020805] border-[#173826] focus:border-[#00D084]"
              />

              <div className="flex items-center justify-end gap-2 pt-1">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowEditBox(false)}
                  disabled={isRevising}
                  className="text-xs font-serif rounded-sm border-[#173826] bg-[#08180E]"
                >
                  Cancel
                </Button>
                <Button
                  type="button"
                  size="sm"
                  onClick={handleApplyRevision}
                  disabled={isRevising || !editPrompt.trim()}
                  className="gap-1.5 font-serif text-xs rounded-sm bg-[#00D084] text-black hover:bg-[#05E594] font-bold disabled:opacity-40"
                >
                  {isRevising ? (
                    <>
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Revising…
                    </>
                  ) : (
                    <>
                      <Send className="w-3 h-3" />
                      Re-generate with Changes
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Modal Actions Footer: Edit + Download / Copy */}
        <div className="flex items-center justify-between px-5 py-3.5 border-t border-[#173826] bg-[#06150D] shrink-0 font-serif">
          {/* Edit Button */}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowEditBox(!showEditBox)}
            disabled={isRevising}
            className={cn(
              'gap-1.5 text-xs font-serif rounded-sm border-[#173826] transition-all',
              showEditBox
                ? 'bg-[#00D084]/20 border-[#00D084]/60 text-[#00D084]'
                : 'bg-[#08180E] text-gray-200 hover:border-[#00D084]/50 hover:text-white'
            )}
          >
            <Edit3 className="w-3.5 h-3.5 text-[#00D084]" />
            {showEditBox ? 'Close Edit Box' : 'Edit Prompt'}
          </Button>

          {/* Action Buttons: Copy / Download */}
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="gap-1.5 font-serif text-xs rounded-sm border-[#173826] bg-[#08180E] text-gray-200 hover:text-white"
            >
              {copied ? <CheckCheck className="w-3.5 h-3.5 text-[#00D084]" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </Button>

            {hasDownload && (
              <Button
                type="button"
                size="sm"
                onClick={handleDownload}
                className="gap-1.5 font-serif text-xs rounded-sm bg-[#00D084] text-black hover:bg-[#05E594] font-bold"
              >
                <Download className="w-3.5 h-3.5" />
                Download Deliverable
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
