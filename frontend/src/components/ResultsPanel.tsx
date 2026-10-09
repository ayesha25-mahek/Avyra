import React, { useState } from 'react';
import {
  Copy, Download, CheckCheck, FileText, Video, Linkedin,
  Twitter, Presentation, BarChart2, Layout, PenTool, AlertCircle, Eye, ClipboardCheck
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { downloadFile } from '@/lib/api';
import type { ResultEvent, OutputFormat } from '@/types';
import { OUTPUT_FORMATS } from '@/components/OutputFormatSelector';

const ICON_MAP: Record<string, React.FC<{ className?: string }>> = {
  Video, Linkedin, Twitter, Presentation, FileText, BarChart2, Layout, PenTool, ClipboardCheck,
};

interface ResultCardProps {
  result: ResultEvent;
  index: number;
  onView: (outputType: OutputFormat) => void;
}

const ResultCard: React.FC<ResultCardProps> = ({ result, onView }) => {
  const [copied, setCopied] = useState(false);
  const meta = OUTPUT_FORMATS.find((f) => f.id === result.output_type);
  const IconComponent = ICON_MAP[meta?.icon ?? 'FileText'] ?? FileText;

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(result.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (result.download_url) {
      downloadFile(result.download_url, result.filename);
    }
  };

  const isError = result.status === 'error';
  const hasDownload = !!result.download_url;
  const hasText = !!result.content;

  // Snippet preview for card display (first 220 characters)
  const snippet = result.content
    ? result.content.slice(0, 240).replace(/^[#*-]\s+/gm, '') + (result.content.length > 240 ? '…' : '')
    : 'No content synthesized yet.';

  return (
    <div
      onClick={() => onView(result.output_type)}
      className={cn(
        'group cursor-pointer relative rounded-xl border flex flex-col justify-between overflow-hidden transition-all duration-200',
        'bg-white p-5 text-left shadow-sm',
        isError ? 'border-red-400' : 'border-[#DCE4E0] hover:border-[#246346]/50 hover:shadow-md'
      )}
    >
      {/* Top Bar: Icon + Title + Status */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className={cn(
              'w-9 h-9 rounded-lg flex items-center justify-center shrink-0 border',
              isError
                ? 'bg-red-50 border-red-200 text-red-600'
                : 'bg-[#EAF2EE] border-[#CFDFD6] text-[#246346]'
            )}>
              {isError
                ? <AlertCircle className="w-4 h-4" />
                : <IconComponent className="w-4 h-4" />
              }
            </div>
            <div className="min-w-0">
              <h4 className="text-xs sm:text-sm font-semibold text-[#101F17] tracking-tight truncate font-serif group-hover:text-[#246346] transition-colors">
                {meta?.label ?? result.output_type}
              </h4>
              <span className="text-[10px] font-mono text-[#567062]">
                {result.output_type.toUpperCase()}
              </span>
            </div>
          </div>

          <Badge variant={isError ? 'destructive' : 'success'} className="text-[9px] shrink-0 font-sans rounded-md px-2 py-0.5">
            {isError ? 'ERROR' : 'READY'}
          </Badge>
        </div>

        {/* Snippet Preview (Click to open full popup preview) */}
        <div className="mb-3.5 p-3 rounded-lg bg-[#F0F5F2] border border-[#D5E0DA] text-xs text-[#2A4034] font-serif line-clamp-3 leading-relaxed">
          {snippet}
        </div>
      </div>

      {/* Card Action Buttons (Clicking card opens popup, or use direct buttons) */}
      <div className="pt-2.5 border-t border-[#EEF3F0] flex items-center justify-between gap-2">
        <span className="text-[11px] font-serif text-[#246346] flex items-center gap-1 group-hover:translate-x-0.5 transition-transform font-semibold">
          <Eye className="w-3.5 h-3.5" />
          Preview &amp; Edit
        </span>

        <div className="flex items-center gap-1.5">
          {hasText && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              title="Quick copy"
              className="h-7 px-2.5 text-[10px] rounded-lg bg-[#EAF2EE] border-[#CFDFD6] text-[#246346] hover:bg-[#246346] hover:text-white"
            >
              {copied ? <CheckCheck className="w-3.5 h-3.5 text-[#246346]" /> : <Copy className="w-3.5 h-3.5" />}
            </Button>
          )}

          {hasDownload && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              title="Download file"
              className="h-7 px-2.5 text-[10px] rounded-lg bg-[#EAF2EE] border-[#CFDFD6] text-[#246346] hover:bg-[#246346] hover:text-white"
            >
              <Download className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

interface ResultsPanelProps {
  results: Partial<Record<OutputFormat, ResultEvent>>;
  onDownloadAll: () => void;
  onView: (outputType: OutputFormat) => void;
}

const ResultsPanel: React.FC<ResultsPanelProps> = ({ results, onDownloadAll, onView }) => {
  const entries = Object.values(results).filter(Boolean) as ResultEvent[];
  const hasDownloadable = entries.some((r) => r.download_url);

  return (
    <div className="space-y-4 font-serif text-[#101F17]">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-[#246346]" />
          <span className="text-sm sm:text-base font-bold text-[#101F17] font-serif tracking-wide">
            Synthesized Outputs
          </span>
          <span className="font-serif text-xs px-2.5 py-0.5 rounded-md bg-[#E8F0EC] text-[#246346] border border-[#CFDFD6] font-semibold">
            {entries.length} Deliverable{entries.length > 1 ? 's' : ''} Ready
          </span>
        </div>

        {hasDownloadable && (
          <Button
            variant="outline"
            size="sm"
            onClick={onDownloadAll}
            className="gap-1.5 text-xs font-serif rounded-lg border-[#CFDFD6] bg-white text-[#246346] hover:bg-[#EAF2EE] shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-[#246346]" />
            Download All Assets
          </Button>
        )}
      </div>

      <p className="text-xs text-[#567062] font-serif">
        Click any generated output below to inspect the full preview, make instant AI revisions, or download the deliverable.
      </p>

      {/* Side-by-Side Grid (1 col on mobile, 2 cols on tablet/desktop) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {entries.map((result, i) => (
          <ResultCard key={result.output_type} result={result} index={i} onView={onView} />
        ))}
      </div>
    </div>
  );
};

export { ResultsPanel };
