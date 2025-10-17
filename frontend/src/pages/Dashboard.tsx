import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Statistic,
  Typography,
  List,
  Tag,
  Space,
  Button,
  Empty,
  Spin,
} from 'antd';
import {
  DatabaseOutlined,
  FileTextOutlined,
  SmileOutlined,
  FrownOutlined,
  RightOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import type { Dataset } from '../types';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

const SOURCE_LABELS: Record<string, string> = {
  manual: '手动录入',
  import: '文件导入',
  weibo: '微博爬虫',
  douyin: '抖音爬虫',
};

const SOURCE_COLORS: Record<string, string> = {
  manual: 'blue',
  import: 'purple',
  weibo: 'orange',
  douyin: 'magenta',
};

interface DashboardStats {
  total_datasets: number;
  total_records: number;
  recent_datasets: Dataset[];
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    total_datasets: 0,
    total_records: 0,
    recent_datasets: [],
  });
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const { data: datasets } = await api.get<Dataset[]>('/datasets/');
      
      let totalRecords = 0;
      for (const dataset of datasets) {
        const count = dataset.record_count ?? dataset.total_records ?? 0;
        totalRecords += count;
      }

      setStats({
        total_datasets: datasets.length,
        total_records: totalRecords,
        recent_datasets: datasets.slice(0, 5),
      });
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive':
        return 'success';
      case 'negative':
        return 'error';
      case 'neutral':
      default:
        return 'default';
    }
  };

  return (
    <Spin spinning={loading}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>欢迎回来，{user?.full_name || user?.username}！</Title>
          <Text type="secondary">这是您的数据分析仪表盘</Text>
        </div>

        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={8}>
            <Card
              hoverable
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                borderRadius: 12,
              }}
            >
              <Statistic
                title={<span style={{ color: 'rgba(255,255,255,0.9)' }}>数据集总数</span>}
                value={stats.total_datasets}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: 'white' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card
              hoverable
              style={{
                background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                color: 'white',
                borderRadius: 12,
              }}
            >
              <Statistic
                title={<span style={{ color: 'rgba(255,255,255,0.9)' }}>数据记录总数</span>}
                value={stats.total_records}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: 'white' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card
              hoverable
              style={{
                background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                color: 'white',
                borderRadius: 12,
              }}
            >
              <Statistic
                title={<span style={{ color: 'rgba(255,255,255,0.9)' }}>今日分析</span>}
                value={0}
                suffix="次"
                valueStyle={{ color: 'white' }}
              />
            </Card>
          </Col>
        </Row>

        <Card
          title="最近的数据集"
          extra={
            <Button
              type="link"
              onClick={() => navigate('/datasets')}
              icon={<RightOutlined />}
            >
              查看全部
            </Button>
          }
          style={{ borderRadius: 12 }}
        >
          {stats.recent_datasets.length === 0 ? (
            <Empty
              description="还没有数据集，快去创建一个吧！"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button type="primary" onClick={() => navigate('/datasets')}>
                创建数据集
              </Button>
            </Empty>
          ) : (
            <List
              dataSource={stats.recent_datasets}
              renderItem={(dataset) => (
                <List.Item
                  key={dataset.id}
                  actions={[
                    <Button
                      type="link"
                      onClick={() => navigate(`/datasets/${dataset.id}`)}
                    >
                      查看详情
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={<DatabaseOutlined style={{ fontSize: 24, color: '#6366f1' }} />}
                    title={dataset.name}
                    description={
                      <Space>
                        <Tag color={SOURCE_COLORS[dataset.source] || 'blue'}>
                          {SOURCE_LABELS[dataset.source] || dataset.source_type}
                        </Tag>
                        {dataset.record_count !== undefined && (
                          <Text type="secondary">{dataset.record_count} 条记录</Text>
                        )}
                        <Text type="secondary">
                          创建于 {new Date(dataset.created_at).toLocaleDateString()}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Card>
      </Space>
    </Spin>
  );
};

export default Dashboard;
