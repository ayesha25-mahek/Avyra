import React, { useState } from 'react';
import {
  Terminal,
  Play,
  AlertCircle,
  Loader2,
  Copy,
  Check,
} from 'lucide-react';
import { executeSandbox } from '@/lib/api';

const SAMPLE_CODES = [
  {
    title: 'ASME B31.3 Pipe Stress & Minimum Wall Thickness',
    code: `# ASME B31.3 Process Piping - Minimum Wall Thickness Calculation
import math

P = 15.0       # Internal design pressure (MPa)
D = 219.1      # Outside diameter (mm, 8" NPS)
S = 138.0      # Allowable stress for ASTM A106 Gr B (MPa)
E = 1.0        # Quality factor (seamless)
W = 1.0        # Weld joint strength reduction factor
Y = 0.4        # Temperature coefficient (< 482 C)
c = 3.0        # Corrosion allowance (mm)

# Formula: tm = (P * D) / (2 * (S * E * W + P * Y)) + c
numerator = P * D
denominator = 2 * (S * E * W + P * Y)
t_pressure = numerator / denominator
t_min = t_pressure + c

print("========================================")
print("ASME B31.3 MECHANICAL CALCULATION REPORT")
print("========================================")
print(f"Design Pressure (P):        {P:.2f} MPa")
print(f"Outside Diameter (D):       {D:.2f} mm")
print(f"Allowable Stress (S):       {S:.2f} MPa")
print(f"Pressure Wall Thickness:    {t_pressure:.3f} mm")
print(f"Corrosion Allowance:        {c:.2f} mm")
print(f"Mandatory Minimum Wall (tm):{t_min:.3f} mm")
print("----------------------------------------")
if t_min <= 8.18: # Schedule 40 WT
    print("STATUS: Schedule 40 (8.18mm) SUFFICIENT")
else:
    print("STATUS: UPGRADE TO SCHEDULE 80 REQUIRED")
print("VERIFICATION: 100% Deterministic Local Sandbox")
`,
  },
  {
    title: 'Hydrostatic Test Pressure Calculation',
    code: `# API 570 / ASME Section VIII Hydrostatic Test Calculation
MAWP = 4.2      # Maximum Allowable Working Pressure (MPa)
Stest = 145.0   # Allowable stress at test temperature (MPa)
Sdesign = 120.0 # Allowable stress at design temperature (MPa)

# Hydrostatic Test Formula: P_test = 1.5 * MAWP * (Stest / Sdesign)
stress_ratio = Stest / Sdesign
P_hydro = 1.5 * MAWP * stress_ratio

print("============================================")
print("STATUTORY HYDROSTATIC TEST PRESSURE SPEC")
print("============================================")
print(f"Operating MAWP:             {MAWP:.2f} MPa")
print(f"Test/Design Stress Ratio:   {stress_ratio:.4f}")
print(f"Required Hydro Test Pressure: {P_hydro:.2f} MPa ({P_hydro * 10:.1f} bar)")
print("HOLD TIME: 30 minutes minimum inspection hold")
print("SAFETY MARGIN: Compliant with statutory PSU norms")
`,
  },
];

export const CodingSandboxView: React.FC = () => {
  const [mode, setMode] = useState<'code' | 'task'>('code');
  const [code, setCode] = useState(SAMPLE_CODES[0].code);
  const [taskPrompt, setTaskPrompt] = useState(
    'Generate and run a Python script to calculate heat exchanger log-mean temperature difference (LMTD) for counter-flow: T_hot_in=150C, T_hot_out=90C, T_cold_in=25C, T_cold_out=65C.'
  );
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleRun = async () => {
    setIsRunning(true);
    setOutput(null);
    setError(null);

    try {
      if (mode === 'code') {
        const res = await executeSandbox({ code });
        setOutput(res);
      } else {
        const res = await executeSandbox({ task: taskPrompt });
        setOutput(res);
      }
    } catch (err: any) {
      setError(err?.message || 'Sandbox execution failed');
    } finally {
      setIsRunning(false);
    }
  };

  const handleCopyOutput = async () => {
    if (!output) return;
    const text = output.stdout || JSON.stringify(output, null, 2);
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-5xl mx-auto">
      {/* Page Heading */}
      <div className="pb-4 border-b border-[#1A402D]">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#143324] border border-[#23573E] text-[#00E599]">
            MODULE 07
          </span>
          <span className="text-xs text-[#74C69D] font-mono">Isolated Python 3.11</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Local Python Engineering Sandbox
        </h1>
        <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
          Execute deterministic engineering calculations, mechanical stresses, and data scripts inside a secure local sandbox with zero cloud connectivity.
        </p>
      </div>

      {/* Editor & Task Card */}
      <div className="p-5 sm:p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
        {/* Mode Switcher */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#1A402D]">
          <div className="flex items-center gap-1.5 bg-[#08170F] p-1 rounded-lg border border-[#1E4D36]">
            <button
              type="button"
              onClick={() => setMode('code')}
              className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                mode === 'code' ? 'bg-[#183D2B] text-white font-bold' : 'text-[#82A895] hover:text-white'
              }`}
            >
              Direct Python Code
            </button>
            <button
              type="button"
              onClick={() => setMode('task')}
              className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                mode === 'task' ? 'bg-[#183D2B] text-white font-bold' : 'text-[#82A895] hover:text-white'
              }`}
            >
              Autonomous Task Runner
            </button>
          </div>

          {mode === 'code' && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {SAMPLE_CODES.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setCode(s.code)}
                  className="px-2.5 py-1 rounded text-[11px] font-mono bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-[#B8D5C6] hover:text-white transition-colors truncate max-w-xs"
                >
                  {s.title.split(' ')[0]} Calc
                </button>
              ))}
            </div>
          )}
        </div>

        {mode === 'code' ? (
          <div>
            <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
              Python Script Editor (Standard Library + Math + CSV)
            </label>
            <textarea
              rows={12}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              disabled={isRunning}
              className="w-full font-mono text-xs text-[#00E599] bg-[#050F09] border border-[#1E4D36] p-4 rounded-xl focus:outline-none focus:border-[#00E599] leading-relaxed resize-y"
            />
          </div>
        ) : (
          <div>
            <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider mb-2 font-mono">
              Engineering Calculation Task Directive
            </label>
            <textarea
              rows={4}
              value={taskPrompt}
              onChange={(e) => setTaskPrompt(e.target.value)}
              disabled={isRunning}
              className="w-full text-xs sm:text-sm text-gray-200 bg-[#050F09] border border-[#1E4D36] p-4 rounded-xl focus:outline-none focus:border-[#00E599] leading-relaxed resize-y font-serif"
            />
          </div>
        )}

        {/* Execution Button */}
        <div className="flex items-center gap-3 pt-1">
          <button
            type="button"
            onClick={handleRun}
            disabled={isRunning}
            className="flex-1 py-3 px-5 rounded-xl bg-[#00E599] hover:bg-[#00C070] text-black font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 shadow-md"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-black" />
                <span>Executing in Local Sandbox…</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-black" />
                <span>Execute Script in Local Sandbox</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-950/60 border border-red-800 text-red-300 text-xs flex items-center gap-2 font-mono">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Terminal Output Console */}
      {output && (
        <div className="p-5 sm:p-6 rounded-xl bg-[#06120B] border border-[#163827] space-y-3 font-mono">
          <div className="flex items-center justify-between pb-2 border-b border-[#163827]">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[#00E599]" />
              <span className="text-xs font-bold text-white uppercase">
                Sandbox Execution Console Output
              </span>
            </div>

            <div className="flex items-center gap-3 text-[11px]">
              <span className={`px-2 py-0.5 rounded border ${
                output.success !== false && (output.exit_code === 0 || output.exit_code === undefined)
                  ? 'bg-emerald-950 text-[#00E599] border-emerald-700/60'
                  : 'bg-red-950 text-red-400 border-red-800'
              }`}>
                Exit Code: {output.exit_code ?? 0}
              </span>

              {output.execution_time_ms && (
                <span className="text-[#74C69D]">
                  {output.execution_time_ms.toFixed(1)} ms
                </span>
              )}

              <button
                type="button"
                onClick={handleCopyOutput}
                className="px-2 py-0.5 rounded bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-[#B8D5C6] hover:text-white flex items-center gap-1"
              >
                {copied ? <Check className="w-3 h-3 text-[#00E599]" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-[#030805] border border-[#0F261B] text-xs text-[#00E599] leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto scrollbar-thin">
            {output.stdout || output.output || output.result || JSON.stringify(output, null, 2)}
            {output.stderr && (
              <div className="text-red-400 mt-2 border-t border-red-950 pt-2">
                [STDERR]: {output.stderr}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
