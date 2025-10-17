import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Upload,
  message,
  Descriptions,
  Typography,
  Progress,
  Popconfirm,
  Tooltip,
} from 'antd';
import {
  UploadOutlined,
  PlusOutlined,
  DeleteOutlined,
  BarChartOutlined,
  ArrowLeftOutlined,
  SmileOutlined,
  MehOutlined,
  FrownOutlined,
  CloudOutlined,
  RobotOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../services/api';
import type { Dataset, DataRecord } from '../types';

const { Title } = Typography;
const { TextArea } = Input;

const SENTIMENT_TAG_MAP: Record<string, { color: string; label: string; icon: React.ReactNode }> = {
  positive: { color: 'success', label: '正面', icon: <SmileOutlined style={{ color: '#22c55e' }} /> },
  neutral: { color: 'warning', label: '中性', icon: <MehOutlined style={{ color: '#faad14' }} /> },
  negative: { color: 'error', label: '负面', icon: <FrownOutlined style={{ color: '#ff4d4f' }} /> },
};

const SOURCE_TEXT: Record<string, string> = {
  manual: '手动录入',
  import: '文件导入',
  weibo: '微博爬虫',
  douyin: '抖音爬虫',
};

const DatasetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [bulkModalVisible, setBulkModalVisible] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [form] = Form.useForm();
  const [bulkForm] = Form.useForm();

  useEffect(() => {
    if (id) {
      fetchDataset();
      fetchRecords();
    }
  }, [id]);

  const fetchDataset = async () => {
    if (!id) return;
    try {
      const { data } = await api.get<Dataset>(`/datasets/${id}`);
      setDataset(data);
    } catch (error) {
      message.error('获取数据集信息失败');
    }
  };

  const fetchRecords = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const { data } = await api.get<DataRecord[]>(`/datasets/${id}/records`);
      setRecords(data);
    } catch (error) {
      message.error('获取记录列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRecord = async (values: any) => {
    if (!id) return;
    try {
      const payload = {
        dataset_id: Number(id),
        content: values.content,
        author: values.author,
      };

      await api.post('/records/', payload);
      message.success('创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchRecords();
      fetchDataset();
    } catch (error) {
      message.error('创建失败');
    }
  };

  const handleBulkCreate = async (values: any) => {
    if (!id) return;
    try {
      const lines = values.content
        .split('\n')
        .map((line: string) => line.trim())
        .filter(Boolean);

      if (!lines.length) {
        message.warning('请输入至少一条记录');
        return;
      }

      await api.post('/records/bulk', {
        dataset_id: Number(id),
        contents: lines,
      });
      message.success('批量创建成功，正在后台处理');
      setBulkModalVisible(false);
      bulkForm.resetFields();
      setTimeout(() => {
        fetchRecords();
        fetchDataset();
      }, 2000);
    } catch (error) {
      message.error('批量创建失败');
    }
  };

  const handleDelete = async (recordId: number) => {
    try {
      await api.delete(`/records/${recordId}`);
      message.success('删除成功');
      fetchRecords();
      fetchDataset();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleUpload = async (file: File) => {
    if (!id) return false;
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post(`/datasets/${id}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      message.success('上传成功，正在处理数据');
      setTimeout(() => {
        fetchRecords();
        fetchDataset();
      }, 2000);
    } catch (error: any) {
      const detail = error.response?.data?.detail || '上传失败';
      message.error(detail);
    }

    return false;
  };

  const handleExport = async () => {
    if (!id) return;
    setExporting(true);
    try {
      const response = await api.get(`/datasets/${id}/export`, { responseType: 'blob' });
      const disposition = response.headers['content-disposition'] as string | undefined;
      let filename = dataset?.name ? `${dataset.name}.csv` : `dataset-${id}.csv`;
      if (disposition) {
        const match = disposition.match(/filename="?([^";]+)"?/);
        if (match && match[1]) {
          filename = decodeURIComponent(match[1]);
        }
      }
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      message.success('已导出CSV文件');
    } catch (error: any) {
      const detail = error.response?.data?.detail || '导出失败';
      message.error(detail);
    } finally {
      setExporting(false);
    }
  };

  const navigateToWordcloud = () => {
    if (!dataset) return;
    navigate(`/wordcloud?dataset=${dataset.id}`);
  };

  const navigateToAI = () => {
    if (!dataset) return;
    navigate(`/ai?dataset=${dataset.id}`);
  };

  const sentimentColumnRender = (sentiment?: string) => {
    const info = sentiment ? SENTIMENT_TAG_MAP[sentiment] : undefined;
    if (!info) {
      return <Tag>未知</Tag>;
    }
    return (
      <Space size={6}>
        {info.icon}
        <Tag color={info.color}>{info.label}</Tag>
      </Space>
    );
  };

  const columns: ColumnsType<DataRecord> = useMemo(
    () => [
      {
        title: '内容',
        dataIndex: 'content',
        key: 'content',
        ellipsis: true,
        width: 420,
      },
      {
        title: '情感',
        dataIndex: 'sentiment',
        key: 'sentiment',
        width: 140,
        render: sentimentColumnRender,
      },
      {
        title: '情感得分',
        dataIndex: 'sentiment_score',
        key: 'sentiment_score',
        width: 160,
        render: (score) =>
          score !== null && score !== undefined ? (
            <Progress
              percent={Math.round(score * 100)}
              size="small"
              status={score > 0.6 ? 'success' : score < 0.4 ? 'exception' : 'normal'}
            />
          ) : (
            '—'
          ),
      },
      {
        title: '作者',
        dataIndex: 'author',
        key: 'author',
        width: 140,
        render: (author?: string) => author || '—',
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 190,
        render: (date) => new Date(date).toLocaleString(),
      },
      {
        title: '操作',
        key: 'actions',
        width: 100,
        render: (_, record) => (
          <Popconfirm
            title="确定要删除这条记录吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        ),
      },
    ],
    []
  );

  useEffect(() => {
    const autoOpenModal = searchParams.get('create');
    if (autoOpenModal === '1') {
      setModalVisible(true);
    }
  }, [searchParams]);

  if (!dataset) {
    return (
      <Card style={{ borderRadius: 12 }}>
        <Space direction="vertical" style={{ width: '100%', alignItems: 'center', padding: '60px 0' }}>
          <Typography.Title level={4}>正在加载数据集...</Typography.Title>
        </Space>
      </Card>
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
          onClick={() => navigate('/datasets')}
          style={{
            background: 'rgba(255,255,255,0.2)',
            color: 'white',
            border: 'none',
            marginBottom: 16,
          }}
        >
          返回
        </Button>
        <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <Title level={2} style={{ color: 'white', margin: 0 }}>
              {dataset.name}
            </Title>
            <p style={{ margin: '8px 0 0', color: 'rgba(255,255,255,0.85)' }}>
              {dataset.description || '暂无描述'}
            </p>
          </div>
          <Space size="middle" wrap>
            <Tooltip title="转到分析页查看图表洞察">
              <Button
                icon={<BarChartOutlined />}
                onClick={() => navigate(`/analytics/${dataset.id}`)}
              >
                查看分析
              </Button>
            </Tooltip>
            <Tooltip title="一键生成高颜值词云图">
              <Button
                icon={<CloudOutlined />}
                onClick={navigateToWordcloud}
              >
                词云分析
              </Button>
            </Tooltip>
            <Tooltip title="调用大模型快速生成洞察与报告">
              <Button
                icon={<RobotOutlined />}
                onClick={navigateToAI}
              >
                AI助手
              </Button>
            </Tooltip>
            <Tooltip title="导出全部记录为CSV文件">
              <Button
                icon={<DownloadOutlined />}
                loading={exporting}
                onClick={handleExport}
              >
                导出CSV
              </Button>
            </Tooltip>
          </Space>
        </div>
      </Card>

      <Card style={{ borderRadius: 12 }}>
        <Descriptions column={3} layout="horizontal">
          <Descriptions.Item label="数据源">
            <Tag color="processing">{SOURCE_TEXT[dataset.source] || dataset.source_type || '未知'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="记录数">{dataset.record_count ?? dataset.total_records ?? 0}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{new Date(dataset.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="关键字">{dataset.keyword || '—'}</Descriptions.Item>
          <Descriptions.Item label="最近更新">{dataset.updated_at ? new Date(dataset.updated_at).toLocaleString() : '—'}</Descriptions.Item>
          <Descriptions.Item label="数据集ID">{dataset.id}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        title="数据记录"
        extra={
          <Space size="middle">
            <Upload beforeUpload={handleUpload} showUploadList={false} accept=".csv,.xlsx">
              <Button icon={<UploadOutlined />}>上传文件</Button>
            </Upload>
            <Button icon={<PlusOutlined />} onClick={() => setBulkModalVisible(true)}>
              批量添加
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
              添加记录
            </Button>
          </Space>
        }
        style={{ borderRadius: 12 }}
      >
        <Table
          columns={columns}
          dataSource={records}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      <Modal
        title="添加记录"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={640}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateRecord}>
          <Form.Item
            name="content"
            label="内容"
            rules={[{ required: true, message: '请输入内容' }]}
          >
            <TextArea rows={4} placeholder="输入数据内容" allowClear />
          </Form.Item>

          <Form.Item name="author" label="作者">
            <Input placeholder="作者名称（可选）" allowClear />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="批量添加记录"
        open={bulkModalVisible}
        onCancel={() => setBulkModalVisible(false)}
        onOk={() => bulkForm.submit()}
        width={640}
      >
        <Form form={bulkForm} layout="vertical" onFinish={handleBulkCreate}>
          <Form.Item
            name="content"
            label="批量内容"
            rules={[{ required: true, message: '请输入内容' }]}
            extra="每行一条记录，系统会自动进行情感分析"
          >
            <TextArea
              rows={10}
              placeholder="输入多条数据，每行一条记录"
              allowClear
            />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
};

export default DatasetDetail;
