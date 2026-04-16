import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Loading } from '@/components/common/Loading';
import { Badge } from '@/components/common/Badge';
import { Cloud } from 'lucide-react';
import api from '@/services/api';
import { resolveBackendUrl } from '@/services/runtime';
import styles from './Advanced.module.css';
import { useSearchParams } from 'react-router-dom';

interface Topic {
    topic_id: number;
    keywords: string[];
    doc_count: number;
    doc_ratio: number;
}

interface Spreader {
    user_name: string;
    post_count: number;
    influence_score: number;
    total_likes: number;
}

export const Advanced: React.FC = () => {
    const [searchParams] = useSearchParams();
    const taskIdParam = searchParams.get('task_id');
    const taskId = taskIdParam ? parseInt(taskIdParam) : null;
    const [loading, setLoading] = useState(false);

    // Data
    const [wordcloudUrl, setWordcloudUrl] = useState<string | null>(null);
    const [topics, setTopics] = useState<Topic[]>([]);
    const [spreaders, setSpreaders] = useState<Spreader[]>([]);

    // Quick helper to fetch all advanced metrics
    const fetchAdvancedData = async (tid: number, kw: string) => {
        setLoading(true);
        try {
            // 1. Wordcloud
            // Use POST if generation needed, but maybe GET if we just want to fetch? 
            // The backend definition is POST /wordcloud.
            const wcRes = await api.post(`/advanced/wordcloud?task_id=${tid}&keyword=${kw}`);
            if (wcRes.data.image_url) {
                setWordcloudUrl(wcRes.data.image_url);
            }

            // 2. Topics
            const topicsRes = await api.get(`/advanced/topics?task_id=${tid}`);
            setTopics(topicsRes.data.topics || []); // Backend returns {topics: [], ...}

            // 3. Spreaders
            const spreadersRes = await api.get(`/advanced/key-spreaders?task_id=${tid}`);
            setSpreaders(spreadersRes.data.spreaders || []); // Backend returns {spreaders: [], ...}

        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // Initial load
    useEffect(() => {
        if (taskId) {
            // Keyword is optional generally if we have task_id, backend should handle it or we fetch task details first.
            // For simplicity, passing empty keyword or a placeholder, as backend filters by task_id first usually.
            fetchAdvancedData(taskId, '');
        }
    }, [taskId]);

    return (
        <MainLayout>
            <div className={styles.header}>
                <h1 className={styles.title}>高级洞察</h1>
                <p className={styles.subtitle}>深度挖掘文本主题、关键传播节点与语义关联。</p>
            </div>

            {!taskId ? (
                <Card className={styles.emptyState}>
                    <div className={styles.emptyContent}>
                        <Cloud size={48} className={styles.emptyIcon} />
                        <h3>暂无分析数据</h3>
                        <p>请先在“舆情分析”页面执行一次完整的分析任务。</p>
                    </div>
                </Card>
            ) : (
                <div className={styles.content}>
                    {loading ? <Loading fullScreen text="正在进行深度计算..." /> : (
                        <>
                            <div className={styles.row}>
                                <Card title="语义词云" subtitle="高频关键词可视化" className={styles.wcCard}>
                                    {wordcloudUrl ? (
                                        <div className={styles.wcWrapper}>
                                            <img src={resolveBackendUrl(wordcloudUrl)} alt="Word Cloud" className={styles.wcImage} />
                                        </div>
                                    ) : (
                                        <div className={styles.placeholder}>词云生成失败或无数据</div>
                                    )}
                                </Card>

                                <Card title="主题聚类" subtitle="自动提取的文本话题" className={styles.topicCard}>
                                    <div className={styles.topicList}>
                                        {topics.map((topic) => (
                                            <div key={topic.topic_id} className={styles.topicItem}>
                                                <div className={styles.topicHeader}>
                                                    <span className={styles.topicId}>Topic {topic.topic_id + 1}</span>
                                                    <Badge variant="info">{(topic.doc_ratio * 100).toFixed(1)}%</Badge>
                                                </div>
                                                <div className={styles.keywords}>
                                                    {topic.keywords.slice(0, 5).map(k => (
                                                        <span key={k} className={styles.keyword}>{k}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </Card>
                            </div>

                            <Card title="关键传播主体" subtitle="基于影响力模型的用户排名" className={styles.spreaderCard}>
                                <table className={styles.table}>
                                    <thead>
                                        <tr>
                                            <th>排名</th>
                                            <th>用户/账号</th>
                                            <th>发布量</th>
                                            <th>互动总量</th>
                                            <th>影响力得分</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {spreaders.map((user, idx) => (
                                            <tr key={idx}>
                                                <td>{idx + 1}</td>
                                                <td className={styles.userCell}>
                                                    <div className={styles.avatar}>{user.user_name[0]}</div>
                                                    {user.user_name}
                                                </td>
                                                <td>{user.post_count}</td>
                                                <td>{user.total_likes}</td>
                                                <td>
                                                    <div className={styles.scoreBar}>
                                                        <div
                                                            className={styles.scoreFill}
                                                            style={{ width: `${Math.min(user.influence_score, 100)}%` }}
                                                        />
                                                        <span>{user.influence_score.toFixed(1)}</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </Card>
                        </>
                    )}
                </div>
            )}
        </MainLayout>
    );
};
