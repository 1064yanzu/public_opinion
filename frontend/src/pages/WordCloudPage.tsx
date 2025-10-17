import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Card,
  Form,
  Select,
  InputNumber,
  Button,
  Typography,
  Space,
  Row,
  Col,
  Statistic,
  message,
  List,
  Tooltip,
  Divider,
} from 'antd';
import {
  CloudOutlined,
  DownloadOutlined,
  ReloadOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import type { Dataset, WordCloudResponse } from '../types';

const { Title, Paragraph, Text } = Typography;

const COLOR_MAP_OPTIONS = [
  'viridis',
  'plasma',
  'inferno',
  'magma',
  'cividis',
  'turbo',
  'cool',
  'spring',
  'autumn',
];

const WordCloudPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [wordCloud, setWordCloud] = useState<WordCloudResponse | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchDatasets();
  }, []);

  useEffect(() => {
    const datasetParam = searchParams.get('dataset');
    if (datasetParam) {
      form.setFieldsValue({ dataset_id: Number(datasetParam) });
    }
  }, [searchParams, form, datasets]);

  const fetchDatasets = async () => {
    setLoadingDatasets(true);
    try {
      const { data } = await api.get<Dataset[]>('/datasets/');
      setDatasets(data);
      if (data.length && !form.getFieldValue('dataset_id')) {
        form.setFieldsValue({ dataset_id: data[0].id });
      }
    } catch (error) {
      message.error('获取数据集失败');
    } finally {
      setLoadingDatasets(false);
    }
  };

  const handleGenerate = async (values: any) => {
    setGenerating(true);
    try {
      const payload = {
        dataset_id: values.dataset_id,
        max_words: values.max_words,
        colormap: values.colormap,
        width: values.width,
        height: values.height,
      };
      const { data } = await api.post<WordCloudResponse>('/wordcloud/generate', payload);
      setWordCloud(data);
      message.success('词云生成成功');
    } catch (error: any) {
      const detail = error.response?.data?.detail || '生成失败';
      message.error(detail);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!wordCloud) return;
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${wordCloud.image_base64}`;
    link.download = `${wordCloud.dataset.name}-wordcloud.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const currentDataset = useMemo(
    () => datasets.find((item) => item.id === wordCloud?.dataset.id),
    [datasets, wordCloud]
  );

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        bordered={false}
        style={{
          background: 'linear-gradient(135deg, #22d3ee 0%, #6366f1 100%)',
          color: 'white',
          borderRadius: 12,
        }}
      >
        <Row gutter={[24, 24]} align="middle">
          <Col xs={24} md={16}>
            <Title level={2} style={{ color: 'white', marginBottom: 12 }}>
              词云分析实验室
            </Title>
            <Paragraph style={{ color: 'rgba(255,255,255,0.9)', fontSize: 16 }}>
              根据文本语料自动生成高颜值词云，快速洞察舆情关键词与关注焦点。
            </Paragraph>
            <Space size="large" wrap>
              <Statistic title="可选调色板" value={COLOR_MAP_OPTIONS.length} valueStyle={{ color: 'white' }} />
              <Statistic title="支持分辨率" value="1600 × 1200" valueStyle={{ color: 'white' }} />
            </Space>
          </Col>
          <Col xs={24} md={8}>
            <Text style={{ color: 'rgba(255,255,255,0.85)' }}>
              提示：词云生成会遵循停用词过滤与分词策略，建议在生成前清理无意义字符以获得更佳效果。
            </Text>
          </Col>
        </Row>
      </Card>

      <Card bordered={false} style={{ borderRadius: 16, boxShadow: '0 12px 40px rgba(34,197,94,0.08)' }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleGenerate}
          initialValues={{
            max_words: 150,
            colormap: 'viridis',
            width: 800,
            height: 600,
          }}
        >
          <Row gutter={[24, 0]}>
            <Col xs={24} md={12}>
              <Form.Item
                name="dataset_id"
                label="选择数据集"
                rules={[{ required: true, message: '请选择数据集' }]}
              >
                <Select
                  placeholder="选择要生成词云的数据集"
                  options={datasets.map((dataset) => ({
                    value: dataset.id,
                    label: `${dataset.name} (${dataset.record_count ?? dataset.total_records ?? 0} 条)`,
                  }))}
                  loading={loadingDatasets}
                  showSearch
                  optionFilterProp="label"
                  allowClear
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="colormap"
                label="配色方案"
                rules={[{ required: true, message: '请选择配色方案' }]}
              >
                <Select
                  options={COLOR_MAP_OPTIONS.map((palette) => ({ value: palette, label: palette }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={[24, 0]}>
            <Col xs={24} md={8}>
              <Form.Item
                name="max_words"
                label="最大词汇数量"
                rules={[{ required: true, message: '请输入最大词汇数量' }]}
              >
                <InputNumber min={10} max={500} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                name="width"
                label="图像宽度"
                rules={[{ required: true, message: '请输入宽度' }]}
              >
                <InputNumber min={300} max={1600} step={50} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                name="height"
                label="图像高度"
                rules={[{ required: true, message: '请输入高度' }]}
              >
                <InputNumber min={300} max={1200} step={50} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Space size="middle">
            <Button type="primary" icon={<CloudOutlined />} size="large" loading={generating} htmlType="submit">
              生成词云
            </Button>
            <Button
              icon={<ReloadOutlined />}
              size="large"
              onClick={() => {
                form.resetFields();
                setWordCloud(null);
              }}
            >
              重置
            </Button>
          </Space>
        </Form>
      </Card>

      {wordCloud && (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={14}>
            <Card
              title={
                <Space>
                  <CloudOutlined />
                  <Text strong>{wordCloud.dataset.name} - 词云结果</Text>
                </Space>
              }
              extra={
                <Space>
                  <Tooltip title="下载词云 PNG 图片">
                    <Button icon={<DownloadOutlined />} onClick={handleDownload}>
                      下载图片
                    </Button>
                  </Tooltip>
                  <Tooltip title="查看数据集详情">
                    <Button icon={<EyeOutlined />} onClick={() => navigate(`/datasets/${wordCloud.dataset.id}`)}>
                      打开数据集
                    </Button>
                  </Tooltip>
                </Space>
              }
              bordered={false}
              style={{ borderRadius: 16 }}
            >
              <div
                style={{
                  width: '100%',
                  minHeight: 420,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: '#0f172a',
                  borderRadius: 12,
                  overflow: 'hidden',
                }}
              >
                <img
                  src={`data:image/png;base64,${wordCloud.image_base64}`}
                  alt="词云图"
                  style={{
                    maxWidth: '100%',
                    height: 'auto',
                    display: 'block',
                  }}
                />
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={10}>
            <Card
              title="高频关键词"
              extra={<Text type="secondary">展示前 20 个关键词及出现频次</Text>}
              bordered={false}
              style={{ borderRadius: 16 }}
            >
              <List
                dataSource={Object.entries(wordCloud.word_frequencies)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 20)}
                renderItem={([word, count], index) => (
                  <List.Item key={word}>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Space size="middle">
                        <Tag color={index < 3 ? 'magenta' : 'blue'}>#{index + 1}</Tag>
                        <Text strong>{word}</Text>
                      </Space>
                      <Text type="secondary">{count} 次</Text>
                    </Space>
                  </List.Item>
                )}
              />
              <Divider />
              <Space direction="vertical" size="small">
                <Text type="secondary">共分析词语：{wordCloud.total_words}</Text>
                <Text type="secondary">独立词语：{wordCloud.unique_words}</Text>
                {currentDataset && (
                  <Text type="secondary">
                    数据集来源：{currentDataset.source_type || currentDataset.source}
                  </Text>
                )}
              </Space>
            </Card>
          </Col>
        </Row>
      )}
    </Space>
  );
};

export default WordCloudPage;
