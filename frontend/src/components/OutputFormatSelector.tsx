import {
  Presentation, FileText,
  BarChart2, Check, ClipboardCheck
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { OutputFormat, OutputFormatMeta } from '@/types';

const OUTPUT_FORMATS: OutputFormatMeta[] = [
  {
    id: 'inspection_analysis',
    label: 'Inspection & Risk Report',
    description: 'Defect analysis, compliance verification & sign-off',
    icon: 'ClipboardCheck',
    estimatedTime: '~25s',
    badge: 'Standard',
  },
  {
    id: 'executive_summary',
    label: 'Executive Approval Brief',
    description: 'Decision matrices, C-suite KPIs & executive actions',
    icon: 'BarChart2',
    estimatedTime: '~20s',
    badge: 'Executive',
  },
  {
    id: 'presentation',
    label: 'Deck Presentation (.pptx)',
    description: 'Executive slides with field findings & notes',
    icon: 'Presentation',
    estimatedTime: '~35s',
    badge: 'PPTX',
  },
  {
    id: 'advisory',
    label: 'Technical Advisory',
    description: 'Mitigation frameworks & corrective interventions',
    icon: 'FileText',
    estimatedTime: '~30s',
    badge: 'Engineering',
  },
];


const ICON_MAP: Record<string, React.FC<{ className?: string }>> = {
  Presentation,
  FileText,
  BarChart2,
  ClipboardCheck,
};

interface OutputFormatCardProps {
  format: OutputFormatMeta;
  selected: boolean;
  onToggle: (id: OutputFormat) => void;
  disabled?: boolean;
}

const OutputFormatCard: React.FC<OutputFormatCardProps> = ({ format, selected, onToggle, disabled }) => {
  const IconComponent = ICON_MAP[format.icon] ?? FileText;

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onToggle(format.id)}
      className={cn(
        'group relative w-full flex items-center gap-2.5 p-2.5 rounded-lg transition-all duration-150 text-left border select-none',
        selected
          ? 'bg-[#1B4330] border-[#2D6E4E] text-white shadow-sm'
          : 'bg-[#0F261B] border-[#1A402D] text-[#B8D5C6] hover:border-[#265E43] hover:bg-[#143324]',
        disabled && 'opacity-40 cursor-not-allowed'
      )}
    >
      {/* Small Checkbox Square */}
      <div
        className={cn(
          'w-4 h-4 rounded-md border flex items-center justify-center shrink-0 transition-colors',
          selected
            ? 'bg-[#74C69D] border-[#74C69D] text-black'
            : 'border-[#265E43] bg-[#0F261B] group-hover:border-[#74C69D]'
        )}
      >
        {selected && <Check className="w-3 h-3 stroke-[3]" />}
      </div>

      {/* Mini Icon */}
      <div
        className={cn(
          'w-7 h-7 rounded-md flex items-center justify-center shrink-0 border transition-colors',
          selected
            ? 'bg-[#143324] border-[#265E43] text-[#74C69D]'
            : 'bg-[#0F261B] border-[#1A402D] text-[#9DC4B0] group-hover:text-white'
        )}
      >
        <IconComponent className="w-3.5 h-3.5" />
      </div>

      {/* Label and Info */}
      <div className="flex-1 min-w-0 pr-1">
        <div className="flex items-center gap-1.5 justify-between">
          <span className="text-xs font-bold font-serif truncate leading-tight">
            {format.label}
          </span>
          <span className="text-[9px] font-mono text-gray-500 shrink-0">
            {format.estimatedTime}
          </span>
        </div>
        <p className="text-[10px] text-gray-400 truncate leading-tight font-serif">
          {format.description}
        </p>
      </div>
    </button>
  );
};

interface OutputFormatSelectorProps {
  selected: OutputFormat[];
  onToggle: (id: OutputFormat) => void;
  disabled?: boolean;
}

const OutputFormatSelector: React.FC<OutputFormatSelectorProps> = ({ selected, onToggle, disabled }) => {
  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#74C69D]" />
          <h3 className="text-xs sm:text-sm font-bold text-white tracking-wide uppercase font-serif">
            Select Output Formats
          </h3>
        </div>
        {selected.length > 0 && (
          <span className="text-[11px] font-serif font-semibold px-2.5 py-0.5 rounded-md bg-[#163827] text-[#74C69D] border border-[#23573E]">
            {selected.length} Selected
          </span>
        )}
      </div>

      {/* Small Checkbox Grid: 2 cols on mobile, 4 cols on desktop */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
        {OUTPUT_FORMATS.map((format) => (
          <OutputFormatCard
            key={format.id}
            format={format}
            selected={selected.includes(format.id)}
            onToggle={onToggle}
            disabled={disabled}
          />
        ))}
      </div>
    </div>
  );
};

export { OutputFormatSelector, OUTPUT_FORMATS };
