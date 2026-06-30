import React, { useEffect, useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Loading } from '@/components/common/Loading';
import { Plus, TrendingUp, Activity, MessageSquare } from 'lucide-react';
import { TrendChart, SentimentPieChart } from '@/components/charts';
import { useAuth } from '@/context/AuthContext';
import styles from './Dashboard.module.css';
import api from '@/services/api';
import { generateWordcloud } from '@/services/page';
import { resolveBackendUrl } from '@/services/runtime';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
    const { user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<any>({});
    const [trendData, setTrendData] = useState<any[]>([]);
    const [sentiments, setSentiments] = useState<any[]>([]);
    const [tasks, setTasks] = useState<any[]>([]);
    const [influencers, setInfluencers] = useState<any[]>([]);
    const [wordcloudUrl, setWordcloudUrl] = useState<string | null>(null);
    const [wordcloudGenerating, setWordcloudGenerating] = useState(false);
    const [loadError, setLoadError] = useState<string | null>(null);

    useEffect(() => {
        let mounted = true;
        const controller = new AbortController();

        const fetchData = async () => {
            // 用 allSettled 并发拉取，任一接口失败不会拖死其他卡片
            const results = await Promise.allSettled([
                api.get('/dashboard/stats', { signal: controller.signal }),
                api.get('/dashboard/trend', { signal: controller.signal }),
                api.get('/spider/tasks?page_size=5', { signal: controller.signal }),
                api.get('/dashboard/influencers', { signal: controller.signal }),
            ]);

            if (!mounted) return;

            const [statsRes, trendRes, tasksRes, infRes] = results;
            const failures: string[] = [];

            if (statsRes.status === 'fulfilled') {
                setStats(statsRes.value.data);
                if (statsRes.value.data.sentiment_distribution) {
                    setSentiments(statsRes.value.data.sentiment_distribution);
                }
            } else {
                failures.push('概览统计');
            }

            if (trendRes.status === 'fulfilled') {
                if (trendRes.value.data.dates) {
                    const data = trendRes.value.data.dates.map((date: string, i: number) => ({
                        time: date,
                        value: trendRes.value.data.values[i],
                    }));
                    setTrendData(data);
                }
            } else {
                failures.push('热度趋势');
            }

            if (tasksRes.status === 'fulfilled') {
                setTasks(tasksRes.value.data.tasks || []);
            } else {
                failures.push('采集任务');
            }

            if (infRes.status === 'fulfilled') {
                setInfluencers(infRes.value.data.influencers || []);
            } else {
                failures.push('传播主体');
            }

            // 词云独立处理（耗时较长，且容易失败）
            setWordcloudGenerating(true);
            generateWordcloud()
                .then((res) => {
                    if (!mounted) return;
                    if (res.image_url) {
                        setWordcloudUrl(resolveBackendUrl(res.image_url));
                    }
                })
                .catch(() => {
                    if (mounted) failures.push('词云图');
                })
                .finally(() => {
                    if (mounted) setWordcloudGenerating(false);
                });

            if (failures.length > 0) {
                setLoadError(`部分数据加载失败：${failures.join('、')}。可下拉刷新或稍后重试。`);
            } else {
                setLoadError(null);
            }
            setLoading(false);
        };

        void fetchData();
        return () => {
            mounted = false;
            controller.abort();
        };
    }, []);


    if (loading) {
        return (
            <MainLayout>
                <Loading fullScreen text="正在加载概览数据..." />
            </MainLayout>
        );
    }

    return (
        <MainLayout>
            <header className={styles.header}>
                <div>
                    <h1 className={styles.heading}>概览</h1>
                    <p className={styles.subheading}>欢迎回来，{user?.username}。今日舆情态势平稳。</p>
                </div>
                <Link to="/analysis">
                    <Button icon={<Plus size={18} />}>新建分析</Button>
                </Link>
            </header>

            {loadError ? (
                <div style={{ background: 'rgba(217, 108, 79, 0.08)', border: '1px solid rgba(217, 108, 79, 0.3)', color: '#8b2d2d', padding: '12px 16px', borderRadius: 12, marginBottom: 16 }}>
                    {loadError}
                </div>
            ) : null}

            {/* Summary Cards */}
            <div className={styles.summaryGrid}>
                <Card className={styles.summaryCard}>
                    <div className={styles.summaryIcon} style={{ background: '#E6F4EA', color: '#4A7A5E' }}>
                        <TrendingUp size={24} />
                    </div>
                    <div>
                        <div className={styles.summaryValue}>{stats.today_posts || 0}</div>
                        <div className={styles.summaryLabel}>今日新增内容</div>
                    </div>
                </Card>
                <Card className={styles.summaryCard}>
                    <div className={styles.summaryIcon} style={{ background: '#E8F0FE', color: '#4A7295' }}>
                        <Activity size={24} />
                    </div>
                    <div>
                        <div className={styles.summaryValue}>{stats.active_tasks || 0}</div>
                        <div className={styles.summaryLabel}>活跃监测任务</div>
                    </div>
                </Card>
                <Card className={styles.summaryCard}>
                    <div className={styles.summaryIcon} style={{ background: '#FEF7E0', color: '#B58428' }}>
                        <MessageSquare size={24} />
                    </div>
                    <div>
                        <div className={styles.summaryValue}>{stats.total_posts || 0}</div>
                        <div className={styles.summaryLabel}>累计采集内容</div>
                    </div>
                </Card>
            </div>

            <div className={styles.grid}>
                <Card title="全网热度趋势" subtitle="过去7天的数据流量变化" className={styles.mainCard}>
                    <div className={styles.chartWrapper}>
                        <TrendChart data={trendData.length > 0 ? trendData : [{ time: 'Mon', value: 10 }, { time: 'Tue', value: 20 }]} height={320} />
                    </div>
                </Card>

                <Card title="整体情感分布" className={styles.sideCard}>
                    <div className={styles.chartWrapperPie}>
                        <SentimentPieChart data={sentiments} height={300} />
                    </div>
                </Card>

                <Card title="全网舆情词云" subtitle="提取最新全网数据高频关键词" action={wordcloudGenerating ? <span style={{fontSize: '0.85em', color: 'var(--text-tertiary)'}}>正在提取...</span> : null} className={styles.wordcloudCard}>
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
                        {wordcloudUrl ? (
                            <img src={wordcloudUrl} alt="全网舆情词云" className={styles.wordcloudImg} />
                        ) : wordcloudGenerating ? (
                            <div style={{ animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite', color: '#9ca3af' }}>正在绘制词图轮廓...</div>
                        ) : (
                            <div style={{ color: '#9ca3af' }}>暂无词云数据</div>
                        )}
                    </div>
                </Card>

                <Card title="关键传播主体" subtitle="全网互动量(转评赞) Top 5" className={styles.influencersCard} noPadding>
                    <div className={styles.taskList}>
                        {influencers.length === 0 ? (
                            <div className={styles.emptyTasks}>暂无传播主体数据</div>
                        ) : (
                            influencers.map((inf, index) => (
                                <div key={index} className={styles.influencerItem}>
                                    <div className={`${styles.influencerRank} ${index === 0 ? styles.top1 : index === 1 ? styles.top2 : index === 2 ? styles.top3 : ''}`}>
                                        {index + 1}
                                    </div>
                                    <div className={styles.influencerName}>@{inf.name}</div>
                                    <div className={styles.influencerScore}>
                                        <span className={styles.influencerScoreValue}>{inf.engagement.toLocaleString()}</span>
                                        <span className={styles.influencerScoreLabel}>总互动</span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </Card>

                <Card title="最近采集记录" className={styles.tasksCard} noPadding>
                    <div className={styles.taskList}>
                        {tasks.length === 0 ? (
                            <div className={styles.emptyTasks}>暂无采集记录</div>
                        ) : (
                            tasks.map((task) => (
                                <div key={task.id} className={styles.taskItem}>
                                    <div className={styles.taskInfo}>
                                        <span className={styles.taskName}>关键词：{task.keyword}</span>
                                        <span className={styles.taskTime}>
                                            {task.task_type === 'weibo' ? '微博' : '抖音'} · {new Date(task.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    <div className={`${styles.taskStatus} ${styles[task.status]}`}>
                                        {task.status === 'completed' ? '已完成' :
                                            task.status === 'processing' ? '进行中' :
                                                task.status === 'failed' ? '失败' : '等待中'}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </Card>
            </div>
        </MainLayout>
    );
};
