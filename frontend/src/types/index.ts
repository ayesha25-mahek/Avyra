export type OutputFormat =
  | 'video'
  | 'linkedin'
  | 'twitter'
  | 'presentation'
  | 'advisory'
  | 'executive_summary'
  | 'infographic'
  | 'article'
  | 'inspection_analysis'
  | 'defect_report'
  | 'technical_report'
  | 'drawing_analysis'
  | 'inspection_summary'
  | 'extracted_text'
  | 'document_summary'
  | 'equipment_tags'
  | 'data_summary'
  | 'abnormal_values'
  | 'analysis_workbook';

export interface OutputFormatMeta {
  id: OutputFormat;
  label: string;
  description: string;
  icon: string;
  estimatedTime: string;
  badge?: string;
}

export interface GenerationParams {
  prompt: string;
  files: File[];
  outputs: OutputFormat[];
  language: string;
  tone: string;
  target_audience: string;
  detail_level: string;
  provider?: string;
}

export interface RoutingMetadata {
  task_type: string;
  selected_model: string;
  provider: string;
  local: boolean;
  reason: string;
  fallback_used?: boolean;
  fallback?: string | null;
  vision_model?: string | null;
  external_calls: number;
  vram_mb?: number;
}

export interface ProgressEvent {
  stage: string;
  message: string;
  percent: number;
  current?: string;
  routing?: RoutingMetadata;
}

export interface ResultEvent {
  output_type: OutputFormat;
  status: 'success' | 'error' | 'not_implemented';
  content: string;
  download_url?: string;
  filename?: string;
  svg_content?: string;
  routing?: RoutingMetadata;
}

export interface GenerationState {
  status: 'idle' | 'generating' | 'complete' | 'error';
  progress: ProgressEvent | null;
  results: Partial<Record<OutputFormat, ResultEvent>>;
  error: string | null;
}

