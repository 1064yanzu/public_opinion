import api from './api';
import type {
  CaseDetailResponse,
  CaseListResponse,
  HotTopic,
  ManualContentResponse,
  PageChartDataResponse,
  PageRealtimeDataResponse,
  RealtimeMonitoringItem,
  SpiderDataListResponse,
  SpiderTaskListResponse,
  SpiderTaskSummary,
} from '@/types';

export async function fetchSpiderTasks(params?: { page_size?: number; status?: string }) {
  const search = new URLSearchParams();
  if (params?.page_size) {
    search.set('page_size', String(params.page_size));
  }
  if (params?.status) {
    search.set('status', params.status);
  }
  const response = await api.get<SpiderTaskListResponse>(`/spider/tasks${search.size ? `?${search}` : ''}`);
  return response.data;
}

export async function fetchSpiderTask(taskId: number) {
  const response = await api.get<SpiderTaskSummary>(`/spider/tasks/${taskId}`);
  return response.data;
}

export async function deleteSpiderTask(taskId: number): Promise<void> {
  await api.delete(`/spider/tasks/${taskId}`);
}

export async function createSpiderTask(payload: {
  task_type: 'weibo' | 'douyin';
  keyword: string;
  max_page: number;
  async_mode: boolean;
}) {
  const response = await api.post<SpiderTaskSummary>('/spider/search', payload);
  return response.data;
}

export async function fetchSpiderData(platform: 'weibo' | 'douyin', taskId?: number) {
  const search = new URLSearchParams({ page_size: '50' });
  if (taskId) {
    search.set('task_id', String(taskId));
  }
  const response = await api.get<SpiderDataListResponse>(`/spider/${platform}?${search.toString()}`);
  return response.data;
}

export async function fetchBigdataChartData() {
  const response = await api.get<PageChartDataResponse>('/page/chart-data');
  return response.data;
}

export async function fetchHotTopics(limit = 8) {
  const response = await api.get<HotTopic[]>(`/page/hot-topics?limit=${limit}`);
  return response.data;
}

export async function fetchRealtimeMonitoring(limit = 12) {
  const response = await api.get<RealtimeMonitoringItem[]>(`/page/realtime-monitoring?limit=${limit}`);
  return response.data;
}

export async function fetchRealtimeData(keyword?: string) {
  const search = new URLSearchParams({ limit: '20' });
  if (keyword?.trim()) {
    search.set('keyword', keyword.trim());
  }
  const response = await api.get<PageRealtimeDataResponse>(`/page/realtime-data?${search.toString()}`);
  return response.data;
}

export async function fetchManualContent() {
  const response = await api.get<ManualContentResponse>('/page/manual-content');
  return response.data;
}

export async function fetchCases(page = 1, pageSize = 12) {
  const response = await api.get<CaseListResponse>(`/page/cases?page=${page}&page_size=${pageSize}`);
  return response.data;
}

export async function fetchCaseDetail(caseId: number) {
  const response = await api.get<CaseDetailResponse>(`/page/cases/${caseId}`);
  return response.data;
}

export async function generateWordcloud() {
  const response = await api.get<{ image_url: string; word_freq: Record<string, number>; message: string }>('/page/wordcloud');
  return response.data;
}

export async function forceGenerateWordcloud(payload: { keyword?: string; task_id?: number } = {}) {
  const response = await api.post<{ image_url: string; word_freq: Record<string, number>; message: string }>('/page/wordcloud', payload);
  return response.data;
}
