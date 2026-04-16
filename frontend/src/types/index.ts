export interface User {
    id: number;
    username: string;
    email: string;
    is_active: boolean;
    is_superuser: boolean;
    created_at: string;
}

export interface Task {
    id: number;
    task_type: 'weibo' | 'douyin';
    keyword: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    total_data: number;
    progress: number;
    error_message?: string;
    started_at?: string;
    completed_at?: string;
    created_at: string;
    config?: Record<string, any>;
}

export interface SentimentAnalysis {
    score: number;
    label: 'positive' | 'negative' | 'neutral';
}

export interface AdvancedStats {
    total_count: number;
    total_likes: number;
    total_comments: number;
    total_shares: number;
    total_interaction?: number;
    sentiment_distribution: Record<string, number>;
    gender_distribution: Record<string, number>;
    province_distribution: Record<string, number>;
    platform_distribution: Record<string, number>;
}

export interface RiskAssessment {
    level: '高' | '中' | '低';
    score: number;
    factors: string[];
    details: {
        sentiment_score: number;
        interaction_score: number;
        speed_score: number;
        negative_ratio: number;
        avg_interaction: number;
        recent_ratio: number;
    };
}

export interface Topic {
    topic_id: number;
    keywords: string[];
    doc_count: number;
    doc_ratio: number;
}

export interface KeySpreader {
    user_name: string;
    user_id: string;
    post_count: number;
    total_likes: number;
    total_comments: number;
    total_shares: number;
    followers: number;
    avg_interaction: number;
    influence_score: number;
}

export interface SystemConfigPayload {
    app_name?: string | null;
    ai_model_type?: string | null;
    ai_api_key?: string | null;
    ai_base_url?: string | null;
    ai_model_id?: string | null;
    weibo_cookie?: string | null;
    douyin_cookie?: string | null;
    crawler_max_page?: number | null;
    crawler_timeout?: number | null;
    crawler_delay?: number | null;
    data_dir?: string | null;
    static_dir?: string | null;
    wordcloud_dir?: string | null;
    reports_dir?: string | null;
    upload_dir?: string | null;
    database_path?: string | null;
    log_dir?: string | null;
}

export interface SystemConfigResponse {
    config: SystemConfigPayload;
    active_runtime: Record<string, unknown>;
    config_path: string;
    restart_required: boolean;
}

export interface DesktopRuntimeStatus {
    desktop_mode: boolean;
    api_host: string;
    api_port: number;
    app_data_dir: string;
    static_dir: string;
    reports_dir: string;
    wordcloud_dir: string;
    database_path: string;
    config_path: string;
    log_dir: string;
}

export interface WeiboConnectionTestResponse {
    success: boolean;
    mode: 'cookie' | 'visitor';
    message: string;
    sample_count: number;
}

export interface SpiderTaskSummary {
    id: number;
    task_type: 'weibo' | 'douyin';
    keyword: string;
    status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
    progress: number;
    error_message?: string | null;
    created_at: string;
    started_at?: string | null;
    completed_at?: string | null;
}

export interface SpiderTaskListResponse {
    total: number;
    tasks: SpiderTaskSummary[];
}

export interface SpiderDataItem {
    id: number;
    content?: string | null;
    user_name?: string | null;
    author?: string | null;
    publish_time?: string | null;
    like_count?: number;
    comment_count?: number;
    share_count?: number;
    sentiment_label?: 'positive' | 'negative' | 'neutral' | null;
    url?: string | null;
}

export interface SpiderDataListResponse {
    total: number;
    data: SpiderDataItem[];
}

export interface HotTopic {
    title: string;
    source?: string | null;
    link?: string | null;
    publish_date?: string | null;
    cover_image?: string | null;
}

export interface RealtimeMonitoringItem {
    author: string;
    content: string;
    Link?: string | null;
    link?: string | null;
    url?: string | null;
    authorUrl?: string | null;
}

export interface PageChartDataResponse {
    heatmap_data: Array<Record<string, unknown>>;
    sentiment_data: Record<string, number>;
    gender_data: Record<string, number>;
}

export interface PageRealtimeDataResponse {
    total: number;
    sentiment_distribution: {
        positive: number;
        negative: number;
        neutral: number;
    };
    data: Array<{
        id: number;
        author: string;
        content: string;
        publish_time?: string | null;
        likes: number;
        comments: number;
        shares: number;
        sentiment: 'positive' | 'negative' | 'neutral';
        sentiment_score?: number | null;
        url?: string | null;
    }>;
}

export interface ManualContentResponse {
    title: string;
    markdown: string;
    source_path: string;
    updated_at?: string | null;
}

export interface CaseSummary {
    id: number;
    keyword: string;
    type: 'weibo' | 'douyin';
    created_at?: string | null;
    completed_at?: string | null;
}

export interface CaseListResponse {
    total: number;
    cases: CaseSummary[];
}

export interface CaseDetailResponse {
    id: number;
    keyword: string;
    task_type: 'weibo' | 'douyin';
    status: string;
    created_at?: string | null;
    started_at?: string | null;
    completed_at?: string | null;
    statistics: AdvancedStats & {
        total_interaction?: number;
    };
    risk: RiskAssessment;
    topics: Topic[];
    spreaders: KeySpreader[];
    recent_items: Array<{
        id: number;
        author: string;
        content: string;
        publish_time?: string | null;
        likes: number;
        comments: number;
        shares: number;
        sentiment: 'positive' | 'negative' | 'neutral';
        url?: string | null;
    }>;
}

// ===== 定时采集任务 =====
export interface ScheduledJob {
  id: number;
  keyword: string;
  task_type: 'weibo' | 'douyin';
  max_page: number;
  interval_minutes: number;
  use_smart_schedule: boolean;
  is_active: boolean;
  last_run_at?: string | null;
  next_run_at?: string | null;
  run_count: number;
  last_error?: string | null;
  last_task_id?: number | null;
  created_at: string;
  updated_at?: string | null;
}

export interface ScheduledJobListResponse {
  total: number;
  jobs: ScheduledJob[];
}

export interface ScheduledJobCreate {
  keyword: string;
  task_type: 'weibo' | 'douyin';
  max_page: number;
  use_smart_schedule: boolean;
  interval_minutes: number;
}

export interface ScheduledJobUpdate {
  interval_minutes?: number;
  max_page?: number;
  is_active?: boolean;
  use_smart_schedule?: boolean;
}

export interface SmartPhaseInfo {
  start: string;        // "06:00"
  end: string;          // "09:00"
  interval_minutes: number;
  label: string;        // "早间高峰"
  emoji: string;        // "🌅"
}

export interface SchedulerStatus {
  is_running: boolean;
  active_jobs: number;
  total_jobs: number;
  message: string;
  current_phase?: string;
  current_phase_emoji?: string;
  current_interval?: number;
  smart_phases?: SmartPhaseInfo[];
}
