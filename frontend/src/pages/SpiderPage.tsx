import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  DatePicker,
  Button,
  Table,
  Space,
  message,
  Tag,
  Tabs,
  Progress,
  Statistic,
  Row,
  Col,
  Timeline,
} from 'antd';
import {
  BugOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../services/api';
import ReactECharts from 'echarts-for-react';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface SpiderTask {
  timestamp: string;
  platform: string;
  keyword: string;
  start_date?: string;
  end_date?: string;
  precision: string;
}

interface SpiderData {
  author: string;
  content: string;
  time: string;
  shares: number;
  comments: number;
  likes: number;
  sentiment?: string;
}

const SpiderPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<SpiderTask[]>([]);
  const [spiderData, setSpiderData] = useState<SpiderData[]>([]);
  const [taskStatus, setTaskStatus] = useState<string>('idle');
  const [stats, setStats] = useState({
    positive: 0,
    negative: 0,
    neutral: 0,
  });

  useEffect(() => {
    fetchHistory();
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // 每5秒更新状态
    return () => clearInterval(interval);
  }, []);

  const fetchHistory = async () => {
    try {
      const { data } = await api.get('/spider/history');
      setHistory(data);
    } catch (error) {
      console.error('获取历史记录失败:', error);
    }
  };

  const fetchStatus = async () => {
    try {
      const { data } = await api.get('/spider/status/current');
      setTaskStatus(data.status);
    } catch (error) {
      console.error('获取状态失败:', error);
    }
  };

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const { data } = await api.post('/spider/task', {
        keyword: values.keyword,
        platforms: values.platforms,
        start_date: values.dateRange?.[0]?.format('YYYY-MM-DD'),
        end_date: values.dateRange?.[1]?.format('YYYY-MM-DD'),
        precision: values.precision || 'medium',
      });

      message.success('爬虫任务已启动！');
      
      if (data.data) {
        setSpiderData(data.data.infos2 || []);
        setStats({
          positive: data.data.positive_count || 0,
          negative: data.data.negative_count || 0,
          neutral: data.data.neutral_count || 0,
        });
      }
      
      fetchHistory();
      form.resetFields();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '爬虫任务失败');
    } finally {
      setLoading(false);
    }
  };

  const getSentimentChart = () => {
    return {
      title: {
        text: '情感分布',
        left: 'center',
      },
      tooltip: {
        trigger: 'item',
      },
      series: [
        {
          name: '情感',
          type: 'pie',
          radius: ['40%', '70%'],
          data: [
            { value: stats.positive, name: '正面', itemStyle: { color: '#52c41a' } },
            { value: stats.neutral, name: '中性', itemStyle: { color: '#faad14' } },
            { value: stats.negative, name: '负面', itemStyle: { color: '#ff4d4f' } },
          ],
        },
      ],
    };
  };

  const dataColumns: ColumnsType<SpiderData> = [
    {
      title: '作者',
      dataIndex: 'author',
      key: 'author',
      width: 120,
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
    {
      title: '情感',
      dataIndex: 'sentiment',
      key: 'sentiment',
      width: 100,
      render: (sentiment) => {
        const colorMap: Record<string, string> = {
          positive: 'success',
          negative: 'error',
          neutral: 'warning',
        };
        return sentiment ? (
          <Tag color={colorMap[sentiment] || 'default'}>{sentiment}</Tag>
        ) : null;
      },
    },
    {
      title: '互动',
      key: 'interaction',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <span>👍 {record.likes}</span>
          <span>💬 {record.comments}</span>
          <span>🔄 {record.shares}</span>
        </Space>
      ),
    },
    {
      title: '时间',
      dataIndex: 'time',
      key: 'time',
      width: 180,
    },
  ];

  const historyColumns: ColumnsType<SpiderTask> = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 120,
    },
    {
      title: '关键词',
      dataIndex: 'keyword',
      key: 'keyword',
    },
    {
      title: '精度',
      dataIndex: 'precision',
      key: 'precision',
      width: 100,
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: 12,
        }}
      >
        <Row gutter={16}>
          <Col span={18}>
            <h2 style={{ color: 'white', margin: 0 }}>🕷️ 爬虫数据采集</h2>
            <p style={{ color: 'rgba(255,255,255,0.9)', margin: '8px 0 0' }}>
              支持微博、抖音、B站等多平台数据采集
            </p>
          </Col>
          <Col span={6} style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 14, opacity: 0.9 }}>
              状态: {taskStatus === 'idle' ? '就绪' : taskStatus === 'running' ? '运行中' : '完成'}
            </div>
          </Col>
        </Row>
      </Card>

      <Card title="爬虫配置" style={{ borderRadius: 12 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="keyword"
                label="关键词"
                rules={[{ required: true, message: '请输入关键词' }]}
              >
                <Input
                  placeholder="输入搜索关键词"
                  prefix={<BugOutlined />}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="platforms"
                label="平台"
                rules={[{ required: true, message: '请选择平台' }]}
              >
                <Select mode="multiple" placeholder="选择平台">
                  <Option value="weibo">微博</Option>
                  <Option value="douyin">抖音</Option>
                  <Option value="bilibili">B站</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="precision" label="精度">
                <Select placeholder="选择精度" defaultValue="medium">
                  <Option value="low">低</Option>
                  <Option value="medium">中</Option>
                  <Option value="high">高</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="dateRange" label="时间范围">
                <RangePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label=" ">
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  block
                  size="large"
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                  }}
                >
                  {loading ? '爬取中...' : '开始爬取'}
                </Button>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      {spiderData.length > 0 && (
        <>
          <Row gutter={16}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="正面"
                  value={stats.positive}
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<CheckCircleOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="中性"
                  value={stats.neutral}
                  valueStyle={{ color: '#faad14' }}
                  prefix={<ClockCircleOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="负面"
                  value={stats.negative}
                  valueStyle={{ color: '#ff4d4f' }}
                  prefix={<CloseCircleOutlined />}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Card title="情感分布" style={{ borderRadius: 12 }}>
                <ReactECharts option={getSentimentChart()} style={{ height: 300 }} />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="数据统计" style={{ borderRadius: 12 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>总计: {spiderData.length} 条数据</div>
                  <Progress
                    percent={Math.round((stats.positive / spiderData.length) * 100)}
                    status="success"
                    format={() => `正面 ${stats.positive}`}
                  />
                  <Progress
                    percent={Math.round((stats.neutral / spiderData.length) * 100)}
                    status="normal"
                    format={() => `中性 ${stats.neutral}`}
                  />
                  <Progress
                    percent={Math.round((stats.negative / spiderData.length) * 100)}
                    status="exception"
                    format={() => `负面 ${stats.negative}`}
                  />
                </Space>
              </Card>
            </Col>
          </Row>

          <Card title="爬取数据" style={{ borderRadius: 12 }}>
            <Table
              columns={dataColumns}
              dataSource={spiderData}
              rowKey={(record, index) => `${record.author}-${index}`}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </>
      )}

      <Card title="历史记录" style={{ borderRadius: 12 }}>
        <Table
          columns={historyColumns}
          dataSource={history}
          rowKey="timestamp"
          pagination={{ pageSize: 5 }}
        />
      </Card>
    </Space>
  );
};

export default SpiderPage;
