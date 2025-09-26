export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  file_type: string;
  document_type: string;
  status: string;
  content_text?: string;
  content_json?: any;
  metadata?: any;
  created_at: string;
  updated_at?: string;
}

export type DocumentType = 'standard' | 'target';

export interface UploadResponse {
  document_id: string;
  filename: string;
  document_type: string;
  status: string;
  file_size: number;
}

export interface ComparisonRequest {
  standard_document_id: string;
  target_document_id: string;
  enable_ai_review?: boolean;
}

export interface ComparisonResponse {
  comparison_id: string;
  // 新的PDF URL字段
  standard_pdf_url?: string;
  target_pdf_url?: string;
  page_count?: number;
  // 保留向后兼容的图片字段
  standard_images: string[];
  target_images: string[];
  diff_list: any[];
  summary: {
    total_differences: number;
    additions: number;
    deletions: number;
    modifications: number;
    moves: number;
  };
  ai_review_enabled?: boolean;
}

export interface DiffReview {
  id: string;
  comparison_id: string;
  diff_id: string;
  risk_level: string;
  compliance: string;
  review_suggestions: string;
  raw_ai_response: string;
  created_at: string;
}

export interface DiffItem {
  element_id: string;
  type: string;
  status: 'ADD' | 'DELETE' | 'MODIFY' | 'MOVE';
  page_index: number;
  elements: string;
  diff: Array<Array<{
    text: string;
    page_index: number;
    line_index: number;
    doc_index: number;
    char_polygons: number[][];
    polygon: number[];
    sub_info: Array<{
      page_id: number;
      sub_polygons: number[];
      sub_text_index: {
        start_index: number;
        length: number;
      };
    }>;
    sub_type: string;
  }>>;
  full_sentence?: {
    sentence: string;
    standard_text: string;
    target_text: string;
  };
  diff_text?: string;
  diff_start?: number;
  diff_length?: number;
  old_text?: string;
  new_text?: string;
}
