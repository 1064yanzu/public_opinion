import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Loading } from '@/components/common/Loading';
import { FileText, Download, Clock } from 'lucide-react';
import api from '@/services/api';
import { resolveBackendUrl } from '@/services/runtime';
import styles from './Reports.module.css';

interface Report {
    id: number;
    keyword: string;
    filename: string;
    create_time: string;
    download_url: string;
    status: 'ready' | 'generating';
}

export const Reports: React.FC = () => {
    const [keyword, setKeyword] = useState('');
    const [generating, setGenerating] = useState(false);
    const [reports, setReports] = useState<Report[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchReports();
    }, []);

    const fetchReports = async () => {
        try {
            const res = await api.get('/reports');
            setReports(res.data);
        } catch (err) {
            console.error("Failed to fetch reports", err);
        }
    };

    const handleGenerate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!keyword.trim()) return;

        setError(null);
        setGenerating(true);
        // Add temp item
        const tempId = Date.now();
        setReports(prev => [{
            id: tempId,
            keyword: keyword,
            filename: '正在生成...',
            create_time: new Date().toLocaleString(),
            download_url: '',
            status: 'generating'
        }, ...prev]);

        try {
            // Call generate API
            const response = await api.post(`/advanced/report?keyword=${encodeURIComponent(keyword)}`);
            if (!response.data?.success) {
                throw new Error(response.data?.message || '当前关键词没有可生成报告的数据');
            }

            // Update item with real data
            setReports(prev => prev.map(r => {
                if (r.id === tempId) {
                    return {
                        ...r,
                        filename: response.data.filename,
                        download_url: response.data.download_url,
                        status: 'ready'
                    };
                }
                return r;
            }));
            await fetchReports();

        } catch (err: any) {
            console.error(err);
            // Remove failed item or show error
            setReports(prev => prev.filter(r => r.id !== tempId));
            setError(err?.message || err?.response?.data?.detail || '生成报告失败，请确保有相关数据');
        } finally {
            setGenerating(false);
            setKeyword('');
        }
    };

    return (
        <MainLayout>
            <div className={styles.header}>
                <h1 className={styles.title}>报告中心</h1>
                <p className={styles.subtitle}>生成、查看与下载详细的舆情分析报告。</p>
            </div>

            {error ? <div style={{ marginBottom: 16, color: '#a33b3b' }}>{error}</div> : null}

            <div className={styles.grid}>
                <Card title="生成新报告" className={styles.createCard}>
                    <form onSubmit={handleGenerate} className={styles.form}>
                        <p className={styles.hint}>
                            输入关键词，系统将基于最近获取的舆情数据，自动生成一份包含数据概览、情感分析、风险评估及建议对策的完整报告。
                        </p>
                        <input
                            type="text"
                            className={styles.input}
                            placeholder="输入分析关键词..."
                            value={keyword}
                            onChange={e => setKeyword(e.target.value)}
                            disabled={generating}
                        />
                        <Button type="submit" disabled={generating || !keyword} isLoading={generating} icon={<FileText size={18} />}>
                            立即生成报告
                        </Button>
                    </form>
                </Card>

                <Card title="历史报告" className={styles.listCard} noPadding>
                    <div className={styles.list}>
                        {reports.map((report) => (
                            <div key={report.id} className={styles.reportItem}>
                                <div className={styles.reportIcon}>
                                    <FileText size={24} color="#4A7295" />
                                </div>
                                <div className={styles.reportInfo}>
                                    <div className={styles.reportName}>
                                        {report.keyword} - 舆情分析报告
                                    </div>
                                    <div className={styles.reportMeta}>
                                        <Clock size={12} /> {report.create_time} · {report.filename}
                                    </div>
                                </div>
                                <div className={styles.reportAction}>
                                    {report.status === 'generating' ? (
                                        <Loading text="生成中" />
                                    ) : (
                                        <a
                                            href={resolveBackendUrl(report.download_url)}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className={styles.downloadLink}
                                        >
                                            <Button size="sm" variant="outline" icon={<Download size={14} />}>下载</Button>
                                        </a>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </Card>
            </div>
        </MainLayout>
    );
};
