import api from './api';
import type { DesktopRuntimeStatus, SystemConfigPayload, SystemConfigResponse, WeiboConnectionTestResponse } from '@/types';

export async function fetchSystemConfig() {
  const response = await api.get<SystemConfigResponse>('/system/config');
  return response.data;
}

export async function saveSystemConfig(payload: SystemConfigPayload) {
  const response = await api.put<SystemConfigResponse>('/system/config', payload);
  return response.data;
}

export async function fetchRuntimeStatus() {
  const response = await api.get<DesktopRuntimeStatus>('/system/runtime');
  return response.data;
}

export async function testWeiboConnection() {
  const response = await api.get<WeiboConnectionTestResponse>('/system/weibo-connection-test');
  return response.data;
}
