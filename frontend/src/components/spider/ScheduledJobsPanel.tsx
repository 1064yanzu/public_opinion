import { useCallback, useEffect, useRef, useState } from 'react';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { ConfirmModal } from '@/components/common/ConfirmModal';
import {
  createScheduledJob,
  deleteScheduledJob,
  fetchScheduledJobs,
  fetchSchedulerStatus,
  triggerScheduledJobNow,
  updateScheduledJob,
} from '@/services/scheduler';
import type { ScheduledJob, SchedulerStatus, SmartPhaseInfo } from '@/types';
import styles from './ScheduledJobsPanel.module.css';

// ─── 格式化工具 ──────────────────────────────────────
function fmtDatetime(value?: string | null) {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString('zh-CN', {
      month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return value;
  }
}

/** 用于显示"距下次执行还有 XX 分钟/秒" */
function fmtCountdown(next_run_at?: string | null): string {
  if (!next_run_at) return '—';
  const diff = new Date(next_run_at).getTime() - Date.now();
  if (diff <= 0) return '即将执行';
  const min = Math.floor(diff / 60000);
  const sec = Math.floor((diff % 60000) / 1000);
  if (min > 0) return `${min} 分 ${sec} 秒后`;
  return `${sec} 秒后`;
}

// ─── 时段配置表 ─────────────────────────────────────
function SmartScheduleTable({ phases }: { phases: SmartPhaseInfo[]; currentInterval?: number }) {
  return (
    <div className={styles.phaseTable}>
      <div className={styles.phaseTableTitle}>全天智能采集计划</div>
      <div className={styles.phaseRows}>
        {phases.map((p) => (
          <div key={p.start} className={styles.phaseRow}>
            <span className={styles.phaseEmoji}>{p.emoji}</span>
            <span className={styles.phaseTime}>{p.start}–{p.end}</span>
            <span className={styles.phaseLabel}>{p.label}</span>
            <span className={styles.phaseInterval}>
              {p.interval_minutes < 60
                ? `${p.interval_minutes} 分钟/次`
                : `${p.interval_minutes / 60} 小时/次`}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── 单张 JobCard ──────────────────────────────────
interface JobCardProps {
  job: ScheduledJob;
  onToggle: (id: number, active: boolean) => void;
  onDelete: (id: number) => void;
  onTrigger: (id: number) => void;
}

function JobCard({ job, onToggle, onDelete, onTrigger }: JobCardProps) {
  const [countdown, setCountdown] = useState(() => fmtCountdown(job.next_run_at));

  // 每秒更新倒计时
  useEffect(() => {
    const t = setInterval(() => setCountdown(fmtCountdown(job.next_run_at)), 1000);
    return () => clearInterval(t);
  }, [job.next_run_at]);

  return (
    <div className={`${styles.jobCard} ${!job.is_active ? styles.paused : ''}`}>
      {/* 顶部 */}
      <div className={styles.jobHeader}>
        <span className={styles.jobKeyword}>{job.keyword}</span>
        <Badge variant="neutral">{job.task_type === 'weibo' ? '微博' : '抖音'}</Badge>
        <Badge variant={job.is_active ? 'success' : 'warning'}>
          {job.is_active ? '监控中' : '已暂停'}
        </Badge>
      </div>

      {/* 状态行 */}
      <div className={styles.jobMeta}>
        <span className={styles.metaItem}>
          📄 {job.max_page} 页/次
        </span>
        <span className={styles.metaItem}>
          ✅ 已采集 {job.run_count} 次
        </span>
        {job.is_active && (
          <span className={styles.metaItem} title={`下次执行: ${fmtDatetime(job.next_run_at)}`}>
            ⏱ {countdown}
          </span>
        )}
      </div>

      {/* 上次执行 / 错误 */}
      {job.last_error ? (
        <div className={styles.jobError} title={job.last_error}>
          ⚠️ {job.last_error}
        </div>
      ) : (
        <div className={styles.jobTime}>
          上次: {fmtDatetime(job.last_run_at)}
        </div>
      )}

      {/* 操作 */}
      <div className={styles.jobFooter}>
        <Button size="sm" variant="ghost" onClick={() => onTrigger(job.id)} title="立即触发一次">
          ▶ 立即执行
        </Button>
        <Button size="sm" variant="ghost" onClick={() => onToggle(job.id, !job.is_active)}>
          {job.is_active ? '暂停' : '恢复'}
        </Button>
        <Button size="sm" variant="ghost" onClick={() => onDelete(job.id)}>
          删除
        </Button>
      </div>
    </div>
  );
}

// ─── 主面板 ──────────────────────────────────────────
export function ScheduledJobsPanel({ refreshTrigger }: { refreshTrigger?: number }) {
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPhases, setShowPhases] = useState(false);
  const [confirmJobId, setConfirmJobId] = useState<number | null>(null);


  const load = useCallback(async () => {
    try {
      const [st, list] = await Promise.all([
        fetchSchedulerStatus(),
        fetchScheduledJobs({ page_size: 50 }),
      ]);
      setStatus(st);
      setJobs(list.jobs);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? '加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    // 每 15 秒重新拉一次（更新 next_run_at / last_run_at）
    const timer = window.setInterval(() => void load(), 15_000);
    return () => clearInterval(timer);
  }, [load, refreshTrigger]);

  const handleToggle = async (id: number, active: boolean) => {
    try {
      await updateScheduledJob(id, { is_active: active });
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? '操作失败');
    }
  };

  const handleDelete = (id: number) => {
    setConfirmJobId(id);
  };

  const performDelete = async () => {
    if (confirmJobId === null) return;
    try {
      await deleteScheduledJob(confirmJobId);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? '删除失败');
    } finally {
      setConfirmJobId(null);
    }
  };

  const handleTrigger = async (id: number) => {
    try {
      await triggerScheduledJobNow(id);
      setTimeout(() => void load(), 2000);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? '触发失败');
    }
  };

  return (
    <div className={styles.panel}>
      {/* 调度器状态条 */}
      <div className={styles.statusBar}>
        <div className={`${styles.statusDot} ${status?.is_running ? '' : styles.inactive}`} />
        <span className={styles.statusText}>{status?.message ?? '加载中...'}</span>
        {status?.current_interval && (
          <span className={styles.currentInterval}>
            当前间隔 {status.current_interval} 分钟
          </span>
        )}
        {status?.smart_phases && (
          <button
            className={styles.phaseToggle}
            onClick={() => setShowPhases((v) => !v)}
            type="button"
          >
            {showPhases ? '收起计划' : '查看计划'}
          </button>
        )}
      </div>

      {/* 全天时段配置展开 */}
      {showPhases && status?.smart_phases && (
        <SmartScheduleTable
          phases={status.smart_phases}
          currentInterval={status.current_interval}
        />
      )}

      {error && <div style={{ color: '#f87171', fontSize: 13 }}>{error}</div>}


      {/* 任务列表 */}
      <div className={styles.jobList}>
        {loading ? (
          <div className={styles.empty}>加载中...</div>
        ) : jobs.length === 0 ? (
          <div className={styles.empty}>
            暂无定时监控关键词。<br />
            添加关键词后，系统会自动按当前时段频率周期采集。
          </div>
        ) : (
          jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onToggle={handleToggle}
              onDelete={handleDelete}
              onTrigger={handleTrigger}
            />
          ))
        )}
      </div>
      
      <ConfirmModal
        isOpen={confirmJobId !== null}
        title="确认删除该监控任务？"
        message="删除后相关调度将被取消，不再自动抓取此关键词。已存在的被关联数据可能也将被清除。"
        onConfirm={performDelete}
        onCancel={() => setConfirmJobId(null)}
      />
    </div>
  );
}
