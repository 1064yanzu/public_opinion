import { useEffect, useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Loading } from '@/components/common/Loading';
import { fetchCaseDetail, fetchCases } from '@/services/page';
import type { CaseDetailResponse, CaseSummary } from '@/types';
import styles from './Cases.module.css';

function formatDate(value?: string | null) {
  if (!value) {
    return '未记录';
  }
  return new Date(value).toLocaleString();
}

export function Cases() {
  const [loading, setLoading] = useState(true);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);
  const [detail, setDetail] = useState<CaseDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      const response = await fetchCases();
      if (!mounted) {
        return;
      }
      setCases(response.cases);
      setSelectedCaseId(response.cases[0]?.id ?? null);
      setLoading(false);
    };

    void load();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedCaseId) {
      setDetail(null);
      return;
    }

    let mounted = true;
    const loadDetail = async () => {
      setDetailLoading(true);
      try {
        const response = await fetchCaseDetail(selectedCaseId);
        if (mounted) {
          setDetail(response);
        }
      } finally {
        if (mounted) {
          setDetailLoading(false);
        }
      }
    };

    void loadDetail();
    return () => {
      mounted = false;
    };
  }, [selectedCaseId]);

  if (loading) {
    return <Loading fullScreen text="正在读取案例库..." />;
  }

  return (
    <MainLayout>
      <div className={styles.header}>
        <h1 className={styles.title}>案例库</h1>
        <p className={styles.subtitle}>基于已完成任务生成真实案例视图，替代旧版 `case_study.html` 的静态 CSV 方案。</p>
      </div>

      <div className={styles.layout}>
        <Card title="案例列表" subtitle="仅展示后端已有真实完成任务。">
          <div className={styles.caseList}>
            {cases.length === 0 ? <div className={styles.empty}>当前还没有可分析的已完成案例。</div> : null}
            {cases.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`${styles.caseItem} ${selectedCaseId === item.id ? styles.selected : ''}`}
                onClick={() => setSelectedCaseId(item.id)}
              >
                <strong>{item.keyword}</strong>
                <span>{item.type === 'weibo' ? '微博' : '抖音'}</span>
                <small>{formatDate(item.completed_at)}</small>
              </button>
            ))}
          </div>
        </Card>

        <div className={styles.detailColumn}>
          {detailLoading ? <Loading text="正在读取案例详情..." /> : null}
          {!detailLoading && !detail ? <Card><div className={styles.empty}>请选择一个案例查看详情。</div></Card> : null}
          {!detailLoading && detail ? (
            <>
              <Card
                title={detail.keyword}
                subtitle={`任务类型：${detail.task_type === 'weibo' ? '微博' : '抖音'} · 完成时间：${formatDate(detail.completed_at)}`}
                action={
                  <Badge variant={detail.risk.level === '高' ? 'error' : detail.risk.level === '中' ? 'warning' : 'success'}>
                    风险 {detail.risk.level}
                  </Badge>
                }
              >
                <div className={styles.statsGrid}>
                  <div className={styles.statCard}>
                    <span>样本量</span>
                    <strong>{detail.statistics.total_count}</strong>
                  </div>
                  <div className={styles.statCard}>
                    <span>总互动</span>
                    <strong>{detail.statistics.total_interaction ?? 0}</strong>
                  </div>
                  <div className={styles.statCard}>
                    <span>风险得分</span>
                    <strong>{detail.risk.score}</strong>
                  </div>
                </div>

                {detail.risk.factors.length > 0 ? (
                  <div className={styles.factorList}>
                    {detail.risk.factors.map((factor) => (
                      <div key={factor} className={styles.factorItem}>{factor}</div>
                    ))}
                  </div>
                ) : null}
              </Card>

              <Card title="主题聚类">
                <div className={styles.topicList}>
                  {detail.topics.length === 0 ? <div className={styles.empty}>该案例暂无可聚类文本。</div> : null}
                  {detail.topics.map((topic) => (
                    <div key={topic.topic_id} className={styles.topicCard}>
                      <strong>主题 {topic.topic_id + 1}</strong>
                      <p>{topic.keywords.join(' / ')}</p>
                    </div>
                  ))}
                </div>
              </Card>

              <Card title="最近样本">
                <div className={styles.sampleList}>
                  {detail.recent_items.slice(0, 8).map((item) => (
                    <div key={item.id} className={styles.sampleItem}>
                      <div className={styles.sampleMeta}>
                        <strong>{item.author}</strong>
                        <span>{formatDate(item.publish_time)}</span>
                      </div>
                      <p>{item.content}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </>
          ) : null}
        </div>
      </div>
    </MainLayout>
  );
}
