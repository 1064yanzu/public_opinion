import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Space,
  Typography,
  Spin,
  Empty,
} from 'antd';
import {
  ArrowLeftOutlined,
  SmileOutlined,
  MehOutlined,
  FrownOutlined,
  RiseOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import api from '../services/api';
import type { Dataset, AnalyticsData } from '../types';

const { Title, Text } = Typography;

const AnalyticsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchData();
    }
  }, [id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [datasetRes, analyticsRes] = await Promise.all([
        api.get<Dataset>(`/datasets/${id}`),
        api.get<AnalyticsData>(`/analytics/${id}`),
      ]);
      setDataset(datasetRes.data);
      setAnalytics(analyticsRes.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentPieOption = () => {
    if (!analytics) return {};

    const { sentiment_distribution } = analytics;
    return {
      title: {
        text: '情感分布',
        left: 'center',
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)',
      },
      legend: {
        bottom: 10,
        left: 'center',
      },
      series: [
        {
          name: '情感',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 20,
              fontWeight: 'bold',
            },
          },
          data: [
            {
              value: sentiment_distribution.positive,
              name: '正面',
              itemStyle: { color: '#52c41a' },
            },
            {
              value: sentiment_distribution.neutral,
              name: '中性',
              itemStyle: { color: '#faad14' },
            },
            {
              value: sentiment_distribution.negative,
              name: '负面',
              itemStyle: { color: '#ff4d4f' },
            },
          ],
        },
      ],
    };
  };

  const getTimeSeriesOption = () => {
    if (!analytics || !analytics.time_series) return {};

    return {
      title: {
        text: '时间趋势',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
      },
      legend: {
        bottom: 10,
      },
      xAxis: {
        type: 'category',
        data: analytics.time_series.map((item) => item.date),
        boundaryGap: false,
      },
      yAxis: [
        {
          type: 'value',
          name: '数量',
          position: 'left',
        },
        {
          type: 'value',
          name: '情感得分',
          position: 'right',
          min: 0,
          max: 1,
        },
      ],
      series: [
        {
          name: '记录数量',
          type: 'line',
          data: analytics.time_series.map((item) => item.count),
          smooth: true,
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
                { offset: 1, color: 'rgba(99, 102, 241, 0.05)' },
              ],
            },
          },
          itemStyle: {
            color: '#6366f1',
          },
        },
        {
          name: '平均情感',
          type: 'line',
          yAxisIndex: 1,
          data: analytics.time_series.map((item) => item.avg_sentiment),
          smooth: true,
          itemStyle: {
            color: '#f5576c',
          },
        },
      ],
    };
  };

  const getKeywordsOption = () => {
    if (!analytics || !analytics.top_keywords) return {};

    return {
      title: {
        text: '关键词分布',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      xAxis: {
        type: 'value',
      },
      yAxis: {
        type: 'category',
        data: analytics.top_keywords.map((item) => item.word).reverse(),
      },
      series: [
        {
          name: '频次',
          type: 'bar',
          data: analytics.top_keywords.map((item) => item.count).reverse(),
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 1,
              y2: 0,
              colorStops: [
                { offset: 0, color: '#667eea' },
                { offset: 1, color: '#764ba2' },
              ],
            },
            borderRadius: [0, 10, 10, 0],
          },
          label: {
            show: true,
            position: 'right',
          },
        },
      ],
    };
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!dataset || !analytics) {
    return (
      <Empty
        description="暂无数据"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        <Button onClick={() => navigate('/datasets')}>返回数据集列表</Button>
      </Empty>
    );
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        bordered={false}
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: 12,
        }}
      >
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(`/datasets/${id}`)}
          style={{
            background: 'rgba(255,255,255,0.2)',
            color: 'white',
            border: 'none',
            marginBottom: 16,
          }}
        >
          返回
        </Button>
        <div>
          <Title level={2} style={{ color: 'white', margin: 0 }}>
            数据分析报告
          </Title>
          <p style={{ margin: '8px 0 0', color: 'rgba(255,255,255,0.9)' }}>
            {dataset.name}
          </p>
        </div>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              borderRadius: 12,
            }}
          >
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.9)' }}>总记录数</span>}
              value={analytics.total_records}
              valueStyle={{ color: 'white' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            style={{
              background: 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)',
              color: 'white',
              borderRadius: 12,
            }}
          >
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.9)' }}>正面情感</span>}
              value={analytics.sentiment_distribution.positive}
              prefix={<SmileOutlined />}
              valueStyle={{ color: 'white' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            style={{
              background: 'linear-gradient(135deg, #faad14 0%, #d48806 100%)',
              color: 'white',
              borderRadius: 12,
            }}
          >
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.9)' }}>中性情感</span>}
              value={analytics.sentiment_distribution.neutral}
              prefix={<MehOutlined />}
              valueStyle={{ color: 'white' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            style={{
              background: 'linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%)',
              color: 'white',
              borderRadius: 12,
            }}
          >
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.9)' }}>负面情感</span>}
              value={analytics.sentiment_distribution.negative}
              prefix={<FrownOutlined />}
              valueStyle={{ color: 'white' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card style={{ borderRadius: 12 }}>
            <ReactECharts option={getSentimentPieOption()} style={{ height: 400 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card style={{ borderRadius: 12 }}>
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Statistic
                title="平均情感得分"
                value={analytics.avg_sentiment_score}
                precision={2}
                prefix={<RiseOutlined />}
                valueStyle={{
                  color: analytics.avg_sentiment_score > 0.6 ? '#52c41a' : analytics.avg_sentiment_score < 0.4 ? '#ff4d4f' : '#faad14',
                  fontSize: 48,
                }}
              />
              <Text type="secondary" style={{ marginTop: 16, display: 'block' }}>
                基于 {analytics.total_records} 条记录的综合评估
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {analytics.time_series && analytics.time_series.length > 0 && (
        <Card style={{ borderRadius: 12 }}>
          <ReactECharts option={getTimeSeriesOption()} style={{ height: 400 }} />
        </Card>
      )}

      {analytics.top_keywords && analytics.top_keywords.length > 0 && (
        <Card style={{ borderRadius: 12 }}>
          <ReactECharts option={getKeywordsOption()} style={{ height: 400 }} />
        </Card>
      )}
    </Space>
  );
};

export default AnalyticsPage;
