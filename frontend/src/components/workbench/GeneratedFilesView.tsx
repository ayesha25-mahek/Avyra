import React, { useEffect, useState } from 'react';
import {
  FolderArchive,
  Download,
  FileText,
  Presentation,
  FileCode,
  Search,
  RefreshCw,
  HardDrive,
  FileSpreadsheet,
  File,
} from 'lucide-react';
import { fetchGeneratedFiles, type GeneratedFileInfo } from '@/lib/api';

function getFileIcon(ext: string) {
  switch (ext.toLowerCase()) {
    case 'docx':
    case 'doc':
    case 'txt':
    case 'md':
      return FileText;
    case 'pptx':
    case 'ppt':
      return Presentation;
    case 'py':
    case 'json':
      return FileCode;
    case 'csv':
    case 'xlsx':
      return FileSpreadsheet;
    default:
      return File;
  }
}

export const GeneratedFilesView: React.FC = () => {
  const [files, setFiles] = useState<GeneratedFileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const loadFiles = async () => {
    setLoading(true);
    try {
      const data = await fetchGeneratedFiles();
      setFiles(data);
    } catch {
      // quiet fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const filtered = files.filter(
    (f) =>
      f.filename.toLowerCase().includes(search.toLowerCase()) ||
      f.extension.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 font-serif text-gray-100 max-w-5xl mx-auto">
      {/* Page Heading */}
      <div className="pb-4 border-b border-[#1A402D]">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#143324] border border-[#23573E] text-[#00E599]">
            MODULE 09
          </span>
          <span className="text-xs text-[#74C69D] font-mono">Deliverables Catalog</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          On-Premise Deliverables &amp; Output Files
        </h1>
        <p className="text-xs sm:text-sm text-[#B8D5C6] mt-1">
          Historical archive of all synthesized statutory reports (.docx), slide presentations (.pptx), Python sandbox scripts, and technical advisories stored locally.
        </p>
      </div>

      {/* Search & Actions Bar */}
      <div className="p-4 rounded-xl bg-[#0E2419] border border-[#1A402D] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-[#74C69D]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search deliverables by name or extension (e.g. .docx, .pptx)…"
            className="w-full pl-10 pr-4 py-2 rounded-lg bg-[#08170F] border border-[#1E4D36] text-xs sm:text-sm text-gray-200 focus:outline-none focus:border-[#00E599] font-serif"
          />
        </div>

        <button
          type="button"
          onClick={loadFiles}
          disabled={loading}
          className="px-3.5 py-2 rounded-lg bg-[#143324] hover:bg-[#1A402D] border border-[#23573E] text-xs font-mono text-[#B8D5C6] hover:text-white flex items-center justify-center gap-2 transition-colors shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Files</span>
        </button>
      </div>

      {/* Files List */}
      <div className="p-5 sm:p-6 rounded-xl bg-[#0A1D13] border border-[#1A402D] space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#1A402D]">
          <div className="flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-[#00E599]" />
            <h3 className="text-sm font-bold text-white">Local Output Directory ({filtered.length} files)</h3>
          </div>
          <span className="text-[11px] font-mono text-[#74C69D]">
            Path: ./output/*
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-[#74C69D] text-xs font-mono">
            Loading local deliverables…
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-[#6B8F7B] space-y-2">
            <FolderArchive className="w-10 h-10 mx-auto opacity-40 text-[#00E599]" />
            <p className="text-xs font-mono">No deliverable files found matching criteria</p>
          </div>
        ) : (
          <div className="divide-y divide-[#163827]">
            {filtered.map((f, i) => {
              const Icon = getFileIcon(f.extension);
              const dateStr = f.modified_at
                ? new Date(f.modified_at * 1000).toLocaleString()
                : 'Recent';

              return (
                <div key={i} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs hover:bg-[#06140D] px-2 rounded-lg transition-colors">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-[#143324] border border-[#23573E] flex items-center justify-center text-[#00E599] shrink-0">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-mono text-white text-xs truncate font-medium">
                        {f.filename}
                      </div>
                      <div className="text-[10px] text-[#74C69D] font-mono truncate">
                        {f.relative_path}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 pt-1 sm:pt-0">
                    <span className="text-[11px] font-mono text-[#82A895]">
                      {(f.size_bytes / 1024).toFixed(1)} KB
                    </span>
                    <span className="text-[10px] font-mono text-[#587E6B] hidden md:inline">
                      {dateStr}
                    </span>
                    <a
                      href={f.download_url}
                      download={f.filename}
                      className="px-3 py-1.5 rounded-lg bg-[#00E599] hover:bg-[#00C070] text-black font-bold font-mono text-xs flex items-center gap-1.5 transition-colors"
                    >
                      <Download className="w-3 h-3" />
                      <span>Download</span>
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
