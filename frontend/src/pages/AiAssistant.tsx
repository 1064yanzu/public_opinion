import React, { useState, useEffect, useRef } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Button } from '@/components/common/Button';
import { Send, User as UserIcon, Bot, Trash2 } from 'lucide-react';
import api from '@/services/api';
import styles from './AiAssistant.module.css';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export const AiAssistant: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchHistory();
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const fetchHistory = async () => {
        try {
            const res = await api.get('/ai/chat-history');
            if (Array.isArray(res.data?.history)) {
                setMessages(res.data.history);
            }
        } catch (err) {
            console.error('Failed to load chat history', err);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSend = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMsg: Message = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            const res = await api.post('/ai/chat', {
                message: userMsg.content,
                history: messages,
                stream: false,
            });
            const botMsg: Message = { role: 'assistant', content: res.data.message };
            setMessages(prev => [...prev, botMsg]);
        } catch (err) {
            const errorMsg: Message = { role: 'assistant', content: '抱歉，我遇到了一些问题，请稍后再试。' };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleClear = async () => {
        try {
            await api.post('/ai/clear-chat');
            setMessages([]);
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <MainLayout>
            <div className={styles.container}>
                <div className={styles.header}>
                    <div>
                        <h1 className={styles.title}>AI 助手</h1>
                        <p className={styles.subtitle}>基于大模型的智能舆情分析助手，可协助撰写报告。</p>
                    </div>
                    <Button variant="outline" size="sm" onClick={handleClear} icon={<Trash2 size={16} />}>
                        清空对话
                    </Button>
                </div>

                <div className={styles.chatWindow}>
                    {messages.length === 0 ? (
                        <div className={styles.emptyState}>
                            <div className={styles.avatarLarge}><Bot size={32} /></div>
                            <h3>你好！我是你的舆情分析助手。</h3>
                            <p>你可以问我关于最近舆情趋势的问题，或者让我帮你总结分析报告。</p>
                        </div>
                    ) : (
                        <div className={styles.messageList}>
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`${styles.message} ${styles[msg.role]}`}>
                                    <div className={styles.avatar}>
                                        {msg.role === 'user' ? <UserIcon size={18} /> : <Bot size={18} />}
                                    </div>
                                    <div className={styles.bubble}>
                                        {msg.content}
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className={`${styles.message} ${styles.assistant}`}>
                                    <div className={styles.avatar}><Bot size={18} /></div>
                                    <div className={`${styles.bubble} ${styles.loading}`}>
                                        <span className={styles.dot}></span>
                                        <span className={styles.dot}></span>
                                        <span className={styles.dot}></span>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                <div className={styles.inputArea}>
                    <form onSubmit={handleSend} className={styles.inputWrapper}>
                        <input
                            type="text"
                            className={styles.input}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="输入你的问题..."
                            disabled={isLoading}
                        />
                        <Button
                            type="submit"
                            className={styles.sendBtn}
                            disabled={!input.trim() || isLoading}
                        >
                            <Send size={18} color="white" />
                        </Button>
                    </form>
                </div>
            </div>
        </MainLayout>
    );
};
