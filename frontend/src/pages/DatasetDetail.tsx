import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Tabs,
  Popconfirm,
  Typography,
  Progress,
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
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../services/api';
import type { Dataset, DataRecord } from '../types';

const { Title, Text } = Typography;
const { TextArea } = Input;

const DatasetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [bulkModalVisible, setBulkModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [bulkForm] = Form.useForm();

  useEffect(() => {
    if (id) {
      fetchDataset();
      fetchRecords();
    }
  }, [id]);

  const fetchDataset = async () => {
    try {
      const { data } = await api.get<Dataset>(`/datasets/${id}`);
      setDataset(data);
    } catch (error) {
      message.error('获取数据集信息失败');
    }
  };

  const fetchRecords = async () => {
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
    try {
      await api.post('/records/', {
        ...values,
        dataset_id: parseInt(id!),
      });
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
    try {
      const lines = values.content.split('\n').filter((line: string) => line.trim());
      await api.post('/records/bulk', {
        dataset_id: parseInt(id!),
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
    } catch (error) {
      message.error('上传失败');
    }

    return false;
  };

  const getSentimentIcon = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive':
        return <SmileOutlined style={{ color: '#52c41a' }} />;
      case 'negative':
        return <FrownOutlined style={{ color: '#ff4d4f' }} />;
      case 'neutral':
      default:
        return <MehOutlined style={{ color: '#faad14' }} />;
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
        return 'warning';
    }
  };

  const columns: ColumnsType<DataRecord> = [
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      width: 400,
    },
    {
      title: '情感',
      dataIndex: 'sentiment',
      key: 'sentiment',
      width: 100,
      render: (sentiment) => (
        <Space>
          {getSentimentIcon(sentiment)}
          <Tag color={getSentimentColor(sentiment)}>
            {sentiment === 'positive' ? '正面' : sentiment === 'negative' ? '负面' : '中性'}
          </Tag>
        </Space>
      ),
    },
    {
      title: '情感得分',
      dataIndex: 'sentiment_score',
      key: 'sentiment_score',
      width: 150,
      render: (score) => (
        score !== null && score !== undefined ? (
          <Progress
            percent={Math.round(score * 100)}
            size="small"
            status={score > 0.6 ? 'success' : score < 0.4 ? 'exception' : 'normal'}
          />
        ) : '-'
      ),
    },
    {
      title: '作者',
      dataIndex: 'author',
      key: 'author',
      width: 120,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
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
          <Button type="link" danger size="small" icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  if (!dataset) {
    return <div>Loading...</div>;
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ color: 'white', margin: 0 }}>
              {dataset.name}
            </Title>
            <p style={{ margin: '8px 0 0', color: 'rgba(255,255,255,0.9)' }}>
              {dataset.description || '暂无描述'}
            </p>
          </div>
          <Space>
            <Button
              icon={<BarChartOutlined />}
              onClick={() => navigate(`/analytics/${id}`)}
              size="large"
              style={{
                background: 'white',
                color: '#667eea',
                border: 'none',
              }}
            >
              查看分析
            </Button>
          </Space>
        </div>
      </Card>

      <Card style={{ borderRadius: 12 }}>
        <Descriptions column={3}>
          <Descriptions.Item label="数据源">{dataset.source_type}</Descriptions.Item>
          <Descriptions.Item label="记录数">{dataset.record_count || 0}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(dataset.created_at).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        title="数据记录"
        extra={
          <Space>
            <Upload beforeUpload={handleUpload} showUploadList={false}>
              <Button icon={<UploadOutlined />}>上传文件</Button>
            </Upload>
            <Button
              icon={<PlusOutlined />}
              onClick={() => setBulkModalVisible(true)}
            >
              批量添加
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setModalVisible(true)}
            >
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
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateRecord}>
          <Form.Item
            name="content"
            label="内容"
            rules={[{ required: true, message: '请输入内容' }]}
          >
            <TextArea rows={4} placeholder="输入数据内容" />
          </Form.Item>

          <Form.Item name="author" label="作者">
            <Input placeholder="作者名称（可选）" />
          </Form.Item>

          <Form.Item name="source_url" label="来源URL">
            <Input placeholder="数据来源链接（可选）" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="批量添加记录"
        open={bulkModalVisible}
        onCancel={() => setBulkModalVisible(false)}
        onOk={() => bulkForm.submit()}
        width={600}
      >
        <Form form={bulkForm} layout="vertical" onFinish={handleBulkCreate}>
          <Form.Item
            name="content"
            label="批量内容"
            rules={[{ required: true, message: '请输入内容' }]}
            extra="每行一条记录"
          >
            <TextArea
              rows={10}
              placeholder="输入多条数据，每行一条记录"
            />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
};

export default DatasetDetail;
