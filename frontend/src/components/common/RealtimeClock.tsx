import React, { useEffect, useState } from 'react';

interface RealtimeClockProps {
  className?: string;
}

function formatClock(date: Date) {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date);
}

/**
 * 独立的实时时钟组件。每秒只重渲染自己，避免触发父级 BigData 整页重绘。
 * 页面隐藏时停掉 timer。
 */
function RealtimeClockInner({ className }: RealtimeClockProps) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    let timer: number | null = null;

    const start = () => {
      if (timer !== null) return;
      timer = window.setInterval(() => setNow(new Date()), 1000);
    };

    const stop = () => {
      if (timer !== null) {
        window.clearInterval(timer);
        timer = null;
      }
    };

    const onVisibility = () => {
      if (document.hidden) {
        stop();
      } else {
        setNow(new Date());
        start();
      }
    };

    if (!document.hidden) start();
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      stop();
    };
  }, []);

  return <div className={className}>{formatClock(now)}</div>;
}

export const RealtimeClock = React.memo(RealtimeClockInner);
