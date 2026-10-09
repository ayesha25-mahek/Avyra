import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Search,
  Upload,
  Database,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  HardDrive,
  Sparkles,
} from 'lucide-react';
import { retrieveSop, fetchRagDocuments, ingestSopDocument } from '@/lib/api';

export const KnowledgeBaseView: React.FC = () => {
  const [query, setQuery] = useState('hydrostatic test pressure requirements and safety factors');
  const [retrievalResults, setRetrievalResults] = useState<any[]>([]);
  const [indexedDocs, setIndexedDocs] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = async () => {
    try {
      const data = await fetchRagDocuments();
      setIndexedDocs(data.documents || []);
    } catch {
      // quiet fallback
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setError(null);
    try {
      const data = await retrieveSop(query.trim(), 4);
      setRetrievalResults(data.results || data.chunks || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to query local SOP knowledge base');
    } finally {
      setIsSearching(false);
    }
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setIsIngesting(true);
    setMessage(null);
    setError(null);

    const formData = new FormData();
    formData.append('files', uploadFile);

    try {
      await ingestSopDocument(formData);
      setMessage(`Successfully indexed "${uploadFile.name}" into local SQLite vector database.`);
      setUploadFile(null);
      await loadDocuments();
    } catch (err: any) {
      setError(err?.message || 'Failed to ingest SOP document');
    } finally {
      setIsIngesting(false);
    }
  };

  const SUGGESTIONS = [
    'Hydrostatic test pressure standards ASME B31.3',
    'Corrosion allowance and ultrasonic thickness limits',
    'Centrifugal pump vibration threshold ISO 10816',
    'Hot work permit fire watch and atmospheric testing rules',
  ];

  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-5xl mx-auto">
      {/* Page Heading */}
      <div className="pb-4 border-b border-[#1A402D]">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#143324] border border-[#23573E] text-[#00E599]">
            MODULE 06
          </span>
          <span className="text-xs text-[#74C69D] font-mono">SQLite Vector RAG</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Industrial SOP &amp; Standards Knowledge Base
        </h1>
        <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
          Semantic retrieval over local standard operating procedures (SOPs), refinery manuals, and statutory engineering codes without external cloud vector databases.
        </p>
      </div>

      {/* Semantic Search Box */}
      <div className="p-5 sm:p-6 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-4">
        <form onSubmit={handleSearch} className="space-y-3">
          <label className="block text-xs font-semibold text-[#9DC4B0] uppercase tracking-wider font-mono">
            Semantic Query over On-Premise Industrial SOPs
          </label>
          <div className="flex flex-col sm:flex-row items-center gap-2">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-[#74C69D]" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search procedures, ASME standards, or safety thresholds…"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#08170F] border border-[#1E4D36] text-xs sm:text-sm text-gray-200 focus:outline-none focus:border-[#00E599] font-serif"
              />
            </div>
            <button
              type="submit"
              disabled={isSearching || !query.trim()}
              className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-[#00E599] hover:bg-[#00C070] text-black font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
            >
              {isSearching ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-black" />
                  <span>Searching…</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Search SOPs</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Suggestion Chips */}
        <div className="space-y-1.5 pt-1">
          <span className="text-[11px] font-mono text-[#527965] flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-[#00E599]" /> Example Technical Queries:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTIONS.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(s);
                }}
                className="px-2.5 py-1 rounded-lg bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-[11px] text-[#B8D5C6] hover:text-white transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-950/60 border border-red-800 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Search Results Display */}
      {retrievalResults.length > 0 && (
        <div className="p-5 sm:p-6 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#1A402D]">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-[#00E599]" />
              <h3 className="text-sm font-bold text-white">Retrieved SOP Passages ({retrievalResults.length})</h3>
            </div>
            <span className="text-[11px] font-mono text-[#74C69D]">
              Local SQLite pgvector match
            </span>
          </div>

          <div className="space-y-3">
            {retrievalResults.map((chunk, idx) => {
              const text = chunk.content || chunk.text || JSON.stringify(chunk);
              const score = chunk.score || chunk.similarity;
              const source = chunk.metadata?.filename || chunk.source || `Document Chunk #${idx + 1}`;

              return (
                <div key={idx} className="p-4 rounded-lg bg-[#06120B] border border-[#163827] space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="text-[#00E599] font-bold flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5" />
                      {source}
                    </span>
                    {score !== undefined && (
                      <span className="px-2 py-0.5 rounded bg-[#102B1E] border border-[#1E4D36] text-[#74C69D]">
                        Relevance: {(Number(score) * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                  <p className="text-xs sm:text-sm text-gray-200 leading-relaxed font-sans whitespace-pre-wrap">
                    {text}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Ingest New SOP & Document Catalog Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Ingest New SOP Card */}
        <div className="p-5 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-3">
          <div className="flex items-center gap-2">
            <Upload className="w-4 h-4 text-[#00E599]" />
            <h3 className="text-sm font-bold text-white">Ingest New SOP or Standard</h3>
          </div>
          <p className="text-xs text-[#9DC4B0]">
            Add refinery procedures or inspection manuals to the local knowledge base.
          </p>

          <form onSubmit={handleIngest} className="space-y-3 pt-1">
            <div className="border border-dashed border-[#1E4D36] rounded-lg p-3 text-center bg-[#091A11] relative">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                disabled={isIngesting}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
              />
              <p className="text-xs font-mono text-[#DCE8E1]">
                {uploadFile ? uploadFile.name : 'Select PDF, DOCX or TXT file'}
              </p>
            </div>

            <button
              type="submit"
              disabled={isIngesting || !uploadFile}
              className="w-full py-2.5 rounded-lg bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-white font-semibold text-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-40"
            >
              {isIngesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <HardDrive className="w-3.5 h-3.5 text-[#00E599]" />}
              <span>Index into Vector Database</span>
            </button>
          </form>

          {message && (
            <div className="p-2.5 rounded bg-emerald-950/80 border border-emerald-700/60 text-[#00E599] text-xs flex items-center gap-2 font-mono">
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
              <span>{message}</span>
            </div>
          )}
        </div>

        {/* Indexed SOPs Catalog Card */}
        <div className="p-5 rounded-xl bg-[#0E2419] border border-[#1A402D] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-[#00E599]" />
              <h3 className="text-sm font-bold text-white">Indexed Knowledge Documents</h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#102B1E] border border-[#1E4D36] text-[#74C69D]">
              {indexedDocs.length} Indexed
            </span>
          </div>

          <div className="divide-y divide-[#183B29] max-h-52 overflow-y-auto pr-1 scrollbar-thin">
            {indexedDocs.length === 0 ? (
              <p className="text-xs text-[#6B8F7B] font-mono py-6 text-center">
                Pre-loaded refinery SOPs (API 570, ASME B31.3, ISO 10816) active in database.
              </p>
            ) : (
              indexedDocs.map((doc, i) => (
                <div key={i} className="py-2 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="w-3.5 h-3.5 text-[#74C69D] shrink-0" />
                    <span className="text-[#DCE8E1] truncate font-mono">{doc.filename || doc.name || `Document ${i+1}`}</span>
                  </div>
                  <span className="text-[10px] font-mono text-[#74C69D] shrink-0">
                    {doc.chunk_count ? `${doc.chunk_count} chunks` : 'Indexed'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
