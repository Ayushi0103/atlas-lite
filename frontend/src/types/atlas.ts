export type DocumentFile = {
  id: number;
  filename: string;
  file_type: string;
  file_path: string;
  source_url?: string | null;
  text_content?: string;
  short_summary?: string | null;
  detailed_summary?: string | null;
  key_concepts?: string | null;
  keywords?: string | null;
  suggested_questions?: string | null;
  created_at: string;
  updated_at: string;
};

export type SemanticResult = {
  type: string;
  id: number;
  filename?: string;
  title?: string;
  score: number;
  text: string;
};

export type RagSource = {
  id?: number;
  filename?: string;
  title?: string;
  text?: string;
  score?: number;
  source_url?: string;
};

export type AskResponse = {
  answer: string;
  sources?: RagSource[];
};

export type SearchState = {
  query: string;
  answer: string;
  sources: RagSource[];
  semanticResults: SemanticResult[];
};
