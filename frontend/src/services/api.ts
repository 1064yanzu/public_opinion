import axios, { type AxiosError, type AxiosRequestConfig, type AxiosResponse } from 'axios';
import { getAppRuntime } from './runtime';

const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

export function configureApiClient() {
    const runtime = getAppRuntime();
    api.defaults.baseURL = runtime.apiBaseUrl;
}

// Request interceptor for API calls
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// ===== 轻量级 GET 重试：网络抖动 / 5xx 自动指数退避重试 2 次 =====
const RETRYABLE_STATUS = new Set([408, 425, 429, 500, 502, 503, 504]);
const MAX_RETRIES = 2;

interface RetriableConfig extends AxiosRequestConfig {
    _retryCount?: number;
    _retryDisabled?: boolean;
}

function shouldRetry(error: AxiosError) {
    const config = error.config as RetriableConfig | undefined;
    if (!config || config._retryDisabled) return false;
    // 只重试幂等方法（GET / HEAD / OPTIONS），避免重复创建任务
    const method = (config.method || 'get').toLowerCase();
    if (!['get', 'head', 'options'].includes(method)) return false;
    if (axios.isCancel(error) || error.code === 'ERR_CANCELED') return false;
    // 真正发不出去的请求（DNS / 断网）也重试
    if (!error.response) return true;
    return RETRYABLE_STATUS.has(error.response.status);
}

// Response interceptor for API calls
api.interceptors.response.use(
    (response: AxiosResponse) => response,
    async (error: AxiosError) => {
        const config = error.config as RetriableConfig | undefined;

        if (config && shouldRetry(error)) {
            config._retryCount = (config._retryCount ?? 0) + 1;
            if (config._retryCount <= MAX_RETRIES) {
                // 指数退避：300ms, 900ms（+一点随机抖动）
                const delay = 300 * Math.pow(3, config._retryCount - 1) + Math.random() * 100;
                await new Promise((resolve) => setTimeout(resolve, delay));
                return api(config);
            }
        }

        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token');
            try {
                const runtime = getAppRuntime();
                if (runtime.routerStrategy === 'hash') {
                    window.location.hash = '#/login';
                } else {
                    window.location.href = '/login';
                }
            } catch {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
