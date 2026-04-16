import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import api from '@/services/api';
import styles from './Login.module.css';

export const Register: React.FC = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError('');
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Basic validation
        if (!formData.username || !formData.email || !formData.password) {
            setError('请填写所有必填字段');
            return;
        }

        if (formData.password !== formData.confirmPassword) {
            setError('两次输入的密码不一致');
            return;
        }

        if (formData.password.length < 6) {
            setError('密码长度至少为6位');
            return;
        }

        setLoading(true);

        try {
            await api.post('/auth/register', {
                username: formData.username,
                email: formData.email,
                password: formData.password,
            });

            // Navigate to login with a success message (could be passed via state if Login handled it)
            // For now just redirect
            navigate('/login');
        } catch (err: any) {
            console.error('Registration failed', err);
            if (err.response?.data?.detail) {
                setError(err.response.data.detail);
            } else {
                setError('注册失败，请稍后重试');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <Card className={styles.loginCard}>
                <div className={styles.header}>
                    <div className={styles.logo} />
                    <h1 className={styles.title}>创建账户</h1>
                    <p className={styles.subtitle}>注册以开始使用舆情分析系统</p>
                </div>

                <form onSubmit={handleSubmit} className={styles.form}>
                    {error && <div className={styles.error}>{error}</div>}

                    <div className={styles.field}>
                        <label htmlFor="username" className={styles.label}>用户名</label>
                        <input
                            id="username"
                            name="username"
                            type="text"
                            className={styles.input}
                            value={formData.username}
                            onChange={handleChange}
                            placeholder="请输入用户名"
                            required
                        />
                    </div>

                    <div className={styles.field}>
                        <label htmlFor="email" className={styles.label}>邮箱</label>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            className={styles.input}
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="请输入邮箱地址"
                            required
                        />
                    </div>

                    <div className={styles.field}>
                        <label htmlFor="password" className={styles.label}>密码</label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            className={styles.input}
                            value={formData.password}
                            onChange={handleChange}
                            placeholder="请输入密码（至少6位）"
                            required
                        />
                    </div>

                    <div className={styles.field}>
                        <label htmlFor="confirmPassword" className={styles.label}>确认密码</label>
                        <input
                            id="confirmPassword"
                            name="confirmPassword"
                            type="password"
                            className={styles.input}
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            placeholder="请再次输入密码"
                            required
                        />
                    </div>

                    <Button
                        type="submit"
                        className={styles.submitButton}
                        isLoading={loading}
                    >
                        注册
                    </Button>

                    <div className={styles.registerLink}>
                        <span>已有账户？</span>
                        <Link to="/login">立即登录</Link>
                    </div>
                </form>
            </Card>

            <p className={styles.footer}>© 2025 Public Opinion Analysis System</p>
        </div>
    );
};
