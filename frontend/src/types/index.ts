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
  description?: string;
  source_type: string;
  user_id: number;
  created_at: string;
  updated_at: string;
  record_count?: number;
}

export interface DataRecord {
  id: number;
  dataset_id: number;
  content: string;
  sentiment?: string;
  sentiment_score?: number;
  source_url?: string;
  author?: string;
  published_at?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface AnalyticsData {
  total_records: number;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  avg_sentiment_score: number;
  time_series: Array<{
    date: string;
    count: number;
    avg_sentiment: number;
  }>;
  top_keywords?: Array<{
    word: string;
    count: number;
  }>;
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
