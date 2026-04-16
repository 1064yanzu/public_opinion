import { useEffect, useMemo, useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { deleteSpiderTask, fetchSpiderData, fetchSpiderTask, fetchSpiderTasks } from '@/services/page';
import { createScheduledJob } from '@/services/scheduler';
import api from '@/services/api';
import { Badge } from '@/components/common/Badge';
import { Loading } from '@/components/common/Loading';
import { ConfirmModal } from '@/components/common/ConfirmModal';
import { ScheduledJobsPanel } from '@/components/spider/ScheduledJobsPanel';
import type { SpiderDataItem, SpiderTaskSummary } from '@/types';
import styles from './Spider.module.css';


function mapSentimentLabel(label?: string | null) {
  if (label === 'positive') {
    return { text: '正面', variant: 'success' as const };
  }
  if (label === 'negative') {
    return { text: '负面', variant: 'error' as const };
  }
  return { text: '中性', variant: 'warning' as const };
}

function formatDate(value?: string | null) {
  if (!value) {
    return '未记录';
  }
  return new Date(value).toLocaleString();
}

function mapTaskStatus(status: SpiderTaskSummary['status']) {
  if (status === 'completed') {
    return { text: '已完成', variant: 'success' as const };
  }
  if (status === 'failed') {
    return { text: '失败', variant: 'error' as const };
  }
  if (status === 'cancelled') {
    return { text: '已取消', variant: 'warning' as const };
  }
  if (status === 'processing') {
    return { text: '进行中', variant: 'info' as const };
  }
  return { text: '等待中', variant: 'neutral' as const };
}

export function Spider() {
  const [keyword, setKeyword] = useState('');
  const [platform, setPlatform] = useState<'weibo' | 'douyin'>('weibo');
  const [maxPage, setMaxPage] = useState(5);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [tasks, setTasks] = useState<SpiderTaskSummary[]>([]);
  const [rows, setRows] = useState<SpiderDataItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [tableLoading, setTableLoading] = useState(false);
  const [scheduleRefreshKey, setScheduleRefreshKey] = useState(0);
  const [confirmTaskId, setConfirmTaskId] = useState<number | null>(null);

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) ?? null,
    [tasks, selectedTaskId],
  );

  const connectionHint = selectedTask?.error_message?.includes('登录态')
    ? '当前微博搜索接口要求登录态。请到设置页粘贴完整微博 Cookie header，再重启内置后端后重试。'
    : '如果微博未配置 Cookie，系统会默认先尝试自动访客模式。';

  const loadTasks = async (preferredTaskId?: number | null, ignoreSelected?: boolean) => {
    const response = await fetchSpiderTasks({ page_size: 10 });
    setTasks(response.tasks);

    const nextTaskId = preferredTaskId !== undefined ? preferredTaskId
      : (ignoreSelected ? null : selectedTaskId)
        ?? response.tasks.find((task) => task.status === 'processing')?.id
        ?? response.tasks[0]?.id
        ?? null;

    setSelectedTaskId(nextTaskId);
    return nextTaskId;
  };

  const loadRows = async (taskId: number | null, currentPlatform: 'weibo' | 'douyin') => {
    setTableLoading(true);
    try {
      const response = await fetchSpiderData(currentPlatform, taskId ?? undefined);
      setRows(response.data);
    } finally {
      setTableLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;

    const boot = async () => {
      try {
        const nextTaskId = await loadTasks(null);
        if (!mounted) {
          return;
        }
        await loadRows(nextTaskId, platform);
      } catch (err: any) {
        if (!mounted) {
          return;
        }
        setError(err?.response?.data?.detail ?? '爬虫任务读取失败。');
      }
    };

    void boot();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (selectedTaskId === null) {
      return;
    }
    void loadRows(selectedTaskId, platform);
  }, [platform, selectedTaskId]);

  useEffect(() => {
    const activeTask = tasks.find((task) => task.status === 'processing');
    if (!activeTask) {
      return;
    }

    const timer = window.setInterval(async () => {
      try {
        const detail = await fetchSpiderTask(activeTask.id);
        setTasks((prev) => prev.map((task) => (task.id === detail.id ? detail : task)));

        if (detail.status === 'completed' || detail.status === 'failed' || detail.status === 'cancelled') {
          window.clearInterval(timer);
          await loadTasks(detail.id);
          await loadRows(detail.id, detail.task_type);
          setPlatform(detail.task_type);
        }
      } catch {
        window.clearInterval(timer);
      }
    }, 2500);

    return () => window.clearInterval(timer);
  }, [tasks]);

  const handleCreateTask = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!keyword.trim()) {
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await createScheduledJob({
        task_type: platform,
        keyword: keyword.trim(),
        max_page: maxPage,
        use_smart_schedule: true,
        interval_minutes: 30, // 后端智能模式下会忽略
      });
      setKeyword('');
      setScheduleRefreshKey((prev) => prev + 1);
      
      // 添加人为延迟以显示启动遮罩并确保后台初始子任务抵达数据库
      await new Promise(resolve => setTimeout(resolve, 2000));
      await loadTasks(null, true);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? '创建自动监控任务失败。');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelTask = async (taskId: number) => {
    try {
      await api.post(`/spider/tasks/${taskId}/cancel`);
      await loadTasks(null);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? '停止任务失败。');
    }
  };

  const handleDeleteTask = (taskId: number, event: React.MouseEvent) => {
    event.stopPropagation(); // 防止触发选中
    setConfirmTaskId(taskId);
  };

  const performDeleteTask = async () => {
    if (confirmTaskId === null) return;
    try {
      await deleteSpiderTask(confirmTaskId);
      const isDeletingSelected = selectedTaskId === confirmTaskId;
      if (isDeletingSelected) setSelectedTaskId(null);
      await loadTasks(null, isDeletingSelected);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? '删除任务失败。');
    } finally {
      setConfirmTaskId(null);
    }
  };

  return (
    <MainLayout>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>爬虫控制台</h1>
          <p className={styles.subtitle}>从桌面端直接发起微博或抖音采集任务，并查看真实抓取结果。</p>
        </div>
      </div>

      {isSubmitting && <Loading fullScreen text="正在将关键词注册到智能监控网络中，稍后首次执行将同步呈现..." />}


      <div className={styles.infoBanner}>{connectionHint}</div>

      {error ? <div className={styles.errorBanner}>{error}</div> : null}

      <div className={styles.grid}>
        <Card title="新建监控任务" subtitle="提交后将自动加入该关键词的全天智能周期监控。">
          <form className={styles.form} onSubmit={handleCreateTask}>
            <div className={styles.platformGroup}>
              <button
                className={`${styles.platformBtn} ${platform === 'weibo' ? styles.active : ''}`}
                type="button"
                onClick={() => setPlatform('weibo')}
              >
                微博
              </button>
              <button
                className={`${styles.platformBtn} ${platform === 'douyin' ? styles.active : ''}`}
                type="button"
                onClick={() => setPlatform('douyin')}
              >
                抖音
              </button>
            </div>

            <label className={styles.field}>
              <span>关键词</span>
              <input
                className={styles.input}
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="例如：某事件、某品牌、某政策"
              />
            </label>

            <label className={styles.field}>
              <span>采集页数</span>
              <input
                className={styles.input}
                type="number"
                min={1}
                max={50}
                value={maxPage}
                onChange={(event) => setMaxPage(Number(event.target.value))}
              />
            </label>

            <Button type="submit" isLoading={isSubmitting}>
              开始采集
            </Button>
          </form>
        </Card>

        <Card title="任务历史" subtitle="点击任务即可切换右侧结果视图。">
          <div className={styles.taskList}>
            {tasks.length === 0 ? <div className={styles.empty}>暂无任务记录</div> : null}
            {tasks.map((task) => (
              <div
                key={task.id}
                className={`${styles.taskItem} ${selectedTaskId === task.id ? styles.selectedTask : ''}`}
                onClick={() => {
                  setSelectedTaskId(task.id);
                  setPlatform(task.task_type);
                }}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    setSelectedTaskId(task.id);
                    setPlatform(task.task_type);
                  }
                }}
                role="button"
                tabIndex={0}
              >
                <div className={styles.taskMeta}>
                  <strong>{task.keyword}</strong>
                  <span>{task.task_type === 'weibo' ? '微博' : '抖音'} · {formatDate(task.created_at)}</span>
                </div>
                <div className={styles.taskActions}>
                  <Badge variant={mapTaskStatus(task.status).variant}>
                    {mapTaskStatus(task.status).text}
                  </Badge>
                  {task.status === 'processing' ? (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => { e.stopPropagation(); handleCancelTask(task.id); }}
                    >
                      停止
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => handleDeleteTask(task.id, e)}
                      title="删除记录"
                    >
                      删除
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="监控中的关键词" subtitle="系统会根据当前时段自动调节以下任务的采集频率（可展开查看计划表）。">
        <ScheduledJobsPanel refreshTrigger={scheduleRefreshKey} />
      </Card>

      <Card
        title="抓取结果"
        subtitle={selectedTask ? `当前任务：${selectedTask.keyword}（${selectedTask.task_type}）` : '展示最近抓取到的真实数据'}
        action={
          selectedTask ? (
            <Badge variant={mapTaskStatus(selectedTask.status).variant}>
              {mapTaskStatus(selectedTask.status).text}
            </Badge>
          ) : undefined
        }
      >
        {selectedTask?.error_message ? <div className={styles.errorBanner}>{selectedTask.error_message}</div> : null}
        {tableLoading ? <Loading text="正在读取抓取结果..." /> : null}
        {!tableLoading && rows.length === 0 ? <div className={styles.empty}>当前还没有抓取结果。</div> : null}
        {!tableLoading && rows.length > 0 ? (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>作者</th>
                  <th>内容</th>
                  <th>情感</th>
                  <th>发布时间</th>
                  <th>互动</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const sentiment = mapSentimentLabel(row.sentiment_label);
                  const author = row.user_name || row.author || '未知作者';
                  const interactions = (row.like_count ?? 0) + (row.comment_count ?? 0) + (row.share_count ?? 0);
                  return (
                    <tr key={row.id}>
                      <td>{author}</td>
                      <td className={styles.contentCell}>{row.content || '无内容'}</td>
                      <td><Badge variant={sentiment.variant}>{sentiment.text}</Badge></td>
                      <td>{formatDate(row.publish_time)}</td>
                      <td>{interactions}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </Card>
      
      <ConfirmModal
        isOpen={confirmTaskId !== null}
        title="确认删除该记录？"
        message="删除任务后，关联的所有抓取数据将会被一并清除，且不可恢复。"
        onConfirm={performDeleteTask}
        onCancel={() => setConfirmTaskId(null)}
      />
    </MainLayout>
  );
}
