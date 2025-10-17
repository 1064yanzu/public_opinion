import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  Select,
  InputNumber,
  Button,
  Typography,
  Space,
  Row,
  Col,
  Tag,
  message,
  Result,
  Divider,
  Alert,
} from 'antd';
import {
  PlayCircleOutlined,
  ThunderboltOutlined,
  DeploymentUnitOutlined,
  PlusCircleOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import type { Dataset, CrawlResponse, SpiderSourcesResponse } from '../types';

const { Title, Paragraph, Text } = Typography;

const SpiderPage: React.FC = () => {
  const navigate = useNavigate();
  const [sources, setSources] = useState<string[]>([]);
  const [sourceDescriptions, setSourceDescriptions] = useState<Record<string, string>>({});
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loadingSources, setLoadingSources] = useState(false);
  const [creatingNew, setCreatingNew] = useState(false);
  const [appending, setAppending] = useState(false);
  const [result, setResult] = useState<CrawlResponse | null>(null);
  const [newForm] = Form.useForm();
  const [appendForm] = Form.useForm();

  useEffect(() => {
    fetchSources();
    fetchDatasets();
  }, []);

  const fetchSources = async () => {
    setLoadingSources(true);
    try {
      const { data } = await api.get<SpiderSourcesResponse>('/spider/sources');
      setSources(data.sources || []);
      setSourceDescriptions(data.descriptions || {});
    } catch (error) {
      message.error('获取爬虫源失败');
    } finally {
      setLoadingSources(false);
    }
  };

  const fetchDatasets = async () => {
    try {
      const { data } = await api.get<Dataset[]>('/datasets/');
      setDatasets(data);
    } catch (error) {
      message.error('获取数据集失败');
    }
  };

  const availableSources = useMemo(() => {
    if (!sources.length) return [];
    return sources.map((source) => ({
      value: source,
      label: sourceDescriptions[source] || source,
    }));
  }, [sources, sourceDescriptions]);

  const handleStartNew = async (values: any) => {
    setCreatingNew(true);
    try {
      const payload = {
        source: values.source,
        keyword: values.keyword.trim(),
        max_pages: values.max_pages,
        dataset_name: values.dataset_name.trim(),
        description: values.description?.trim() || undefined,
      };
      const { data } = await api.post<CrawlResponse>('/spider/crawl', payload);
      message.success('已启动爬虫任务，稍后可在数据集页面查看进度');
      setResult(data);
      newForm.resetFields(['keyword']);
      fetchDatasets();
    } catch (error: any) {
      const detail = error.response?.data?.detail || '启动爬虫失败';
      message.error(detail);
    } finally {
      setCreatingNew(false);
    }
  };

  const handleAppend = async (values: any) => {
    setAppending(true);
    try {
      const payload = {
        source: values.source,
        keyword: values.keyword.trim(),
        max_pages: values.max_pages,
        dataset_id: values.dataset_id,
      };
      const { data } = await api.post<CrawlResponse>('/spider/crawl', payload);
      message.success('已为数据集追加爬虫任务');
      setResult(data);
      appendForm.resetFields(['keyword']);
      fetchDatasets();
    } catch (error: any) {
      const detail = error.response?.data?.detail || '启动爬虫失败';
      message.error(detail);
    } finally {
      setAppending(false);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        bordered={false}
        style={{
          background: 'linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)',
          color: 'white',
          borderRadius: 12,
        }}
      >
        <Row gutter={[24, 24]} align="middle">
          <Col xs={24} md={16}>
            <Title level={2} style={{ color: 'white', marginBottom: 12 }}>
              智能爬虫中心
            </Title>
            <Paragraph style={{ color: 'rgba(255,255,255,0.9)', fontSize: 16 }}>
              一键启动微博、抖音等平台的舆情采集任务，自动去重并同步情感分析结果。
            </Paragraph>
            <Space size="middle" wrap>
              {availableSources.map((source) => (
                <Tag key={source.value} color="rgba(255,255,255,0.25)" style={{ padding: '6px 16px' }}>
                  {source.label}
                </Tag>
              ))}
            </Space>
          </Col>
          <Col xs={24} md={8}>
            <Alert
              message="温馨提示"
              description="爬虫任务将在后台运行，数据写入后会自动完成情感分析。"
              type="info"
              showIcon
            />
          </Col>
        </Row>
      </Card>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <ThunderboltOutlined style={{ color: '#f97316' }} />
                <Text strong>新建数据集并启动爬虫</Text>
              </Space>
            }
            bordered={false}
            style={{ borderRadius: 16, boxShadow: '0 12px 40px rgba(99,102,241,0.08)' }}
          >
            <Form
              form={newForm}
              layout="vertical"
              onFinish={handleStartNew}
              initialValues={{ max_pages: 5 }}
            >
              <Form.Item
                name="dataset_name"
                label="数据集名称"
                rules={[{ required: true, message: '请输入数据集名称' }]}
              >
                <Input placeholder="例如：微博-山东大学舆情" allowClear />
              </Form.Item>

              <Form.Item
                name="description"
                label="数据集描述"
              >
                <Input.TextArea
                  rows={3}
                  placeholder="记录此次监测的目的、范围或背景"
                  allowClear
                />
              </Form.Item>

              <Form.Item
                name="source"
                label="数据来源平台"
                rules={[{ required: true, message: '请选择数据来源' }]}
              >
                <Select
                  placeholder="选择要爬取的平台"
                  options={availableSources}
                  loading={loadingSources}
                />
              </Form.Item>

              <Form.Item
                name="keyword"
                label="核心关键词"
                rules={[{ required: true, message: '请输入关键词' }]}
                extra="支持中文与英文，可包含品牌、事件、话题等多个词"
              >
                <Input placeholder="例如：山东大学 新生 报到" allowClear />
              </Form.Item>

              <Form.Item
                name="max_pages"
                label="采集页数"
                rules={[{ required: true, message: '请选择采集页数' }]}
                extra="每页约10条数据，页数越多耗时越长"
              >
                <InputNumber min={1} max={30} style={{ width: '100%' }} />
              </Form.Item>

              <Button
                type="primary"
                size="large"
                block
                icon={<PlayCircleOutlined />}
                loading={creatingNew}
                htmlType="submit"
              >
                启动新任务
              </Button>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <DeploymentUnitOutlined style={{ color: '#22c55e' }} />
                <Text strong>为已有数据集追加抓取</Text>
              </Space>
            }
            bordered={false}
            style={{ borderRadius: 16, boxShadow: '0 12px 40px rgba(34,197,94,0.08)' }}
          >
            <Form
              form={appendForm}
              layout="vertical"
              onFinish={handleAppend}
              initialValues={{ max_pages: 3 }}
            >
              <Form.Item
                name="dataset_id"
                label="目标数据集"
                rules={[{ required: true, message: '请选择数据集' }]}
              >
                <Select
                  placeholder="选择需要追加的现有数据集"
                  options={datasets.map((dataset) => ({
                    value: dataset.id,
                    label: `${dataset.name} (${dataset.record_count ?? dataset.total_records ?? 0} 条)`,
                  }))}
                  showSearch
                  optionFilterProp="label"
                />
              </Form.Item>

              <Form.Item
                name="source"
                label="数据来源平台"
                rules={[{ required: true, message: '请选择数据来源' }]}
              >
                <Select
                  placeholder="选择要爬取的平台"
                  options={availableSources}
                  loading={loadingSources}
                />
              </Form.Item>

              <Form.Item
                name="keyword"
                label="追加关键词"
                rules={[{ required: true, message: '请输入关键词' }]}
              >
                <Input placeholder="输入本次追加的关键词" allowClear />
              </Form.Item>

              <Form.Item
                name="max_pages"
                label="采集页数"
                rules={[{ required: true, message: '请选择采集页数' }]}
              >
                <InputNumber min={1} max={30} style={{ width: '100%' }} />
              </Form.Item>

              <Button
                type="default"
                size="large"
                block
                icon={<PlusCircleOutlined />}
                loading={appending}
                htmlType="submit"
              >
                追加到数据集
              </Button>
            </Form>
          </Card>
        </Col>
      </Row>

      {result && (
        <Card style={{ borderRadius: 16 }}>
          <Result
            status="success"
            title={`${result.dataset_name} 的爬虫任务已启动`}
            subTitle={`预估将采集约 ${result.estimated_records} 条数据，请稍后在数据集详情页查看最新记录。`}
            extra={
              <Space>
                <Button type="primary" onClick={() => navigate('/dashboard')}>
                  返回仪表盘
                </Button>
                <Button onClick={() => navigate(`/datasets/${result.dataset_id}`)}>
                  打开数据集
                </Button>
              </Space>
            }
          />
        </Card>
      )}

      <Divider />

      <Card title="使用建议" bordered={false} style={{ borderRadius: 16 }}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Text>• 关键词建议覆盖主体 + 行为 + 地点等组合，以提高命中率。</Text>
          <Text>• 同一关键词请合理控制任务频率，避免触发平台反爬策略。</Text>
          <Text>• 数据写入后会自动进行情感分析，可直接前往分析页面查看图表。</Text>
        </Space>
      </Card>
    </Space>
  );
};

export default SpiderPage;
