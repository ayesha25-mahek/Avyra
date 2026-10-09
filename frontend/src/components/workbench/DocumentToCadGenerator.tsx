import React, { useState } from 'react';
import {
  Layers,
  Sparkles,
  Download,
  AlertCircle,
  Loader2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  FileText,
  FileCode,
  Plus,
  Trash2,
  Edit3,
  ShieldAlert,
  ArrowRight,
  Info,
} from 'lucide-react';
import { extractDrawingRequirements, generateCadDrawing, downloadFile } from '@/lib/api';

type CadStage = 'upload' | 'review' | 'result';
type DrawingType = 'pid_schematic' | 'process_flow' | '2d_mechanical' | 'equipment_arrangement';

interface ComponentItem {
  tag: string;
  name: string;
  type: string;
  dimensions: string;
  material: string;
  specifications: string;
  source_ref: string;
}

export const DocumentToCadGenerator: React.FC = () => {
  const [stage, setStage] = useState<CadStage>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [textInput, setTextInput] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Extracted & Editable Requirements
  const [title, setTitle] = useState('');
  const [drawingNumber, setDrawingNumber] = useState('');
  const [revision, setRevision] = useState('REV 0 (DRAFT)');
  const [projectUnit, setProjectUnit] = useState('Crude Fractionation Section');
  const [drawingType, setDrawingType] = useState<DrawingType>('pid_schematic');
  const [components, setComponents] = useState<ComponentItem[]>([]);
  const [dimensions, setDimensions] = useState<Array<{ label: string; value: string; source: string }>>([]);
  const [notes, setNotes] = useState<string[]>([]);

  // Generated Result
  const [cadResult, setCadResult] = useState<any | null>(null);
  const [zoom, setZoom] = useState(100);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleExtract = async () => {
    if (!file && !textInput.trim()) {
      setError('Please upload a source document or enter engineering specifications.');
      return;
    }

    setIsExtracting(true);
    setError(null);

    const formData = new FormData();
    if (file) formData.append('files', file);
    if (textInput.trim()) formData.append('text', textInput.trim());

    try {
      const res = await extractDrawingRequirements(formData);
      const req = res.requirements;
      setTitle(req.title || 'Equipment & Piping Schematic');
      setDrawingNumber(req.drawing_number || 'DWG-ENG-001');
      setRevision(req.revision || 'REV 0 (DRAFT)');
      setProjectUnit(req.project_unit || 'Operational Unit Fractionation Section');
      setDrawingType(req.drawing_type || 'pid_schematic');
      setComponents(req.components || []);
      setDimensions(req.dimensions || []);
      setNotes(req.notes || []);
      setStage('review');
    } catch (err: any) {
      setError(err.message || 'Failed to extract requirements from document.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);

    const payload = {
      title,
      drawing_number: drawingNumber,
      revision,
      project_unit: projectUnit,
      drawing_type: drawingType,
      components,
      dimensions,
      notes,
    };

    try {
      const res = await generateCadDrawing(payload);
      setCadResult(res);
      setStage('result');
      setZoom(100);
    } catch (err: any) {
      setError(err.message || 'Failed to generate CAD drawing.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Component Table Handlers
  const handleUpdateComponent = (index: number, field: keyof ComponentItem, value: string) => {
    const updated = [...components];
    updated[index] = { ...updated[index], [field]: value };
    setComponents(updated);
  };

  const handleAddComponent = () => {
    setComponents([
      ...components,
      {
        tag: `EQ-${components.length + 1}`,
        name: 'New Equipment',
        type: 'component',
        dimensions: 'Not specified',
        material: 'Not specified',
        specifications: 'Added by engineer',
        source_ref: 'Manual entry',
      },
    ]);
  };

  const handleRemoveComponent = (index: number) => {
    setComponents(components.filter((_, idx) => idx !== index));
  };

  return (
    <div className="space-y-6 font-serif text-gray-100">
      {/* Workflow Navigation Stepper */}
      <div className="flex items-center justify-between p-3 rounded-xl bg-[#091A11] border border-[#163827] text-xs font-mono">
        <div className="flex items-center gap-2 sm:gap-6 flex-wrap">
          <div className={`flex items-center gap-2 ${stage === 'upload' ? 'text-[#00E599] font-bold' : 'text-[#74C69D]'}`}>
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${stage === 'upload' ? 'bg-[#00E599] text-black font-bold' : 'bg-[#143324] text-[#74C69D]'}`}>
              1
            </span>
            <span>Upload Document</span>
          </div>
          <ArrowRight className="w-3.5 h-3.5 text-[#1E4D36] hidden sm:inline" />
          <div className={`flex items-center gap-2 ${stage === 'review' ? 'text-[#00E599] font-bold' : 'text-[#74C69D]'}`}>
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${stage === 'review' ? 'bg-[#00E599] text-black font-bold' : 'bg-[#143324] text-[#74C69D]'}`}>
              2
            </span>
            <span>Review Requirements</span>
          </div>
          <ArrowRight className="w-3.5 h-3.5 text-[#1E4D36] hidden sm:inline" />
          <div className={`flex items-center gap-2 ${stage === 'result' ? 'text-[#00E599] font-bold' : 'text-[#74C69D]'}`}>
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${stage === 'result' ? 'bg-[#00E599] text-black font-bold' : 'bg-[#143324] text-[#74C69D]'}`}>
              3
            </span>
            <span>Deterministic CAD &amp; DXF</span>
          </div>
        </div>

        <span className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-700/60 text-[#00E599] text-[10px] hidden md:inline">
          100% LOCAL VECTOR CAD
        </span>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-950/80 border border-rose-700 text-rose-200 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ─── STAGE 1: UPLOAD SOURCE DOCUMENT ───────────────────────────────── */}
      {stage === 'upload' && (
        <div className="p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-5">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#00E599]" />
              <span>1. Upload Source Technical Document or Specifications</span>
            </h3>
            <p className="text-xs text-[#8CBFA7] mt-1 font-sans">
              Upload PDF specifications, DOCX maintenance records, scanned image blueprints, or text specs. Avyara will extract explicit equipment tags, dimensions, and metallurgy without hallucination.
            </p>
          </div>

          <div className="border-2 border-dashed border-[#1E4D36] hover:border-[#00E599]/60 rounded-xl p-6 text-center bg-[#07130D] transition-colors relative">
            <input
              type="file"
              accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              disabled={isExtracting}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />
            <div className="w-12 h-12 rounded-xl bg-[#143324] border border-[#23573E] flex items-center justify-center mx-auto mb-3 text-[#00E599]">
              <Layers className="w-6 h-6" />
            </div>
            {file ? (
              <div className="space-y-1">
                <p className="text-sm font-bold text-[#00E599]">{file.name}</p>
                <p className="text-xs text-[#74C69D] font-mono">
                  {(file.size / 1024).toFixed(1)} KB • {file.type || 'document'}
                </p>
              </div>
            ) : (
              <div>
                <p className="text-xs font-semibold text-white">Click or drag &amp; drop document here</p>
                <p className="text-[11px] text-[#74C69D] mt-1 font-mono">PDF, DOCX, TXT, PNG, or JPG (up to 50MB)</p>
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-mono text-[#74C69D] mb-1 font-semibold">
              OR ENTER / PASTE ENGINEERING SPECIFICATIONS &amp; TAGS:
            </label>
            <textarea
              rows={4}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="e.g. Column C-101 (Height 42m, OD 3200mm, SS316). Pumps P-101A/B suction from Drum V-201 (4.5 bar). Discharge line 4-CS-101 to Overhead Condenser E-301."
              className="w-full bg-[#07130D] border border-[#1A402D] rounded-lg p-3 text-xs font-mono text-white placeholder-gray-500 focus:outline-none focus:border-[#00E599]"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleExtract}
              disabled={isExtracting || (!file && !textInput.trim())}
              className="px-5 py-2.5 rounded-lg bg-[#00E599] hover:bg-[#00c582] text-[#030604] font-bold text-xs font-mono flex items-center gap-2 disabled:opacity-40 transition-colors shadow-sm"
            >
              {isExtracting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#030604]" />
                  <span>Extracting Engineering Requirements…</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Extract Drawing Requirements</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ─── STAGE 2: REVIEW & APPROVE REQUIREMENTS ─────────────────────────── */}
      {stage === 'review' && (
        <div className="p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1A402D]">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-[#00E599]" />
                <span>2. Review &amp; Validate Extracted Drawing Requirements</span>
              </h3>
              <p className="text-xs text-[#8CBFA7] mt-0.5 font-sans">
                Verify components, dimensions, and specifications. Incomplete values are flagged as "Not specified".
              </p>
            </div>
            <button
              type="button"
              onClick={() => setStage('upload')}
              className="px-3 py-1.5 rounded bg-[#102B1E] border border-[#1E4D36] text-xs font-mono text-[#74C69D] hover:text-white"
            >
              ← Back to Upload
            </button>
          </div>

          {/* Drawing Metadata Header */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
            <div>
              <label className="block text-[#74C69D] text-[10px] mb-1">DRAWING TITLE</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-[#07130D] border border-[#1E4D36] rounded px-2.5 py-1.5 text-white focus:outline-none focus:border-[#00E599]"
              />
            </div>
            <div>
              <label className="block text-[#74C69D] text-[10px] mb-1">DRAWING NUMBER</label>
              <input
                type="text"
                value={drawingNumber}
                onChange={(e) => setDrawingNumber(e.target.value)}
                className="w-full bg-[#07130D] border border-[#1E4D36] rounded px-2.5 py-1.5 text-white focus:outline-none focus:border-[#00E599]"
              />
            </div>
            <div>
              <label className="block text-[#74C69D] text-[10px] mb-1">REVISION STATUS</label>
              <input
                type="text"
                value={revision}
                onChange={(e) => setRevision(e.target.value)}
                className="w-full bg-[#07130D] border border-[#1E4D36] rounded px-2.5 py-1.5 text-[#F59E0B] focus:outline-none focus:border-[#00E599]"
              />
            </div>
            <div>
              <label className="block text-[#74C69D] text-[10px] mb-1">PROJECT / PLANT SECTION</label>
              <input
                type="text"
                value={projectUnit}
                onChange={(e) => setProjectUnit(e.target.value)}
                className="w-full bg-[#07130D] border border-[#1E4D36] rounded px-2.5 py-1.5 text-white focus:outline-none focus:border-[#00E599]"
              />
            </div>
          </div>

          {/* Drawing Type Selector */}
          <div className="space-y-2">
            <label className="block text-xs font-mono text-[#74C69D] font-semibold">
              SELECT SUPPORTED DRAWING TYPE:
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              {[
                { id: 'pid_schematic', label: 'P&ID Schematic', sub: 'Piping & Instrumentation' },
                { id: 'process_flow', label: 'Process Flow (PFD)', sub: 'Main Process Streams' },
                { id: '2d_mechanical', label: '2D Mechanical Component', sub: 'Orthographic Section' },
                { id: 'equipment_arrangement', label: 'Equipment Arrangement', sub: 'Skid / Plant Top-View' },
              ].map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setDrawingType(t.id as DrawingType)}
                  className={`p-2.5 rounded-lg border text-left transition-colors flex flex-col gap-0.5 ${
                    drawingType === t.id
                      ? 'bg-[#183D2B] border-[#00E599] text-white shadow-sm'
                      : 'bg-[#091A11] border-[#1E4D36] text-[#B8D5C6] hover:bg-[#102B1E]'
                  }`}
                >
                  <span className="font-bold">{t.label}</span>
                  <span className="text-[10px] text-[#74C69D]">{t.sub}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Component Requirements Table */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono text-[#74C69D] font-semibold">
                EXTRACTED COMPONENT REQUIREMENTS ({components.length}):
              </label>
              <button
                type="button"
                onClick={handleAddComponent}
                className="px-2.5 py-1 rounded bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-xs font-mono text-[#00E599] flex items-center gap-1"
              >
                <Plus className="w-3 h-3" />
                <span>Add Component</span>
              </button>
            </div>

            <div className="overflow-x-auto border border-[#163827] rounded-lg">
              <table className="w-full text-left font-mono text-xs border-collapse">
                <thead>
                  <tr className="bg-[#0A1F14] border-b border-[#163827] text-[#74C69D] text-[11px]">
                    <th className="py-2 px-3">Tag</th>
                    <th className="py-2 px-3">Description</th>
                    <th className="py-2 px-3">Dimensions</th>
                    <th className="py-2 px-3">Metallurgy</th>
                    <th className="py-2 px-3">Source Provenance</th>
                    <th className="py-2 px-2 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#132C1F] text-white">
                  {components.map((comp, idx) => (
                    <tr key={idx} className="hover:bg-[#0A1F14]/60">
                      <td className="py-2 px-3">
                        <input
                          type="text"
                          value={comp.tag}
                          onChange={(e) => handleUpdateComponent(idx, 'tag', e.target.value)}
                          className="w-24 bg-[#07130D] border border-[#1E4D36] rounded px-1.5 py-1 text-[#00E599] font-bold text-xs"
                        />
                      </td>
                      <td className="py-2 px-3">
                        <input
                          type="text"
                          value={comp.name}
                          onChange={(e) => handleUpdateComponent(idx, 'name', e.target.value)}
                          className="w-36 bg-[#07130D] border border-[#1E4D36] rounded px-1.5 py-1 text-white text-xs"
                        />
                      </td>
                      <td className="py-2 px-3">
                        <input
                          type="text"
                          value={comp.dimensions}
                          onChange={(e) => handleUpdateComponent(idx, 'dimensions', e.target.value)}
                          className={`w-32 bg-[#07130D] border rounded px-1.5 py-1 text-xs ${
                            comp.dimensions === 'Not specified'
                              ? 'border-amber-600/80 text-amber-300'
                              : 'border-[#1E4D36] text-[#74C69D]'
                          }`}
                        />
                      </td>
                      <td className="py-2 px-3">
                        <input
                          type="text"
                          value={comp.material}
                          onChange={(e) => handleUpdateComponent(idx, 'material', e.target.value)}
                          className="w-28 bg-[#07130D] border border-[#1E4D36] rounded px-1.5 py-1 text-[#9DC4B0] text-xs"
                        />
                      </td>
                      <td className="py-2 px-3 text-[10px] text-[#6B937D] truncate max-w-[200px]" title={comp.source_ref}>
                        {comp.source_ref}
                      </td>
                      <td className="py-2 px-2 text-center">
                        <button
                          type="button"
                          onClick={() => handleRemoveComponent(idx)}
                          className="p-1 text-gray-500 hover:text-rose-400 transition-colors"
                          title="Remove component"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Engineering Disclaimer */}
          <div className="p-3.5 rounded-lg bg-[#0A1F14] border border-[#1E4D36] text-xs font-mono flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-[#F59E0B] shrink-0 mt-0.5" />
            <div className="space-y-1 text-[#B8D5C6]">
              <span className="font-bold text-[#F59E0B]">PRELIMINARY / DRAFT NOTICE:</span>
              <p className="text-[11px] leading-relaxed">
                Deterministic CAD drawing outputs are marked as draft schematics. Dimensions marked "Not specified" must be confirmed via vendor datasheets. Do not use for physical construction without licensed Professional Engineer (PE) sign-off.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleGenerate}
              disabled={isGenerating || components.length === 0}
              className="px-6 py-2.5 rounded-lg bg-[#00E599] hover:bg-[#00c582] text-[#030604] font-bold text-xs font-mono flex items-center gap-2 transition-colors shadow-sm"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#030604]" />
                  <span>Synthesizing Deterministic CAD (SVG &amp; DXF)…</span>
                </>
              ) : (
                <>
                  <Layers className="w-4 h-4" />
                  <span>Generate Deterministic CAD Drawing</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ─── STAGE 3: INTERACTIVE PREVIEW & DOWNLOAD DELIVERABLES ───────────── */}
      {stage === 'result' && cadResult && (
        <div className="space-y-4">
          {/* Action & Metric Toolbar */}
          <div className="p-4 rounded-xl bg-[#0E2419] border border-[#1A402D] flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700/60 text-[10px] font-mono font-bold">
                  PRELIMINARY / DRAFT
                </span>
                <span className="text-sm font-bold text-white font-mono">{cadResult.title}</span>
              </div>
              <p className="text-xs text-[#74C69D] font-mono">
                {cadResult.drawing_number} • {cadResult.revision} • {cadResult.metrics?.components_count || 0} Components ({cadResult.metrics?.specified_dimensions_count || 0} Specified)
              </p>
            </div>

            {/* Controls: Zoom & Downloads */}
            <div className="flex items-center gap-2 flex-wrap">
              {/* Zoom Buttons */}
              <div className="flex items-center rounded-lg bg-[#07130D] border border-[#1E4D36] p-0.5 text-xs font-mono">
                <button
                  type="button"
                  onClick={() => setZoom(Math.max(50, zoom - 20))}
                  className="px-2 py-1 text-[#74C69D] hover:text-white"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="px-2 text-[11px] text-[#00E599] font-bold">{zoom}%</span>
                <button
                  type="button"
                  onClick={() => setZoom(Math.min(250, zoom + 20))}
                  className="px-2 py-1 text-[#74C69D] hover:text-white"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => setZoom(100)}
                  className="px-2 py-1 text-[#74C69D] hover:text-white text-[10px]"
                  title="Reset 100%"
                >
                  <RotateCcw className="w-3 h-3" />
                </button>
              </div>

              {/* Download SVG */}
              <button
                type="button"
                onClick={() => downloadFile(cadResult.download_urls.svg, cadResult.svg_filename)}
                className="px-3.5 py-1.5 rounded-lg bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-[#00E599] hover:text-white font-mono text-xs flex items-center gap-1.5 transition-colors font-bold"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Vector SVG</span>
              </button>

              {/* Download DXF */}
              <button
                type="button"
                onClick={() => downloadFile(cadResult.download_urls.dxf, cadResult.dxf_filename)}
                className="px-3.5 py-1.5 rounded-lg bg-[#00E599] hover:bg-[#00c582] text-[#030604] font-mono text-xs flex items-center gap-1.5 transition-colors font-bold shadow-sm"
              >
                <FileCode className="w-3.5 h-3.5" />
                <span>AutoCAD DXF</span>
              </button>

              {/* Revise Requirements Button */}
              <button
                type="button"
                onClick={() => setStage('review')}
                className="px-3 py-1.5 rounded-lg bg-[#091A11] border border-[#1E4D36] text-[#B8D5C6] hover:text-white font-mono text-xs flex items-center gap-1"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>Revise</span>
              </button>
            </div>
          </div>

          {/* Interactive SVG Canvas Container with Zoom & Scroll */}
          <div className="border border-[#1A402D] rounded-xl bg-[#030805] overflow-auto max-h-[680px] p-4 flex items-center justify-center relative shadow-inner">
            <div
              style={{
                transform: `scale(${zoom / 100})`,
                transformOrigin: 'top center',
                transition: 'transform 0.15s ease-out',
                width: '100%',
                maxWidth: '1200px',
              }}
              dangerouslySetInnerHTML={{ __html: cadResult.svg_content }}
            />
          </div>

          {/* Provenance & Compliance Strip */}
          <div className="p-3 rounded-lg bg-[#0A1F14] border border-[#1E4D36] text-xs font-mono text-[#8CBFA7] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Info className="w-3.5 h-3.5 text-[#00E599]" />
              <span>Standard: ISO 10628 / API 610 • Layering: AutoCAD R12/2000 standard</span>
            </div>
            <span className="text-[11px] text-[#74C69D]">
              External calls: 0 • Zero cloud egress • Localhost generation
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
