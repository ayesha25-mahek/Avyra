import React, { useState } from 'react';
import {
  FileSpreadsheet,
  Sparkles,
  Download,
  AlertCircle,
  Loader2,
  Table,
  Plus,
  Trash2,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { extractSpreadsheetFromDoc, generateSpreadsheetWorkbook, downloadFile } from '@/lib/api';

type Stage = 'upload' | 'review' | 'result';

interface SheetSchema {
  sheet_name: string;
  description: string;
  columns: string[];
  rows: (string | number)[][];
  formulas?: Record<string, string>;
}

export const DocumentToExcelGenerator: React.FC = () => {
  const [stage, setStage] = useState<Stage>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [textInput, setTextInput] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Review state
  const [workbookTitle, setWorkbookTitle] = useState('Industrial Asset & Inspection Register');
  const [sheets, setSheets] = useState<SheetSchema[]>([]);
  const [activeSheetIndex, setActiveSheetIndex] = useState(0);

  // Result state
  const [result, setResult] = useState<any | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleExtract = async () => {
    if (!file && !textInput.trim()) {
      setError('Please upload a technical document or paste source text.');
      return;
    }

    setIsExtracting(true);
    setError(null);

    const formData = new FormData();
    if (file) formData.append('files', file);
    if (textInput.trim()) formData.append('text', textInput.trim());

    try {
      const resp = await extractSpreadsheetFromDoc(formData);
      if (resp.status === 'success' && resp.proposed_schema) {
        const schema = resp.proposed_schema;
        setWorkbookTitle(schema.workbook_title || 'Industrial Asset & Operations Register');
        setSheets(schema.sheets || []);
        setActiveSheetIndex(0);
        setStage('review');
      } else {
        setError('Failed to extract structured spreadsheet schema from input.');
      }
    } catch (err: any) {
      setError(err.message || 'Error communicating with document extraction service.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleGenerate = async () => {
    if (!sheets.length) {
      setError('At least one sheet is required to generate a workbook.');
      return;
    }

    setIsGenerating(true);
    setError(null);

    const payload = {
      workbook_title: workbookTitle,
      source_filename: file?.name || 'document',
      sheets: sheets,
    };

    try {
      const resp = await generateSpreadsheetWorkbook(payload);
      if (resp.status === 'success') {
        setResult(resp);
        setStage('result');
      } else {
        setError('Workbook generation failed.');
      }
    } catch (err: any) {
      setError(err.message || 'Error generating Excel workbook.');
    } finally {
      setIsGenerating(false);
    }
  };

  const currentSheet = sheets[activeSheetIndex];

  const updateCell = (rowIndex: number, colIndex: number, val: string) => {
    const newSheets = [...sheets];
    const targetSheet = { ...newSheets[activeSheetIndex] };
    const newRows = targetSheet.rows.map((row) => [...row]);
    if (newRows[rowIndex]) {
      newRows[rowIndex][colIndex] = val;
      targetSheet.rows = newRows;
      newSheets[activeSheetIndex] = targetSheet;
      setSheets(newSheets);
    }
  };

  const addRow = () => {
    const newSheets = [...sheets];
    const targetSheet = { ...newSheets[activeSheetIndex] };
    const newRow = targetSheet.columns.map(() => '');
    targetSheet.rows = [...targetSheet.rows, newRow];
    newSheets[activeSheetIndex] = targetSheet;
    setSheets(newSheets);
  };

  const deleteRow = (rowIndex: number) => {
    const newSheets = [...sheets];
    const targetSheet = { ...newSheets[activeSheetIndex] };
    targetSheet.rows = targetSheet.rows.filter((_, idx) => idx !== rowIndex);
    newSheets[activeSheetIndex] = targetSheet;
    setSheets(newSheets);
  };

  return (
    <div className="space-y-6">
      {/* Stepper Header */}
      <div className="flex items-center justify-between p-4 rounded-xl bg-[#091A11] border border-[#1A402D]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center text-[#00E599]">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">Document-to-Excel Generator</h2>
            <p className="text-xs text-[#74C69D] font-mono">
              Extracts inventories, maintenance logs, and readings into genuine multi-sheet XLSX workbooks.
            </p>
          </div>
        </div>

        {/* Stepper indicator */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span
            className={`px-2.5 py-1 rounded-md border ${
              stage === 'upload'
                ? 'bg-[#00E599]/20 text-[#00E599] border-[#00E599]/40 font-bold'
                : 'bg-[#0E2419] text-[#74C69D] border-[#1A402D]'
            }`}
          >
            1. Document Input
          </span>
          <span className="text-[#23573E]">→</span>
          <span
            className={`px-2.5 py-1 rounded-md border ${
              stage === 'review'
                ? 'bg-[#00E599]/20 text-[#00E599] border-[#00E599]/40 font-bold'
                : 'bg-[#0E2419] text-[#74C69D] border-[#1A402D]'
            }`}
          >
            2. Review Schema &amp; Rows
          </span>
          <span className="text-[#23573E]">→</span>
          <span
            className={`px-2.5 py-1 rounded-md border ${
              stage === 'result'
                ? 'bg-[#00E599]/20 text-[#00E599] border-[#00E599]/40 font-bold'
                : 'bg-[#0E2419] text-[#74C69D] border-[#1A402D]'
            }`}
          >
            3. Download XLSX
          </span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-start gap-3 font-mono">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* STAGE 1: UPLOAD */}
      {stage === 'upload' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-5 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
            <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider font-mono">
              Upload Source Document (PDF, DOCX, TXT, Image)
            </label>
            <div className="border border-dashed border-[#1E4D36] hover:border-[#00E599]/60 rounded-xl p-6 text-center bg-[#091A11] transition-colors relative">
              <input
                type="file"
                accept=".pdf,.docx,.txt,.csv,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                disabled={isExtracting}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
              />
              <div className="w-12 h-12 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center mx-auto mb-3 text-[#00E599]">
                <Table className="w-6 h-6" />
              </div>
              {file ? (
                <div>
                  <p className="text-xs font-bold text-[#00E599]">{file.name}</p>
                  <p className="text-[10px] text-[#74C69D] font-mono mt-1">
                    {(file.size / 1024).toFixed(1)} KB • Ready for schema extraction
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-xs font-semibold text-white">Click or drag industrial document</p>
                  <p className="text-[11px] text-[#74C69D] mt-1 font-mono">
                    Audit reports, equipment manuals, test logs, vendor datasheets
                  </p>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider font-mono">
                Or Paste Technical Text
              </label>
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Paste equipment specifications, inspection logs, or calibration readings here..."
                rows={5}
                className="w-full bg-[#07170E] border border-[#1E4D36] focus:border-[#00E599] rounded-lg p-3 text-xs text-white placeholder-gray-500 font-mono focus:outline-none"
              />
            </div>

            <button
              onClick={handleExtract}
              disabled={isExtracting || (!file && !textInput.trim())}
              className="w-full py-3 px-4 bg-[#00E599] hover:bg-[#00c885] disabled:bg-[#143324] disabled:text-gray-500 text-black font-bold rounded-lg text-xs uppercase tracking-wider transition-colors flex items-center justify-center gap-2 font-mono"
            >
              {isExtracting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Extracting Table Schema &amp; Rows…
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Extract Multi-Sheet Schema
                </>
              )}
            </button>
          </div>

          {/* Guidelines card */}
          <div className="p-5 rounded-xl bg-[#091A11] border border-[#1A402D] space-y-4">
            <h3 className="text-xs font-bold text-[#00E599] font-mono uppercase tracking-wider flex items-center gap-2">
              <Info className="w-4 h-4" />
              Document-to-Spreadsheet Pipeline Features
            </h3>
            <ul className="space-y-3 text-xs text-[#B8D5C6]">
              <li className="flex items-start gap-2">
                <span className="text-[#00E599] mt-0.5">•</span>
                <span>
                  <strong>Multi-Sheet Architecture:</strong> Segregates parsed information into distinct sheets (Equipment Master, Maintenance Schedule, Operational Readings).
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00E599] mt-0.5">•</span>
                <span>
                  <strong>Human-in-the-Loop Review:</strong> Inspect and edit extracted rows, columns, and sheet names before the final Excel file is compiled.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00E599] mt-0.5">•</span>
                <span>
                  <strong>Native Excel Formulas:</strong> Automatically embeds summary calculation formulas (<code className="text-[#00E599] font-mono">=AVERAGE()</code>, <code className="text-[#00E599] font-mono">=MAX()</code>, <code className="text-[#00E599] font-mono">=COUNTA()</code>) for numerical columns.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00E599] mt-0.5">•</span>
                <span>
                  <strong>Strict Local Execution:</strong> Processed entirely locally on the Avyara server with zero external cloud or data egress.
                </span>
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* STAGE 2: REVIEW & EDIT SCHEMA */}
      {stage === 'review' && currentSheet && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-[#0E2419] border border-[#1A402D] flex flex-wrap items-center justify-between gap-4">
            <div className="flex-1 min-w-[260px]">
              <label className="block text-[10px] text-[#74C69D] font-mono uppercase mb-1">
                Workbook Title
              </label>
              <input
                type="text"
                value={workbookTitle}
                onChange={(e) => setWorkbookTitle(e.target.value)}
                className="w-full bg-[#07170E] border border-[#1E4D36] focus:border-[#00E599] rounded px-3 py-1.5 text-xs text-white font-mono"
              />
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setStage('upload')}
                className="px-3 py-1.5 rounded-lg border border-[#1E4D36] text-xs font-mono text-[#9DC4B0] hover:bg-[#143324]"
              >
                ← Back to Upload
              </button>
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="px-4 py-1.5 bg-[#00E599] hover:bg-[#00c885] disabled:bg-[#143324] text-black font-bold rounded-lg text-xs font-mono flex items-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Generating XLSX…
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    Approve &amp; Generate Excel Workbook
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Sheet Selector Tabs */}
          <div className="flex items-center gap-2 border-b border-[#1A402D] pb-2">
            <span className="text-xs text-[#74C69D] font-mono uppercase px-2">Sheets:</span>
            {sheets.map((s, idx) => (
              <button
                key={idx}
                onClick={() => setActiveSheetIndex(idx)}
                className={`px-3 py-1.5 rounded-t-lg text-xs font-mono transition-colors border-t border-x ${
                  activeSheetIndex === idx
                    ? 'bg-[#143324] text-[#00E599] border-[#23573E] font-bold'
                    : 'bg-[#091A11] text-[#9DC4B0] border-[#1A402D] hover:bg-[#0E2419]'
                }`}
              >
                {s.sheet_name} ({s.rows.length} rows)
              </button>
            ))}
          </div>

          {/* Current Sheet Content & Table */}
          <div className="p-4 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-white font-mono">{currentSheet.sheet_name}</h4>
                <p className="text-xs text-[#74C69D]">{currentSheet.description}</p>
              </div>
              <button
                onClick={addRow}
                className="px-3 py-1 bg-[#143324] hover:bg-[#1E4D36] text-[#00E599] border border-[#23573E] rounded text-xs font-mono flex items-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Row
              </button>
            </div>

            {/* Editable Table */}
            <div className="overflow-x-auto border border-[#1A402D] rounded-lg">
              <table className="w-full text-xs font-mono text-left">
                <thead className="bg-[#091A11] text-[#00E599] border-b border-[#1A402D]">
                  <tr>
                    <th className="py-2.5 px-3 w-10 text-center text-[#74C69D]">#</th>
                    {currentSheet.columns.map((col, colIdx) => (
                      <th key={colIdx} className="py-2.5 px-3 font-semibold uppercase tracking-wider">
                        {col}
                      </th>
                    ))}
                    <th className="py-2.5 px-3 w-12 text-center text-[#74C69D]">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#143324]">
                  {currentSheet.rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-[#143324]/40">
                      <td className="py-2 px-3 text-center text-[#74C69D] font-mono text-[11px]">
                        {rIdx + 1}
                      </td>
                      {currentSheet.columns.map((_, cIdx) => (
                        <td key={cIdx} className="py-1 px-2">
                          <input
                            type="text"
                            value={String(row[cIdx] ?? '')}
                            onChange={(e) => updateCell(rIdx, cIdx, e.target.value)}
                            className="w-full bg-[#07170E] border border-transparent hover:border-[#1E4D36] focus:border-[#00E599] rounded px-2 py-1 text-xs text-white font-mono focus:outline-none"
                          />
                        </td>
                      ))}
                      <td className="py-1 px-2 text-center">
                        <button
                          onClick={() => deleteRow(rIdx)}
                          className="p-1 text-red-400 hover:text-red-300 rounded hover:bg-red-950/40"
                          title="Delete row"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {currentSheet.rows.length === 0 && (
                    <tr>
                      <td
                        colSpan={currentSheet.columns.length + 2}
                        className="py-6 text-center text-[#74C69D] text-xs font-mono"
                      >
                        No rows currently in this sheet. Click &quot;Add Row&quot; above to create one.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* STAGE 3: RESULT & DOWNLOAD */}
      {stage === 'result' && result && (
        <div className="p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#1A402D]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center text-[#00E599]">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white font-mono">
                  {result.workbook_title} Generated Successfully
                </h3>
                <p className="text-xs text-[#74C69D] font-mono">
                  Standard publication-grade multi-sheet XLSX compiled with native Excel formula logic.
                </p>
              </div>
            </div>

            <button
              onClick={() => downloadFile(result.download_url, result.filename)}
              className="px-5 py-2.5 bg-[#00E599] hover:bg-[#00c885] text-black font-bold rounded-lg text-xs font-mono uppercase tracking-wider flex items-center gap-2 shadow-lg shadow-[#00E599]/10"
            >
              <Download className="w-4 h-4" />
              Download {result.filename}
            </button>
          </div>

          {/* Details summary */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-[#091A11] border border-[#1A402D]">
              <span className="text-[10px] text-[#74C69D] font-mono uppercase block">Sheets Generated</span>
              <span className="text-lg font-bold text-white font-mono">{result.sheet_count} Sheets</span>
            </div>
            <div className="p-4 rounded-lg bg-[#091A11] border border-[#1A402D]">
              <span className="text-[10px] text-[#74C69D] font-mono uppercase block">Total Data Rows</span>
              <span className="text-lg font-bold text-white font-mono">{result.total_rows} Rows</span>
            </div>
            <div className="p-4 rounded-lg bg-[#091A11] border border-[#1A402D]">
              <span className="text-[10px] text-[#74C69D] font-mono uppercase block">File Format</span>
              <span className="text-lg font-bold text-[#00E599] font-mono">Microsoft Excel (.XLSX)</span>
            </div>
          </div>

          {/* Sheet listing */}
          <div className="space-y-2">
            <span className="text-xs font-bold text-[#9DC4B0] font-mono uppercase">Worksheet Layout:</span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {result.sheets?.map((s: any, idx: number) => (
                <div key={idx} className="p-3 rounded-lg bg-[#091A11] border border-[#1E4D36] flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-white font-mono">{s.name}</span>
                    <p className="text-[10px] text-[#74C69D] font-mono">{s.columns} columns</p>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-[#143324] text-[#00E599] border border-[#23573E]">
                    {s.rows} rows
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3 pt-4 border-t border-[#1A402D]">
            <button
              onClick={() => setStage('review')}
              className="px-4 py-2 rounded-lg border border-[#1E4D36] text-xs font-mono text-[#9DC4B0] hover:bg-[#143324]"
            >
              Modify Schema &amp; Re-generate
            </button>
            <button
              onClick={() => {
                setFile(null);
                setTextInput('');
                setStage('upload');
              }}
              className="px-4 py-2 rounded-lg border border-[#1E4D36] text-xs font-mono text-[#74C69D] hover:bg-[#143324]"
            >
              Process Another Document
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
