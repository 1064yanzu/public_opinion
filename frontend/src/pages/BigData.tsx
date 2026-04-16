import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChinaHeatmap, SentimentPieChart } from '@/components/charts';
import { fetchBigdataChartData, fetchHotTopics, fetchRealtimeMonitoring, fetchRealtimeData } from '@/services/page';
import api from '@/services/api';
import styles from './BigData.module.css';
import type { HotTopic, RealtimeMonitoringItem } from '@/types';

function resolveMonitoringLink(item: RealtimeMonitoringItem) {
  return item.Link ?? item.link ?? item.url ?? '#';
}

function toPieData(source: Record<string, number>, nameMap?: Record<string, string>) {
  return Object.entries(source).map(([name, value]) => ({
    name: nameMap?.[name] ?? name,
    value,
  }));
}

function formatClock(date: Date) {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date);
}

export function BigData() {
  const navigate = useNavigate();
  const [now, setNow] = useState(() => new Date());
  const [loading, setLoading] = useState(true);
  const [heatmapData, setHeatmapData] = useState<Array<Record<string, unknown>>>([]);
  const [sentiment, setSentiment] = useState<Record<string, number>>({});
  const [gender, setGender] = useState<Record<string, number>>({});
  const [hotTopics, setHotTopics] = useState<HotTopic[]>([]);
  const [monitoring, setMonitoring] = useState<RealtimeMonitoringItem[]>([]);
  const [alerts, setAlerts] = useState<Array<{ id: string; message: string; level: string }>>([]);
  const [summary, setSummary] = useState<{ total: number; positive: number; negative: number; neutral: number }>({
    total: 0,
    positive: 0,
    negative: 0,
    neutral: 0,
  });

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        const [chart, hot, realtime, latest, alertResponse] = await Promise.all([
          fetchBigdataChartData(),
          fetchHotTopics(10), 
          fetchRealtimeMonitoring(20),
          fetchRealtimeData(),
          api.get('/monitor/alerts'),
        ]);

        if (!mounted) {
          return;
        }

        setHeatmapData(chart.heatmap_data || []);
        setSentiment(chart.sentiment_data || {});
        setGender(chart.gender_data || {});
        setHotTopics(hot);
        setMonitoring(realtime);
        setAlerts(alertResponse.data.alerts || []);
        setSummary({
          total: latest.total,
          positive: latest.sentiment_distribution.positive,
          negative: latest.sentiment_distribution.negative,
          neutral: latest.sentiment_distribution.neutral,
        });
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const sentimentData = useMemo(
    () => toPieData(sentiment, { 正面: '正面', 负面: '负面', 中性: '中性', positive: '正面', negative: '负面', neutral: '中性' }),
    [sentiment],
  );

  const genderData = useMemo(
    () => toPieData(gender, { 男: '男', 女: '女', unknown: '未知', 未知: '未知' }),
    [gender],
  );

  const totalSentiment = (summary.positive || 0) + (summary.negative || 0) + (summary.neutral || 0) || 1;
  const negativePercentage = ((summary.negative || 0) / totalSentiment) * 100;
  
  let warningMessage = '无异常';
  let warningClass = styles.normal;
  
  if (alerts.length > 0) {
    warningMessage = alerts[0].message;
    warningClass = alerts[0].level === 'error' ? styles.danger : styles.warning;
  } else {
    if (negativePercentage <= 30) {
      warningMessage = '无异常';
      warningClass = styles.normal;
    } else if (negativePercentage <= 50) {
      warningMessage = '需要注意';
      warningClass = styles.warning;
    } else {
      warningMessage = '舆情危机提醒';
      warningClass = styles.danger;
    }
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>网络舆情大数据看板</h1>
      </header>
      
      <button onClick={() => navigate('/')} className={styles.returnButton} title="返回首页">
        ←
      </button>

      <div className={styles.realTimeClock}>{formatClock(now)}</div>

      <div className={styles.container}>
        <div className={`${styles.card} ${styles.chinaHeatmap}`}>
          <div className={styles.cardHeader}>
            <h2>中国热力图</h2>
          </div>
          <div className={styles.cardBody}>
            {loading ? <div className={styles.placeholder}>正在加载数据...</div> : null}
            {!loading && (
              <ChinaHeatmap
                data={heatmapData.map((item) => ({
                  name: String((item as any).name ?? ''),
                  value: Number((item as any).value ?? 0),
                }))}
                height={450}
              />
            )}
          </div>
        </div>

        <div className={`${styles.card} ${styles.sentimentAnalysis}`}>
          <div className={styles.cardHeader}>
            <h2>情感分析</h2>
          </div>
          <div className={styles.cardBody}>
             {loading ? <div className={styles.placeholder}>正在加载数据...</div> : null}
             {!loading && sentimentData.length > 0 ? (
                <SentimentPieChart data={sentimentData} height={250} />
             ) : (!loading ? <div className={styles.placeholder}>暂无数据</div> : null)}
          </div>
        </div>

        <div className={`${styles.card} ${styles.genderDistribution}`}>
          <div className={styles.cardHeader}>
            <h2>性别分布</h2>
          </div>
          <div className={styles.cardBody}>
             {loading ? <div className={styles.placeholder}>正在加载数据...</div> : null}
             {!loading && genderData.length > 0 && genderData.some(item => item.value > 0) ? (
                <SentimentPieChart data={genderData} height={250} />
             ) : (!loading ? <div className={styles.placeholder}>暂无数据</div> : null)}
          </div>
        </div>
        
        <div className={`${styles.card} ${styles.alertcard}`}>
          <div className={styles.cardHeader}>
            <h2>预警提示</h2>
          </div>
          <div className={styles.cardBody} style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            {loading ? <div className={styles.placeholder}>正在评估...</div> : (
              <div className={`${styles.warningBox} ${warningClass}`}>
                {warningMessage}
              </div>
            )}
          </div>
        </div>

        <div className={`${styles.card} ${styles.hotTopics}`}>
          <div className={styles.cardHeader}>
            <h2>时事热点</h2>
          </div>
          <div className={`${styles.cardBody} ${styles.hotTopicsBody}`}>
            {loading ? <div className={styles.placeholder}>正在加载热点...</div> : (
              hotTopics.length > 0 ? (
                <div className={styles.hotTopicsGrid}>
                  {hotTopics.map((topic, index) => (
                    <div key={index} className={styles.hotTopicItem}>
                      <a href={topic.link || '#'} target="_blank" rel="noopener noreferrer">
                        {topic.title}
                      </a>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={styles.placeholder}>暂无时事热点数据</div>
              )
            )}
          </div>
        </div>

        <div className={`${styles.card} ${styles.realtimeMonitoring}`}>
          <div className={styles.cardHeader}>
            <h2>实时监测</h2>
          </div>
          <div className={styles.cardBody} style={{ padding: 0 }}>
            {loading ? <div className={styles.placeholder}>正在加载监测...</div> : (
              monitoring.length > 0 ? (
                <ul className={styles.realtimeList}>
                  {monitoring.map((item, index) => (
                    <li key={`${item.author}-${index}`}>
                       <span className={styles.author}>{item.author}</span>
                       <span className={styles.content}>
                         <a href={resolveMonitoringLink(item)} target="_blank" rel="noopener noreferrer">
                           {item.content || '无内容'}
                         </a>
                       </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className={styles.placeholder}>暂无实时监测数据</div>
              )
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
