import { useEffect, useMemo, useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { Loading } from '@/components/common/Loading';
import { createSpiderTask, fetchSpiderData, fetchSpiderTask, fetchSpiderTasks } from '@/services/page';
import api from '@/services/api';
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

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) ?? null,
    [tasks, selectedTaskId],
  );

  const connectionHint = selectedTask?.error_message?.includes('登录态')
    ? '当前微博搜索接口要求登录态。请到设置页粘贴完整微博 Cookie header，再重启内置后端后重试。'
    : '如果微博未配置 Cookie，系统会默认先尝试自动访客模式。';

  const loadTasks = async (preferredTaskId?: number | null) => {
    const response = await fetchSpiderTasks({ page_size: 10 });
    setTasks(response.tasks);

    const nextTaskId = preferredTaskId
      ?? selectedTaskId
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
      const task = await createSpiderTask({
        task_type: platform,
        keyword: keyword.trim(),
        max_page: maxPage,
        async_mode: true,
      });
      setKeyword('');
      await loadTasks(task.id);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? '创建采集任务失败。');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelTask = async (taskId: number) => {
    try {
      await api.post(`/spider/tasks/${taskId}/cancel`);
      await loadTasks(taskId);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? '停止任务失败。');
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

      <div className={styles.infoBanner}>{connectionHint}</div>

      {error ? <div className={styles.errorBanner}>{error}</div> : null}

      <div className={styles.grid}>
        <Card title="新建采集任务" subtitle="关键词、平台与页数都会真实提交给后端执行。">
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
                    <Button size="sm" variant="ghost" onClick={() => handleCancelTask(task.id)}>
                      停止
                    </Button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

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
    </MainLayout>
  );
}
