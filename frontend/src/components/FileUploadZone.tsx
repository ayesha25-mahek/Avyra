import React, { useCallback, useRef, useState } from 'react';
import { Upload, X, FileText, Film, Image as ImageIcon, Sparkles } from 'lucide-react';
import { cn, formatFileSize, getFileIcon } from '@/lib/utils';

const ACCEPTED = '.pdf,.docx,.pptx,.txt,.csv,.png,.jpg,.jpeg,.webp,.mp4,.mov,.avi';
const MAX_FILES = 10;

function getTypeColor(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() ?? '';
  if (['pdf', 'docx', 'pptx', 'txt', 'csv'].includes(ext)) return 'text-[#00E599]';
  if (['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext)) return 'text-[#34D399]';
  if (['mp4', 'mov', 'avi'].includes(ext)) return 'text-[#06B6D4]';
  return 'text-gray-400';
}

interface FileUploadZoneProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
  disabled?: boolean;
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({ files, onFilesChange, disabled }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const addFiles = useCallback(
    (newFiles: FileList | null) => {
      if (!newFiles) return;
      const arr = Array.from(newFiles);
      const combined = [...files, ...arr].slice(0, MAX_FILES);
      onFilesChange(combined);
    },
    [files, onFilesChange]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (!disabled) addFiles(e.dataTransfer.files);
    },
    [addFiles, disabled]
  );

  const removeFile = (index: number) => {
    onFilesChange(files.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={cn(
          'relative rounded-lg border border-dashed p-6 text-center cursor-pointer transition-all duration-150 group',
          'overflow-hidden',
          dragging
            ? 'border-[#74C69D] bg-[#143324]'
            : 'border-[#1A402D] bg-[#0F261B] hover:border-[#265E43] hover:bg-[#122E20]',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED}
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
          disabled={disabled}
        />

        <div className={cn(
          'w-10 h-10 rounded-lg flex items-center justify-center mx-auto mb-2.5 transition-all duration-150 border',
          dragging
            ? 'bg-[#1B4330] border-[#74C69D]'
            : 'bg-[#1B4330] border-[#265E43] group-hover:border-[#2D6E4E]'
        )}>
          <Upload className={cn(
            'w-4 h-4 transition-transform',
            dragging ? 'text-[#74C69D]' : 'text-[#9DC4B0] group-hover:text-white'
          )} />
        </div>

        <p className="text-sm font-semibold text-white mb-1 tracking-tight font-serif">
          {dragging ? 'Drop files to ingest into neural pipeline' : 'Drag & drop source documents or media'}
        </p>
        <p className="text-xs text-[#9DC4B0] mb-2 font-serif">
          or click to browse local files
        </p>

        {/* Formats support pill tags */}
        <div className="flex flex-wrap items-center justify-center gap-1.5 text-[11px] font-serif text-[#B8D5C6]">
          <span className="px-2.5 py-0.5 rounded-md bg-[#163827] border border-[#23573E] flex items-center gap-1.5">
            <FileText className="w-3 h-3 text-[#74C69D]" /> PDF / DOCX / PPTX / TXT / CSV
          </span>
          <span className="px-2.5 py-0.5 rounded-md bg-[#163827] border border-[#23573E] flex items-center gap-1.5">
            <ImageIcon className="w-3 h-3 text-[#74C69D]" /> PNG / JPG / DWG / P&ID / WEBP
          </span>
          <span className="px-2.5 py-0.5 rounded-md bg-[#163827] border border-[#23573E] flex items-center gap-1.5">
            <Film className="w-3 h-3 text-[#74C69D]" /> MP4 / MOV
          </span>
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, i) => (
            <div
              key={`${file.name}-${i}`}
              className="flex items-center gap-3 px-3.5 py-2 rounded-md bg-[#050B07] border border-[#142B1F] group hover:border-[#204430] transition-colors"
            >
              <span className={cn('text-base leading-none', getTypeColor(file.name))}>
                {getFileIcon(file.name)}
              </span>
              <div className="flex-1 min-w-0 font-serif">
                <p className="text-xs font-semibold text-gray-200 truncate">{file.name}</p>
                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                  <span className="text-[10px] font-mono text-gray-400">{formatFileSize(file.size)}</span>
                  <span className="px-1.5 py-0.5 rounded bg-[#102B1E] border border-[#1E4D36] text-[9px] font-mono text-[#00E599] font-medium tracking-tight">
                    🔒 CONFIDENTIAL | PROCESSING: LOCAL | EXTERNAL TRANSFER: NONE
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                className="w-6 h-6 rounded-md flex items-center justify-center opacity-70 group-hover:opacity-100 transition-all hover:bg-red-500/20 text-gray-400 hover:text-red-400"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {files.length >= MAX_FILES && (
        <p className="text-xs font-mono text-amber-400 flex items-center gap-1">
          <Sparkles className="w-3 h-3" /> Ingestion capacity reached ({MAX_FILES}/{MAX_FILES} files).
        </p>
      )}
    </div>
  );
};

export { FileUploadZone };
