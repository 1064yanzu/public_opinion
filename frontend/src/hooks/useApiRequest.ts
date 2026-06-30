import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * 统一三态 API Hook：返回 { data, loading, error, refetch }。
 *
 * 主要修复:
 *   - Dashboard/Monitor 等页面之前只在失败时 console.error，
 *     用户看到的是空白或永久 loading；这里把 error 暴露给 UI。
 *   - 自动用 AbortController 取消上一次未完成的请求，避免“慢请求覆盖快请求”竞态。
 *
 * 用法:
 *   const stats = useApiRequest(signal => api.get('/dashboard/stats', { signal }));
 *   if (stats.error) ...
 */
export interface ApiRequestState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

type Fetcher<T> = (signal: AbortSignal) => Promise<{ data: T } | T>;

function extractMessage(err: unknown): string {
  if (!err) return '请求失败，请稍后重试。';
  if (typeof err === 'string') return err;
  if (err instanceof Error) return err.message || '请求失败，请稍后重试。';
  const anyErr = err as { response?: { data?: { detail?: string; message?: string } }; message?: string };
  return (
    anyErr.response?.data?.detail
    ?? anyErr.response?.data?.message
    ?? anyErr.message
    ?? '请求失败，请稍后重试。'
  );
}

export function useApiRequest<T>(fetcher: Fetcher<T>, deps: ReadonlyArray<unknown> = []): ApiRequestState<T> {
  const [state, setState] = useState<{ data: T | null; loading: boolean; error: string | null }>({
    data: null,
    loading: true,
    error: null,
  });

  const abortRef = useRef<AbortController | null>(null);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const run = useCallback(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState((prev) => ({ ...prev, loading: true, error: null }));

    fetcherRef.current(controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        const value = (result && typeof result === 'object' && 'data' in (result as object))
          ? (result as { data: T }).data
          : (result as T);
        setState({ data: value, loading: false, error: null });
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        if (err?.code === 'ERR_CANCELED' || err?.name === 'CanceledError') return;
        setState({ data: null, loading: false, error: extractMessage(err) });
      });
  }, []);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    run();
    return () => {
      abortRef.current?.abort();
    };
  }, deps);

  return { ...state, refetch: run };
}
