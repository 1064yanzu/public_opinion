import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Table,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Typography,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  BarChartOutlined,
  DatabaseOutlined,
  CloudUploadOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../services/api';
import type { Dataset } from '../types';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

const DATA_SOURCE_OPTIONS = [
  { value: 'manual', label: '手动录入' },
  { value: 'import', label: '文件导入' },
  { value: 'weibo', label: '微博爬虫' },
  { value: 'douyin', label: '抖音爬虫' },
];

const SOURCE_COLOR_MAP: Record<string, string> = {
  manual: 'blue',
  import: 'purple',
  weibo: 'orange',
  douyin: 'magenta',
};

const DatasetsPage: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingDataset, setEditingDataset] = useState<Dataset | null>(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const { data } = await api.get<Dataset[]>('/datasets/');
      setDatasets(data);
    } catch (error) {
      message.error('获取数据集列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingDataset(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (dataset: Dataset) => {
    setEditingDataset(dataset);
    form.setFieldsValue({
      name: dataset.name,
      description: dataset.description,
      source: dataset.source,
      keyword: dataset.keyword,
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/datasets/${id}`);
      message.success('删除成功');
      fetchDatasets();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSubmit = async (values: any) => {
    const payload = editingDataset
      ? {
          name: values.name,
          description: values.description,
        }
      : {
          name: values.name,
          description: values.description,
          source: values.source,
          keyword: values.keyword?.trim() || undefined,
        };

    try {
      if (editingDataset) {
        await api.put(`/datasets/${editingDataset.id}`, payload);
        message.success('更新成功');
      } else {
        await api.post('/datasets/', payload);
        message.success('创建成功，爬取或导入数据后即可开始分析');
      }
      setModalVisible(false);
      fetchDatasets();
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      message.error(detail || (editingDataset ? '更新失败' : '创建失败'));
    }
  };

  const renderSourceTag = (source?: string) => {
    if (!source) return <Tag>未知</Tag>;
    return (
      <Tag color={SOURCE_COLOR_MAP[source] || 'default'}>
        {DATA_SOURCE_OPTIONS.find((item) => item.value === source)?.label || source}
      </Tag>
    );
  };

  const columns: ColumnsType<Dataset> = useMemo(
    () => [
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
        render: (text, record) => (
          <Space size={8}>
            <DatabaseOutlined style={{ color: '#6366f1' }} />
            <a onClick={() => navigate(`/datasets/${record.id}`)}>{text}</a>
          </Space>
        ),
      },
      {
        title: '描述',
        dataIndex: 'description',
        key: 'description',
        ellipsis: true,
      },
      {
        title: '数据源',
        dataIndex: 'source',
        key: 'source',
        render: (source: string, record) => renderSourceTag(source || record.source_type),
      },
      {
        title: '关键字',
        dataIndex: 'keyword',
        key: 'keyword',
        render: (keyword?: string | null) => keyword || '—',
      },
      {
        title: '记录数',
        dataIndex: 'record_count',
        key: 'record_count',
        render: (count, record) => count ?? record.total_records ?? 0,
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        render: (date) => new Date(date).toLocaleString(),
      },
      {
        title: '操作',
        key: 'actions',
        width: 280,
        render: (_, record) => (
          <Space size="middle">
            <Button
              type="link"
              icon={<BarChartOutlined />}
              onClick={() => navigate(`/analytics/${record.id}`)}
            >
              分析
            </Button>
            <Button
              type="link"
              icon={<CloudUploadOutlined />}
              onClick={() => navigate(`/datasets/${record.id}`)}
            >
              管理数据
            </Button>
            <Tooltip title="编辑名称与描述">
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
            </Tooltip>
            <Popconfirm
              title="确定要删除这个数据集吗？"
              description="删除后数据将无法恢复"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [navigate]
  );

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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ color: 'white', margin: 0 }}>
              数据集管理
            </Title>
            <Paragraph style={{ margin: '8px 0 0', color: 'rgba(255,255,255,0.85)' }}>
              统一管理微博、抖音、手动录入等多数据源，支持导入、爬取与分析全流程
            </Paragraph>
          </div>
          <Space size="middle">
            <Button
              type="primary"
              size="large"
              icon={<SearchOutlined />}
              onClick={() => navigate('/spider')}
              style={{
                background: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: 'none',
              }}
            >
              爬取数据
            </Button>
            <Button
              type="primary"
              size="large"
              icon={<PlusOutlined />}
              onClick={handleCreate}
              style={{
                background: 'white',
                color: '#667eea',
                border: 'none',
              }}
            >
              创建数据集
            </Button>
          </Space>
        </div>
      </Card>

      <Card style={{ borderRadius: 12 }}>
        <Table
          columns={columns}
          dataSource={datasets}
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
        title={editingDataset ? '编辑数据集' : '创建数据集'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={620}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ source: 'manual' }}
        >
          <Form.Item
            name="name"
            label="数据集名称"
            rules={[{ required: true, message: '请输入数据集名称' }]}
          >
            <Input placeholder="例如：微博-人工智能舆情" allowClear />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              rows={3}
              placeholder="描述数据集的内容、来源或监测目的"
              allowClear
            />
          </Form.Item>

          <Form.Item
            name="keyword"
            label="默认关键字"
            extra="用于爬虫任务或快速检索，可在后续任务中修改"
          >
            <Input placeholder="如需使用爬虫，请填写核心关键词" allowClear />
          </Form.Item>

          <Form.Item
            name="source"
            label="数据源类型"
            rules={[{ required: true, message: '请选择数据源类型' }]}
          >
            <Select
              placeholder="选择数据源"
              options={DATA_SOURCE_OPTIONS}
              disabled={Boolean(editingDataset)}
            />
          </Form.Item>

          {editingDataset && (
            <Text type="secondary">
              如需调整数据源或关键字，请在爬虫页面发起新的任务。
            </Text>
          )}
        </Form>
      </Modal>
    </Space>
  );
};

export default DatasetsPage;
