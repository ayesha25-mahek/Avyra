import React from 'react';
import { Cpu, Zap, FileSearch, CheckCircle2, Sparkles, Loader2, Activity, Server } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { ProgressEvent, ResultEvent, OutputFormat } from '@/types';
import { OUTPUT_FORMATS } from '@/components/OutputFormatSelector';

const STAGE_ICONS: Record<string, React.FC<{ className?: string }>> = {
  reading: FileSearch,
  routing: Server,
  analyzing: Cpu,
  preparing: Sparkles,
  generating: Zap,
  done: CheckCircle2,
};

interface ProgressPanelProps {
  progress: ProgressEvent | null;
  completedResults: Partial<Record<OutputFormat, ResultEvent>>;
  selectedOutputs: OutputFormat[];
}

const ProgressPanel: React.FC<ProgressPanelProps> = ({ progress, completedResults, selectedOutputs }) => {
  const stage = progress?.stage ?? 'analyzing';
  const StageIcon = STAGE_ICONS[stage] ?? Zap;
  const percent = progress?.percent ?? 0;
  const message = progress?.message ?? 'Autonomous Pipeline Active…';

  return (
    <div className="relative rounded-xl border border-[#1A402D] bg-[#0F261B] p-5 space-y-4 font-serif">
      {/* Stage indicator & Telemetry */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#1B4330] border border-[#265E43] flex items-center justify-center text-[#74C69D]">
            <StageIcon className="w-4 h-4 text-[#74C69D]" />
          </div>
          <div>
            <p className="text-xs sm:text-sm font-semibold text-white font-serif tracking-tight">{message}</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#74C69D]" />
              <span className="text-[10px] font-mono text-[#9DC4B0] tracking-wider uppercase">
                {stage === 'done' ? 'ALL DELIVERABLES ASSEMBLED' : `AVYRA PLAYBOOK // ${stage.toUpperCase()}`}
              </span>
            </div>
          </div>
        </div>

        <div className="text-right hidden sm:block">
          <span className="text-lg font-mono font-bold text-[#74C69D]">
            {percent}%
          </span>
        </div>
      </div>

      {/* High-tech Progress bar */}
      <div className="space-y-1.5">
        <Progress value={percent} />
        <div className="flex justify-between text-[11px] font-mono text-[#9DC4B0]">
          <span className="flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-[#74C69D]" /> Neural Inference Stream
          </span>
          <span className="text-white font-bold">{percent}% COMPLETED</span>
        </div>
      </div>

      {/* Autonomous Local Model Router Telemetry Card */}
      {progress?.routing && (
        <div className="rounded-lg border border-[#23573E] bg-[#0A1A12] p-3 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-[#74C69D] uppercase tracking-wider flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-[#74C69D]" /> Autonomous Model Router
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#163827] text-[#74C69D] border border-[#265E43] font-bold">
              {progress.routing.local ? '100% SOVEREIGN / LOCAL' : 'CLOUD CASCADE'}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 border-t border-[#163827] text-[11px] font-mono">
            <div>
              <span className="text-[#688A78] block text-[9px] uppercase">Task</span>
              <span className="text-white font-semibold">
                {progress.routing.task_type.replace(/_/g, ' ').toUpperCase()}
              </span>
            </div>
            <div>
              <span className="text-[#688A78] block text-[9px] uppercase">Selected Model</span>
              <span className="text-[#74C69D] font-bold">{progress.routing.selected_model}</span>
            </div>
            <div>
              <span className="text-[#688A78] block text-[9px] uppercase">Provider</span>
              <span className="text-white">{progress.routing.provider.toUpperCase()}</span>
            </div>
            <div>
              <span className="text-[#688A78] block text-[9px] uppercase">External Calls</span>
              <span className="text-white font-bold">{progress.routing.external_calls}</span>
            </div>
          </div>
          <p className="text-[10px] font-serif text-[#9DC4B0] italic pt-0.5">
            ↳ Reason: {progress.routing.reason}
            {progress.routing.fallback_used && progress.routing.fallback && (
              <span className="text-[#74C69D] ml-1.5 font-mono not-italic font-bold">
                [{progress.routing.fallback.toUpperCase()}]
              </span>
            )}
          </p>
        </div>
      )}

      {/* Neural Pipeline Output Stage Status List */}
      {selectedOutputs.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-[#1A402D]">
          <div className="flex items-center justify-between text-[10px] font-mono text-[#9DC4B0] uppercase tracking-widest px-1">
            <span>Target Pipeline Task</span>
            <span>Execution Status</span>
          </div>

          {selectedOutputs.map((outputId) => {
            const meta = OUTPUT_FORMATS.find((f) => f.id === outputId);
            const result = completedResults[outputId];
            const isDone = !!result;
            const isError = result?.status === 'error';
            const isCurrent = progress?.current === outputId;

            return (
              <div
                key={outputId}
                className={cn(
                  'flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-serif transition-colors duration-150',
                  isDone && !isError ? 'bg-[#163827] border border-[#23573E] text-[#74C69D]' :
                  isError ? 'bg-red-950/30 border border-red-800/40 text-red-300' :
                  isCurrent ? 'bg-[#143324] border border-[#2D6E4E] text-white' :
                  'bg-[#0C1F16] border border-[#1A402D] text-[#9DC4B0]'
                )}
              >
                <div className="flex items-center gap-2.5">
                  {isDone && !isError ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#74C69D] shrink-0" />
                  ) : isCurrent ? (
                    <Loader2 className="w-3.5 h-3.5 text-[#74C69D] animate-spin shrink-0" />
                  ) : (
                    <div className={cn('w-3.5 h-3.5 rounded-md border flex items-center justify-center text-[9px] shrink-0',
                      isError ? 'border-red-400 text-red-400' : 'border-[#265E43] text-[#9DC4B0]'
                    )}>
                      •
                    </div>
                  )}
                  <span className={cn('font-semibold font-serif text-xs',
                    isDone && !isError ? 'text-white' :
                    isCurrent ? 'text-white' : 'text-[#9DC4B0]'
                  )}>
                    {meta?.label ?? outputId}
                  </span>
                </div>

                <div className="text-[11px] font-mono">
                  {isError && <span className="text-red-400 font-bold">FAILED</span>}
                  {isDone && !isError && <span className="text-[#74C69D] font-bold">READY</span>}
                  {isCurrent && <span className="text-[#74C69D] font-bold animate-pulse">PROCESSING…</span>}
                  {!isDone && !isCurrent && !isError && <span className="text-[#688A78]">QUEUED</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export { ProgressPanel };
