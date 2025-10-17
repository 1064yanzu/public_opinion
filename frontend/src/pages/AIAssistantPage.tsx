import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Typography,
  Space,
  Select,
  message,
  Tag,
  Row,
  Col,
  Checkbox,
  List,
  Tooltip,
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  StopOutlined,
  ReloadOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';
import type {
  Dataset,
  AIProvidersResponse,
  AIChatMessage,
  AIReportChunk,
} from '../types';

const { TextArea } = Input;
const { Title, Paragraph, Text } = Typography;

interface ChatBubble {
  role: 'user' | 'assistant';
  content: string;
}

const REPORT_SECTIONS = [
  { label: '舆情概览', value: 'overview' },
  { label: '核心洞察', value: 'analysis' },
  { label: '风险预警', value: 'risk' },
  { label: '应对策略', value: 'strategy' },
];

const SYSTEM_PROMPT = '你是一名经验丰富的数据分析顾问，擅长解读舆情数据、情感分析结果以及社交媒体互动指标。请用结构化的中文回答问题，并在需要时给出可执行的建议。';

const AIAssistantPage: React.FC = () => {
  const token = useAuthStore((state) => state.token);
  const [searchParams] = useSearchParams();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [providers, setProviders] = useState<string[]>([]);
  const [providerDescriptions, setProviderDescriptions] = useState<Record<string, string>>({});
  const [selectedProvider, setSelectedProvider] = useState<string | undefined>();

  const [chatConversation, setChatConversation] = useState<ChatBubble[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isStreamingChat, setIsStreamingChat] = useState(false);
  const [liveAssistantReply, setLiveAssistantReply] = useState('');
  const chatControllerRef = useRef<AbortController | null>(null);

  const [reportForm] = Form.useForm();
  const [chatForm] = Form.useForm();
  const [reportContent, setReportContent] = useState('');
  const [reportGenerating, setReportGenerating] = useState(false);
  const reportControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetchDatasets();
    fetchProviders();
  }, []);

  useEffect(() => {
    const datasetParam = searchParams.get('dataset');
    if (datasetParam) {
      const datasetId = Number(datasetParam);
      if (!Number.isNaN(datasetId)) {
        reportForm.setFieldsValue({ dataset_id: datasetId });
      }
    }
  }, [searchParams, reportForm]);

  const fetchDatasets = async () => {
    try {
      const { data } = await api.get<Dataset[]>('/datasets/');
      setDatasets(data);
    } catch (error) {
      message.error('获取数据集失败');
    }
  };

  const fetchProviders = async () => {
    try {
      const { data } = await api.get<AIProvidersResponse>('/ai/providers');
      setProviders(data.available || []);
      setProviderDescriptions(data.descriptions || {});
      setSelectedProvider((data.available || [])[0]);
    } catch (error) {
      message.error('获取AI服务商失败');
    }
  };

  const buildMessages = (conversation: ChatBubble[], userMessage: string): AIChatMessage[] => {
    const history: AIChatMessage[] = conversation.map((item) => ({
      role: item.role,
      content: item.content,
    }));
    return [{ role: 'system', content: SYSTEM_PROMPT }, ...history, { role: 'user', content: userMessage }];
  };

  const streamChat = async (messages: AIChatMessage[]) => {
    if (!token) {
      throw new Error('未登录或登录已过期');
    }

    const controller = new AbortController();
    chatControllerRef.current = controller;

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          messages,
          provider: selectedProvider,
          stream: true,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'AI 服务请求失败');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('浏览器不支持流式响应');
      }

      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let finalContent = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';
        for (const part of parts) {
          if (!part.trim()) continue;
          if (part.startsWith('data: ')) {
            const payload = part.slice(6).trim();
            if (payload === '[DONE]') {
              continue;
            }
            try {
              const chunk = JSON.parse(payload);
              if (chunk.content) {
                finalContent += chunk.content;
                setLiveAssistantReply((prev) => prev + chunk.content);
              }
            } catch (error) {
              console.warn('解析AI流式数据失败', error);
            }
          }
        }
      }

      return finalContent;
    } finally {
      chatControllerRef.current = null;
    }
  };

  const handleSendChat = async () => {
    const content = chatInput.trim();
    if (!content) {
      message.warning('请输入问题或需求');
      return;
    }
    if (!selectedProvider) {
      message.warning('请先选择AI服务商');
      return;
    }

    const updatedConversation = [...chatConversation, { role: 'user', content }];
    setChatConversation(updatedConversation);
    setChatInput('');
    setLiveAssistantReply('');
    setIsStreamingChat(true);

    try {
      const messages = buildMessages(chatConversation, content);
      const assistantReply = await streamChat(messages);
      if (assistantReply) {
        setChatConversation((prev) => [...prev, { role: 'assistant', content: assistantReply }]);
      }
    } catch (error: any) {
      const errorName = error?.name;
      if (errorName === 'AbortError' || errorName === 'DOMException') {
        message.info('已停止本次对话生成');
      } else {
        message.error(error?.message || 'AI 对话失败');
        setChatConversation((prev) => prev.slice(0, -1));
      }
    } finally {
      setIsStreamingChat(false);
      setLiveAssistantReply('');
    }
  };

  const handleStopChat = () => {
    chatControllerRef.current?.abort();
    chatControllerRef.current = null;
    setIsStreamingChat(false);
    setLiveAssistantReply('');
  };

  const streamReport = async (values: { dataset_id: number; sections?: string[] }) => {
    if (!token) {
      throw new Error('未登录或登录已过期');
    }

    const controller = new AbortController();
    reportControllerRef.current = controller;

    try {
      const response = await fetch('/api/ai/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          dataset_id: values.dataset_id,
          sections: values.sections?.length ? values.sections : undefined,
          provider: selectedProvider,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || '报告生成失败');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('浏览器不支持流式响应');
      }

      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let finalMarkdown = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';
        for (const part of parts) {
          if (!part.trim()) continue;
          if (part.startsWith('data: ')) {
            const payload = part.slice(6).trim();
            if (payload === '[DONE]') {
              continue;
            }
            try {
              const chunk: AIReportChunk = JSON.parse(payload);
              if (chunk.type && chunk.content) {
                finalMarkdown += chunk.content;
                setReportContent((prev) => prev + chunk.content);
              }
            } catch (error) {
              console.warn('解析报告流式数据失败', error);
            }
          }
        }
      }

      return finalMarkdown;
    } finally {
      reportControllerRef.current = null;
    }
  };

  const handleGenerateReport = async (values: { dataset_id: number; sections?: string[] }) => {
    if (!selectedProvider) {
      message.warning('请先选择AI服务商');
      return;
    }
    setReportContent('');
    setReportGenerating(true);
    try {
      await streamReport(values);
      message.success('报告生成完成');
    } catch (error: any) {
      const errorName = error?.name;
      if (errorName === 'AbortError' || errorName === 'DOMException') {
        message.info('已停止生成报告');
      } else {
        const detail = error?.message || '报告生成失败';
        message.error(detail);
      }
    } finally {
      setReportGenerating(false);
    }
  };

  const handleStopReport = () => {
    reportControllerRef.current?.abort();
    reportControllerRef.current = null;
    setReportGenerating(false);
  };

  const handleCopyReport = async () => {
    if (!reportContent) {
      message.info('暂无可复制的内容');
      return;
    }
    try {
      await navigator.clipboard.writeText(reportContent);
      message.success('报告内容已复制到剪贴板');
    } catch (error) {
      message.error('复制失败，请手动选择文本');
    }
  };

  const chatBubbles = useMemo(() => {
    const bubbles = [...chatConversation];
    if (isStreamingChat && liveAssistantReply) {
      bubbles.push({ role: 'assistant', content: liveAssistantReply });
    }
    return bubbles;
  }, [chatConversation, isStreamingChat, liveAssistantReply]);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        bordered={false}
        style={{
          background: 'linear-gradient(135deg, #f97316 0%, #6366f1 100%)',
          color: 'white',
          borderRadius: 12,
        }}
      >
        <Title level={2} style={{ color: 'white', marginBottom: 12 }}>
          AI 智能分析助手
        </Title>
        <Paragraph style={{ color: 'rgba(255,255,255,0.85)', fontSize: 16 }}>
          借助大模型快速生成舆情洞察、撰写分析报告，并获得实时的策略建议。
        </Paragraph>
        <Space wrap>
          {providers.map((provider) => (
            <Tag key={provider} color="rgba(255,255,255,0.25)" style={{ padding: '6px 16px' }}>
              {providerDescriptions[provider] || provider}
            </Tag>
          ))}
        </Space>
      </Card>

      <Card bordered={false} style={{ borderRadius: 16 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} md={12}>
              <Select
                value={selectedProvider}
                options={providers.map((provider) => ({
                  value: provider,
                  label: providerDescriptions[provider] || provider,
                }))}
                placeholder="选择AI服务商"
                onChange={setSelectedProvider}
                style={{ width: 280 }}
              />
            </Col>
            <Col xs={24} md={12}>
              <Text type="secondary">
                当前支持多家大模型厂商，推荐选择效果最佳的默认选项。
              </Text>
            </Col>
          </Row>

          <Tabs
            defaultActiveKey="chat"
            items={[
              {
                key: 'chat',
                label: (
                  <Space>
                    <RobotOutlined />
                    对话咨询
                  </Space>
                ),
                children: (
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <Card style={{ borderRadius: 16, maxHeight: 400, overflowY: 'auto' }}>
                      {chatBubbles.length === 0 ? (
                        <Space direction="vertical" align="center" style={{ width: '100%', padding: '60px 0' }}>
                          <RobotOutlined style={{ fontSize: 40, color: '#6366f1' }} />
                          <Text type="secondary">向我提问：例如“基于最新数据集总结情绪趋势”</Text>
                        </Space>
                      ) : (
                        <List
                          dataSource={chatBubbles}
                          renderItem={(item, index) => (
                            <List.Item key={`${item.role}-${index}`} style={{ border: 'none', padding: '12px 0' }}>
                              <div
                                style={{
                                  maxWidth: '80%',
                                  marginLeft: item.role === 'assistant' ? 0 : 'auto',
                                  textAlign: item.role === 'assistant' ? 'left' : 'right',
                                }}
                              >
                                <div
                                  style={{
                                    display: 'inline-block',
                                    padding: '12px 16px',
                                    borderRadius: 16,
                                    background: item.role === 'assistant' ? '#f4f8ff' : 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                                    color: item.role === 'assistant' ? '#1f2937' : 'white',
                                    boxShadow: '0 10px 30px rgba(99,102,241,0.08)',
                                  }}
                                >
                                  {item.content}
                                </div>
                              </div>
                            </List.Item>
                          )}
                        />
                      )}
                    </Card>

                    <Form form={chatForm} onFinish={handleSendChat} style={{ width: '100%' }}>
                      <TextArea
                        rows={3}
                        value={chatInput}
                        onChange={(event) => setChatInput(event.target.value)}
                        placeholder="请输入你的问题，例如：帮我总结近期负面舆情的原因"
                        allowClear
                      />
                      <Space style={{ marginTop: 12, justifyContent: 'space-between', width: '100%' }}>
                        <Text type="secondary">提示：可以结合具体数据集或情感指标进行提问。</Text>
                        <Space>
                          {isStreamingChat ? (
                            <Button icon={<StopOutlined />} onClick={handleStopChat} danger>
                              停止
                            </Button>
                          ) : (
                            <Button
                              type="primary"
                              icon={<SendOutlined />}
                              onClick={handleSendChat}
                              disabled={isStreamingChat || !chatInput.trim()}
                            >
                              发送
                            </Button>
                          )}
                          <Button
                            icon={<ReloadOutlined />}
                            onClick={() => {
                              setChatConversation([]);
                              setLiveAssistantReply('');
                              setChatInput('');
                            }}
                          >
                            清空对话
                          </Button>
                        </Space>
                      </Space>
                    </Form>
                  </Space>
                ),
              },
              {
                key: 'report',
                label: (
                  <Space>
                    <RobotOutlined />
                    报告生成
                  </Space>
                ),
                children: (
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <Form
                      layout="vertical"
                      form={reportForm}
                      onFinish={handleGenerateReport}
                      initialValues={{ sections: REPORT_SECTIONS.map((item) => item.value) }}
                    >
                      <Row gutter={[16, 0]}>
                        <Col xs={24} md={12}>
                          <Form.Item
                            name="dataset_id"
                            label="选择数据集"
                            rules={[{ required: true, message: '请选择数据集' }]}
                          >
                            <Select
                              placeholder="选择需要生成报告的数据集"
                              options={datasets.map((dataset) => ({
                                value: dataset.id,
                                label: `${dataset.name} (${dataset.record_count ?? dataset.total_records ?? 0} 条)`,
                              }))}
                              showSearch
                              optionFilterProp="label"
                            />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="sections" label="报告模块">
                            <Checkbox.Group options={REPORT_SECTIONS} style={{ width: '100%' }} />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Space>
                        {reportGenerating ? (
                          <Button icon={<StopOutlined />} danger onClick={handleStopReport}>
                            停止生成
                          </Button>
                        ) : (
                          <Button type="primary" icon={<SendOutlined />} htmlType="submit">
                            生成AI报告
                          </Button>
                        )}
                        <Button icon={<CopyOutlined />} onClick={handleCopyReport} disabled={!reportContent}>
                          复制内容
                        </Button>
                      </Space>
                    </Form>

                    <Card style={{ borderRadius: 16, minHeight: 320 }}>
                      {reportContent ? (
                        <pre style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontFamily: 'inherit' }}>
                          {reportContent}
                        </pre>
                      ) : (
                        <Space direction="vertical" align="center" style={{ width: '100%', padding: '40px 0' }}>
                          <RobotOutlined style={{ fontSize: 40, color: '#6366f1' }} />
                          <Text type="secondary">选择数据集并点击生成，即可获得Markdown格式的智能报告</Text>
                        </Space>
                      )}
                    </Card>
                  </Space>
                ),
              },
            ]}
          />
        </Space>
      </Card>
    </Space>
  );
};

export default AIAssistantPage;
