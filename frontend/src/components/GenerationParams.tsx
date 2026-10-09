import React, { useState } from 'react';
import { ChevronDown, ChevronUp, SlidersHorizontal } from 'lucide-react';
import { Select } from '@/components/ui/select';

const LANGUAGES = [
  { value: 'English', label: 'English (US/UK)' },
  { value: 'Spanish', label: 'Spanish' },
  { value: 'French', label: 'French' },
  { value: 'German', label: 'German' },
  { value: 'Arabic', label: 'Arabic' },
  { value: 'Hindi', label: 'Hindi' },
  { value: 'Portuguese', label: 'Portuguese' },
  { value: 'Chinese', label: 'Chinese (Mandarin)' },
  { value: 'Japanese', label: 'Japanese' },
  { value: 'Korean', label: 'Korean' },
];

const TONES = [
  { value: 'Professional', label: 'Executive & Authoritative' },
  { value: 'Conversational', label: 'Engaging & Conversational' },
  { value: 'Formal', label: 'Formal / Institutional' },
  { value: 'Technical', label: 'Deep Technical & Analytical' },
  { value: 'Inspiring', label: 'Visionary & Inspiring' },
  { value: 'Urgent', label: 'High Urgency / Action-Driven' },
  { value: 'Casual', label: 'Casual & Direct' },
  { value: 'Friendly', label: 'Approachable & Warm' },
];

const AUDIENCES = [
  { value: 'General', label: 'General Enterprise Audience' },
  { value: 'Executives', label: 'C-Suite (CIO / CISO / CMO)' },
  { value: 'Technical', label: 'Engineering & SecOps Teams' },
  { value: 'Marketing', label: 'GTM & Growth Marketing' },
  { value: 'Investors', label: 'Venture & Board Investors' },
  { value: 'Students', label: 'Academic & Educational' },
];

const DETAIL_LEVELS = [
  { value: 'Brief', label: 'Precision Brief (High-Level Summary)' },
  { value: 'Standard', label: 'Standard Enterprise Depth' },
  { value: 'Detailed', label: 'Deep Tactical Breakdown' },
  { value: 'Comprehensive', label: 'Comprehensive 360° Package' },
];

const PROVIDERS = [
  { value: 'auto', label: 'Existing Providers (Gemini / Groq Cascade)' },
  { value: 'ollama', label: 'Local Ollama (qwen2.5:7b Sovereign)' },
];

interface GenerationParamsProps {
  provider?: string;
  language: string;
  tone: string;
  targetAudience: string;
  detailLevel: string;
  onChange: (field: string, value: string) => void;
  disabled?: boolean;
}

const GenerationParams: React.FC<GenerationParamsProps> = ({
  provider = 'auto', language, tone, targetAudience, detailLevel, onChange,
}) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-[#1A402D] bg-[#0F261B] overflow-hidden transition-all duration-150">
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-[#122E20] hover:bg-[#163827] transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-md bg-[#1B4330] flex items-center justify-center border border-[#265E43]">
            <SlidersHorizontal className="w-3 h-3 text-[#74C69D]" />
          </div>
          <span className="text-xs sm:text-sm font-semibold text-white font-serif tracking-wide">
            Execution Parameters
          </span>
          <span className="text-xs font-serif text-[#9DC4B0] hidden sm:inline-block border-l border-[#1E4D36] pl-2.5">
            {provider === 'ollama' ? '⚡ Local Ollama (qwen2.5:7b)' : '☁️ Existing Providers'} · {language} · {tone}
          </span>
        </div>
        <div className="flex items-center gap-2 text-[#9DC4B0] font-serif">
          <span className="text-xs text-[#74C69D] font-medium">
            {expanded ? 'Hide Config' : 'Customize Options'}
          </span>
          {expanded
            ? <ChevronUp className="w-3.5 h-3.5 text-[#74C69D]" />
            : <ChevronDown className="w-3.5 h-3.5 text-[#9DC4B0]" />
          }
        </div>
      </button>

      {/* Content */}
      {expanded && (
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-3.5 bg-[#0F261B] border-t border-[#1A402D] animate-in fade-in duration-150">
          <div className="sm:col-span-2">
            <Select
              label="AI Inference Engine / Provider"
              value={provider}
              onValueChange={(v) => onChange('provider', v)}
              options={PROVIDERS}
            />
          </div>
          <Select
            label="Target Language"
            value={language}
            onValueChange={(v) => onChange('language', v)}
            options={LANGUAGES}
          />
          <Select
            label="Voice & Persona Tone"
            value={tone}
            onValueChange={(v) => onChange('tone', v)}
            options={TONES}
          />
          <Select
            label="Target Audience Persona"
            value={targetAudience}
            onValueChange={(v) => onChange('target_audience', v)}
            options={AUDIENCES}
          />
          <Select
            label="Detail & Output Depth"
            value={detailLevel}
            onValueChange={(v) => onChange('detail_level', v)}
            options={DETAIL_LEVELS}
          />
        </div>
      )}
    </div>
  );
};

export { GenerationParams };
