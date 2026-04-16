import api from './api';
import type {
  ScheduledJob,
  ScheduledJobCreate,
  ScheduledJobListResponse,
  ScheduledJobUpdate,
  SchedulerStatus,
} from '@/types';

export async function fetchSchedulerStatus(): Promise<SchedulerStatus> {
  const res = await api.get<SchedulerStatus>('/scheduler/status');
  return res.data;
}

export async function fetchScheduledJobs(params?: {
  page?: number;
  page_size?: number;
  is_active?: boolean;
}): Promise<ScheduledJobListResponse> {
  const search = new URLSearchParams();
  if (params?.page) search.set('page', String(params.page));
  if (params?.page_size) search.set('page_size', String(params.page_size));
  if (params?.is_active !== undefined) search.set('is_active', String(params.is_active));
  const qs = search.size ? `?${search}` : '';
  const res = await api.get<ScheduledJobListResponse>(`/scheduler/jobs${qs}`);
  return res.data;
}

export async function fetchScheduledJob(jobId: number): Promise<ScheduledJob> {
  const res = await api.get<ScheduledJob>(`/scheduler/jobs/${jobId}`);
  return res.data;
}

export async function createScheduledJob(payload: ScheduledJobCreate): Promise<ScheduledJob> {
  const res = await api.post<ScheduledJob>('/scheduler/jobs', payload);
  return res.data;
}

export async function updateScheduledJob(
  jobId: number,
  payload: ScheduledJobUpdate,
): Promise<ScheduledJob> {
  const res = await api.patch<ScheduledJob>(`/scheduler/jobs/${jobId}`, payload);
  return res.data;
}

export async function deleteScheduledJob(jobId: number): Promise<void> {
  await api.delete(`/scheduler/jobs/${jobId}`);
}

export async function triggerScheduledJobNow(jobId: number): Promise<ScheduledJob> {
  const res = await api.post<ScheduledJob>(`/scheduler/jobs/${jobId}/trigger`);
  return res.data;
}
