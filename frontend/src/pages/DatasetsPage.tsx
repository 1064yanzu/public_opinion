import React, { useEffect, useState } from 'react';
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
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  BarChartOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../services/api';
import type { Dataset } from '../types';

const { Title } = Typography;
const { TextArea } = Input;

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
    form.setFieldsValue(dataset);
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
    try {
      if (editingDataset) {
        await api.put(`/datasets/${editingDataset.id}`, values);
        message.success('更新成功');
      } else {
        await api.post('/datasets/', values);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchDatasets();
    } catch (error) {
      message.error(editingDataset ? '更新失败' : '创建失败');
    }
  };

  const columns: ColumnsType<Dataset> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
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
      dataIndex: 'source_type',
      key: 'source_type',
      render: (type) => {
        const colorMap: Record<string, string> = {
          manual: 'blue',
          weibo: 'orange',
          douyin: 'pink',
          api: 'green',
          upload: 'purple',
        };
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>;
      },
    },
    {
      title: '记录数',
      dataIndex: 'record_count',
      key: 'record_count',
      render: (count) => count || 0,
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
      width: 250,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<BarChartOutlined />}
            onClick={() => navigate(`/analytics/${record.id}`)}
          >
            分析
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个数据集吗？"
            description="删除后数据将无法恢复"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

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
            <p style={{ margin: '8px 0 0', color: 'rgba(255,255,255,0.9)' }}>
              管理您的所有数据集，支持多种数据源
            </p>
          </div>
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
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="数据集名称"
            rules={[{ required: true, message: '请输入数据集名称' }]}
          >
            <Input placeholder="例如：微博热点数据" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              rows={3}
              placeholder="描述数据集的内容和用途"
            />
          </Form.Item>

          <Form.Item
            name="source_type"
            label="数据源类型"
            rules={[{ required: true, message: '请选择数据源类型' }]}
          >
            <Select placeholder="选择数据源">
              <Select.Option value="manual">手动录入</Select.Option>
              <Select.Option value="weibo">微博</Select.Option>
              <Select.Option value="douyin">抖音</Select.Option>
              <Select.Option value="api">API</Select.Option>
              <Select.Option value="upload">文件上传</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
};

export default DatasetsPage;
