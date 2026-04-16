import React, { useEffect, useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Plus, TrendingUp, Activity, MessageSquare } from 'lucide-react';
import { TrendChart, SentimentPieChart } from '@/components/charts';
import { useAuth } from '@/context/AuthContext';
import styles from './Dashboard.module.css';
import api from '@/services/api';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
    const { user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<any>({});
    const [trendData, setTrendData] = useState<any[]>([]);
    const [sentiments, setSentiments] = useState<any[]>([]);
    const [tasks, setTasks] = useState<any[]>([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Basic Stats
                const statsRes = await api.get('/dashboard/stats');
                setStats(statsRes.data);
                if (statsRes.data.sentiment_distribution) {
                    setSentiments(statsRes.data.sentiment_distribution);
                }

                // 2. Trend Data 
                const chartRes = await api.get('/dashboard/trend');
                if (chartRes.data.dates) {
                    const data = chartRes.data.dates.map((date: string, i: number) => ({
                        time: date,
                        value: chartRes.data.values[i]
                    }));
                    setTrendData(data);
                }

                // 3. Latest Tasks
                const tasksRes = await api.get('/spider/tasks?page_size=5');
                setTasks(tasksRes.data.tasks || []);

                // 4. Sentiment (Already handled in stats)
            } catch (error) {
                console.error("Failed to load dashboard data", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);


    if (loading) {
        return (
            <MainLayout>
                <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ animation: 'spin 1s linear infinite' }}>Loading...</div>
                </div>
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

                <Card title="最近监测任务" className={styles.tasksCard} noPadding>
                    <div className={styles.taskList}>
                        {tasks.length === 0 ? (
                            <div className={styles.emptyTasks}>暂无活跃任务</div>
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
