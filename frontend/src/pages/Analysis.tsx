import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Loading } from '@/components/common/Loading';
import { Badge } from '@/components/common/Badge';
import { TrendChart, SentimentPieChart } from '@/components/charts';
import { Search, RefreshCw, AlertCircle, TrendingUp } from 'lucide-react';
import api from '@/services/api';
import type { AdvancedStats, RiskAssessment } from '@/types';
import styles from './Analysis.module.css';

interface TrendPoint {
  time: string;
  value: number;
}

function getSentimentChartData(stats: AdvancedStats | null) {
  if (!stats?.sentiment_distribution) {
    return [];
  }

  return Object.entries(stats.sentiment_distribution)
    .map(([name, value]) => ({ name, value }))
    .filter((item) => item.value > 0);
}

export const Analysis: React.FC = () => {
  const [keyword, setKeyword] = useState('');
  const [platform, setPlatform] = useState<'weibo' | 'douyin'>('weibo');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [taskId, setTaskId] = useState<number | null>(null);
  const [pollIntervalId, setPollIntervalId] = useState<number | null>(null);
  const [stats, setStats] = useState<AdvancedStats | null>(null);
  const [risk, setRisk] = useState<RiskAssessment | null>(null);
  const [trendData, setTrendData] = useState<TrendPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (pollIntervalId) {
        window.clearInterval(pollIntervalId);
      }
    };
  }, [pollIntervalId]);

  const fetchAnalysisResults = async (nextTaskId: number) => {
    try {
      const [statsRes, riskRes, trendRes] = await Promise.all([
        api.get(`/advanced/statistics?task_id=${nextTaskId}`),
        api.get(`/advanced/risk-assessment?task_id=${nextTaskId}`),
        api.get(`/advanced/trend?task_id=${nextTaskId}`),
      ]);

      setStats(statsRes.data);
      setRisk(riskRes.data);
      setTrendData((trendRes.data.timeline || []).map((point: any) => ({
        time: point.time,
        value: point.count,
      })));
    } catch (err) {
      console.error('Failed to fetch analysis results', err);
      setError('获取分析结果失败。');
    } finally {
      setLoading(false);
      setAnalyzing(false);
    }
  };

  const handleSearch = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!keyword.trim()) {
      return;
    }

    if (pollIntervalId) {
      window.clearInterval(pollIntervalId);
      setPollIntervalId(null);
    }

    setLoading(true);
    setAnalyzing(true);
    setError(null);
    setStats(null);
    setRisk(null);
    setTrendData([]);

    try {
      const response = await api.post('/spider/search', {
        task_type: platform,
        keyword: keyword.trim(),
        max_page: 5,
        async_mode: true,
      });

      const nextTaskId = response.data.id;
      setTaskId(nextTaskId);

      const interval = window.setInterval(async () => {
        try {
          const taskRes = await api.get(`/spider/tasks/${nextTaskId}`);
          const status = taskRes.data.status;

          if (status === 'completed') {
            window.clearInterval(interval);
            setPollIntervalId(null);
            await fetchAnalysisResults(nextTaskId);
          } else if (status === 'failed' || status === 'cancelled') {
            window.clearInterval(interval);
            setPollIntervalId(null);
            setLoading(false);
            setAnalyzing(false);
            setError(taskRes.data.error_message || '任务执行失败，请稍后重试。');
          }
        } catch {
          window.clearInterval(interval);
          setPollIntervalId(null);
          setLoading(false);
          setAnalyzing(false);
          setError('获取任务状态失败。');
        }
      }, 2000);

      setPollIntervalId(interval);
    } catch (err: any) {
      setLoading(false);
      setAnalyzing(false);
      setError(err?.response?.data?.detail || '创建任务失败。');
    }
  };

  const sentimentData = getSentimentChartData(stats);
  const negativeRatio = risk?.details?.negative_ratio ? risk.details.negative_ratio * 100 : 0;

  return (
    <MainLayout>
      <div className={styles.container}>
        <div className={styles.header}>
          <h1 className={styles.title}>舆情分析</h1>
          <p className={styles.subtitle}>先执行真实采集任务，再读取真实统计、风险和趋势结果。</p>
        </div>

        <Card className={styles.searchCard}>
          <form onSubmit={handleSearch} className={styles.searchForm}>
            <div className={styles.platformSelector}>
              <button
                type="button"
                className={`${styles.platformBtn} ${platform === 'weibo' ? styles.active : ''}`}
                onClick={() => setPlatform('weibo')}
              >
                微博
              </button>
              <button
                type="button"
                className={`${styles.platformBtn} ${platform === 'douyin' ? styles.active : ''}`}
                onClick={() => setPlatform('douyin')}
              >
                抖音
              </button>
            </div>
            <div className={styles.inputWrapper}>
              <input
                type="text"
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder={`请输入${platform === 'weibo' ? '微博' : '抖音'}关键词...`}
                className={styles.searchInput}
                disabled={analyzing}
              />
              <Button
                type="submit"
                disabled={analyzing || !keyword.trim()}
                icon={analyzing ? <RefreshCw className={styles.spin} size={18} /> : <Search size={18} />}
              >
                {analyzing ? '分析中...' : '开始分析'}
              </Button>
            </div>
          </form>
        </Card>

        {error ? (
          <div className={styles.errorBanner}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        ) : null}

        {loading ? <Loading fullScreen /> : null}

        {analyzing ? (
          <div className={styles.loadingState}>
            <Loading text="正在抓取并分析数据，这可能需要几十秒..." />
          </div>
        ) : null}

        {!analyzing && stats ? (
          <div className={styles.results}>
            <div className={styles.statsGrid}>
              <Card className={styles.statCard}>
                <div className={styles.statLabel}>总数据量</div>
                <div className={styles.statValue}>{stats.total_count}</div>
                <div className={styles.statTrend}><TrendingUp size={14} /> 当前任务样本</div>
              </Card>
              <Card className={styles.statCard}>
                <div className={styles.statLabel}>总互动量</div>
                <div className={styles.statValue}>{stats.total_interaction?.toLocaleString() ?? 0}</div>
                <div className={styles.statSub}>点赞 + 评论 + 转发</div>
              </Card>
              <Card className={styles.statCard}>
                <div className={styles.statLabel}>风险等级</div>
                <div className={styles.statValue}>
                  <Badge variant={risk?.level === '高' ? 'error' : risk?.level === '中' ? 'warning' : 'success'}>
                    {risk?.level || '低'}
                  </Badge>
                </div>
                <div className={styles.statSub}>分数：{risk?.score ?? 0}</div>
              </Card>
              <Card className={styles.statCard}>
                <div className={styles.statLabel}>负面占比</div>
                <div className={`${styles.statValue} ${styles.negative}`}>
                  {negativeRatio.toFixed(1)}%
                </div>
                <div className={styles.statSub}>根据真实风险计算</div>
              </Card>
            </div>

            {taskId ? (
              <div style={{ marginBottom: 20 }}>
                <Link to={`/advanced?task_id=${taskId}`}>
                  <Button variant="secondary" icon={<TrendingUp size={18} />}>
                    查看深度洞察
                  </Button>
                </Link>
              </div>
            ) : null}

            <div className={styles.chartsGrid}>
              <Card title="热度趋势" subtitle="来自 `/api/advanced/trend`">
                <TrendChart data={trendData} />
              </Card>
              <Card title="情感分布" subtitle="来自 `/api/advanced/statistics`">
                <div style={{ display: 'flex', justifyContent: 'center' }}>
                  <SentimentPieChart data={sentimentData} />
                </div>
              </Card>
            </div>

            {risk?.factors?.length ? (
              <Card title="风险预警">
                <ul className={styles.riskList}>
                  {risk.factors.map((factor) => (
                    <li key={factor} className={styles.riskItem}>
                      <AlertCircle size={16} className={styles.riskIcon} />
                      {factor}
                    </li>
                  ))}
                </ul>
              </Card>
            ) : null}
          </div>
        ) : null}
      </div>
    </MainLayout>
  );
};
