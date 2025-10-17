export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: string;
  created_at: string;
}

export interface Dataset {
  id: number;
  name: string;
  description?: string | null;
  source: string;
  source_type: string;
  keyword?: string | null;
  user_id: number;
  created_at: string;
  updated_at: string | null;
  record_count?: number;
  total_records?: number;
}

export interface DataRecord {
  id: number;
  dataset_id: number;
  content: string;
  sentiment?: string;
  sentiment_label?: string;
  sentiment_score?: number;
  source_url?: string;
  author?: string;
  published_at?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface SentimentDistribution {
  positive: number;
  neutral: number;
  negative: number;
}

export interface TimeSeriesPoint {
  date: string;
  count: number;
  avg_sentiment: number;
}

export interface KeywordStat {
  word: string;
  count: number;
}

export interface AnalyticsData {
  total_records: number;
  sentiment_distribution: SentimentDistribution;
  avg_sentiment_score: number;
  time_series: TimeSeriesPoint[];
  top_keywords?: KeywordStat[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SpiderSourcesResponse {
  sources: string[];
  descriptions?: Record<string, string>;
}

export interface CrawlResponse {
  message: string;
  dataset_id: number;
  dataset_name: string;
  estimated_records: number;
}

export interface WordCloudResponse {
  image_base64: string;
  word_frequencies: Record<string, number>;
  total_words: number;
  unique_words: number;
  dataset: {
    id: number;
    name: string;
  };
}

export interface AIProvidersResponse {
  available: string[];
  descriptions?: Record<string, string>;
}

export type AIChatRole = 'system' | 'user' | 'assistant';

export interface AIChatMessage {
  role: AIChatRole;
  content: string;
}

export interface AIChatChunk {
  content?: string;
}

export interface AIReportChunk {
  type: string;
  content: string;
}
