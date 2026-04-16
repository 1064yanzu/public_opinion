import React, { useEffect, useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Loading } from '@/components/common/Loading';
import { Cpu, Database, Server, AlertTriangle, CheckCircle } from 'lucide-react';
import api from '@/services/api';
import styles from './Monitor.module.css';

export const Monitor: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [perf, setPerf] = useState<any>(null);
    const [cache, setCache] = useState<any>(null);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [health, setHealth] = useState<any>(null);

    useEffect(() => {
        fetchMonitorData();
        const interval = setInterval(fetchMonitorData, 5000); // 5s refresh
        return () => clearInterval(interval);
    }, []);

    const fetchMonitorData = async () => {
        try {
            const [perfRes, cacheRes, alertsRes, healthRes] = await Promise.all([
                api.get('/monitor/performance'),
                api.get('/monitor/cache'),
                api.get('/monitor/alerts'),
                api.get('/monitor/health'),
            ]);

            setPerf(perfRes.data);
            setCache(cacheRes.data);
            setAlerts(alertsRes.data.alerts || []);
            setHealth(healthRes.data);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setLoading(false);
        }
    };

    const getHealthColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'healthy': return 'success';
            case 'warning': return 'warning';
            case 'critical': return 'error';
            default: return 'neutral';
        }
    };

    if (loading && !perf) return <Loading fullScreen />;

    return (
        <MainLayout>
            <div className={styles.header}>
                <div>
                    <h1 className={styles.title}>系统监控</h1>
                    <p className={styles.subtitle}>实时监控服务器资源、缓存状态及系统告警。</p>
                </div>
                <Badge variant={getHealthColor(health?.status) as any} className={styles.statusBadge}>
                    系统状态: {health?.status || '未知'}
                </Badge>
            </div>

            <div className={styles.grid}>
                {/* Resource Usage */}
                <Card title="资源使用率" className={styles.resourceCard}>
                    <div className={styles.resourceGrid}>
                        <div className={styles.resourceItem}>
                            <Cpu size={24} className={styles.resourceIcon} />
                            <div className={styles.resourceInfo}>
                                <div className={styles.label}>CPU 使用率</div>
                                <div className={styles.value}>{perf?.cpu_usage || 0}%</div>
                                <div className={styles.barBg}>
                                    <div className={styles.barFill} style={{ width: `${perf?.cpu_usage || 0}%`, background: '#D96C4F' }} />
                                </div>
                            </div>
                        </div>
                        <div className={styles.resourceItem}>
                            <Server size={24} className={styles.resourceIcon} />
                            <div className={styles.resourceInfo}>
                                <div className={styles.label}>内存使用率</div>
                                <div className={styles.value}>{perf?.memory_usage || 0}%</div>
                                <div className={styles.barBg}>
                                    <div className={styles.barFill} style={{ width: `${perf?.memory_usage || 0}%`, background: '#4A7295' }} />
                                </div>
                            </div>
                        </div>
                        <div className={styles.resourceItem}>
                            <Database size={24} className={styles.resourceIcon} />
                            <div className={styles.resourceInfo}>
                                <div className={styles.label}>磁盘使用率</div>
                                <div className={styles.value}>{perf?.disk_usage || 0}%</div>
                                <div className={styles.barBg}>
                                    <div className={styles.barFill} style={{ width: `${perf?.disk_usage || 0}%`, background: '#4A7A5E' }} />
                                </div>
                            </div>
                        </div>
                    </div>
                </Card>

                {/* Cache Stats */}
                <Card title="缓存性能" className={styles.cacheCard}>
                    <div className={styles.statRow}>
                        <div className={styles.statItem}>
                            <div className={styles.statValue}>{((cache?.hit_rate || 0) * 100).toFixed(1)}%</div>
                            <div className={styles.statLabel}>命中率</div>
                        </div>
                        <div className={styles.statItem}>
                            <div className={styles.statValue}>{cache?.item_count || 0}</div>
                            <div className={styles.statLabel}>缓存键数</div>
                        </div>
                        <div className={styles.statItem}>
                            <div className={styles.statValue}>{cache?.total_size || 0} B</div>
                            <div className={styles.statLabel}>占用内存</div>
                        </div>
                    </div>
                </Card>

                {/* Alerts */}
                <Card title="告警信息" className={styles.alertCard} noPadding>
                    <div className={styles.alertList}>
                        {alerts.length === 0 ? (
                            <div className={styles.emptyAlerts}>
                                <CheckCircle size={48} color="#4A7A5E" style={{ opacity: 0.5, marginBottom: 10 }} />
                                <p>系统运行正常，无告警信息</p>
                            </div>
                        ) : (
                            alerts.map((alert) => (
                                <div key={alert.id} className={styles.alertItem}>
                                    <AlertTriangle size={18} color="#D15555" />
                                    <div className={styles.alertContent}>
                                        <div className={styles.alertMsg}>{alert.message}</div>
                                        <div className={styles.alertTime}>{new Date(alert.timestamp).toLocaleString()}</div>
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
