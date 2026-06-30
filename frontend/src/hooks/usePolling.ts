import { useEffect, useRef } from 'react';

/**
 * 轮询 Hook：在挂载后按 interval 调用 fn；当页面隐藏时自动暂停，
 * 重新可见时立即触发一次刷新 + 恢复轮询。组件卸载或 deps 变化时会清理 timer。
 *
 * - 使用 useRef 保存 fn，避免依赖 fn 引用触发反复 setInterval（典型闭包陷阱）。
 * - immediate=true（默认）会在挂载时先执行一次。
 * - 传 interval<=0 或 enabled=false 时彻底停止。
 */
type PollFn = () => void | Promise<void>;

interface UsePollingOptions {
  enabled?: boolean;
  immediate?: boolean;
}

export function usePolling(
  fn: PollFn,
  interval: number,
  deps: ReadonlyArray<unknown> = [],
  options: UsePollingOptions = {},
) {
  const { enabled = true, immediate = true } = options;
  const fnRef = useRef<PollFn>(fn);
  fnRef.current = fn;

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!enabled || interval <= 0) {
      return;
    }

    let timer: number | null = null;
    let cancelled = false;

    const run = () => {
      if (cancelled) return;
      try {
        const ret = fnRef.current?.();
        if (ret && typeof (ret as Promise<unknown>).catch === 'function') {
          (ret as Promise<unknown>).catch(() => {
            /* 内部错误由调用方自己处理；这里吞掉避免噪声 */
          });
        }
      } catch {
        /* 同上 */
      }
    };

    const start = () => {
      if (timer !== null) return;
      timer = window.setInterval(run, interval);
    };

    const stop = () => {
      if (timer !== null) {
        window.clearInterval(timer);
        timer = null;
      }
    };

    const onVisibilityChange = () => {
      if (document.hidden) {
        stop();
      } else {
        run();
        start();
      }
    };

    if (immediate && !document.hidden) {
      run();
    }
    if (!document.hidden) {
      start();
    }
    document.addEventListener('visibilitychange', onVisibilityChange);

    return () => {
      cancelled = true;
      document.removeEventListener('visibilitychange', onVisibilityChange);
      stop();
    };
  }, [interval, enabled, immediate, ...deps]);
}
