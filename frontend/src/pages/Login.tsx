import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import styles from './Login.module.css';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import api from '@/services/api';

export const Login: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const response = await api.post('/auth/login', {
                username,
                password,
            });

            const { access_token, user } = response.data;

            // Update Auth Context logic to accept separate user object if needed, 
            // or fetch user profile after login. 
            // For now, let's assume login saves the token and we fetch user immediately or passing a mock user object.
            // The backend login return: { "access_token": "...", "token_type": "bearer", "user": { ... } }
            // My AuthContext login expects (token, user).

            login(access_token, user || { id: 1, username, email: '', is_active: true, is_superuser: false, created_at: '' });
            navigate('/');
        } catch (err: any) {
            console.error('Login failed', err);
            setError(err.response?.data?.detail || '登录失败，请检查用户名和密码');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <Card className={styles.loginCard}>
                <div className={styles.header}>
                    <div className={styles.logo} />
                    <h1 className={styles.title}>舆情洞察系统</h1>
                    <p className={styles.subtitle}>请登录以继续访问</p>
                </div>

                <form onSubmit={handleSubmit} className={styles.form}>
                    {error && <div className={styles.error}>{error}</div>}

                    <div className={styles.field}>
                        <label htmlFor="username" className={styles.label}>用户名</label>
                        <input
                            id="username"
                            type="text"
                            className={styles.input}
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="请输入用户名"
                            required
                        />
                    </div>

                    <div className={styles.field}>
                        <label htmlFor="password" className={styles.label}>密码</label>
                        <input
                            id="password"
                            type="password"
                            className={styles.input}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="请输入密码"
                            required
                        />
                    </div>

                    <Button
                        type="submit"
                        className={styles.submitButton}
                        isLoading={isLoading}
                    >
                        登录
                    </Button>

                    <div className={styles.registerLink}>
                        <span>还没有账户？</span>
                        <Link to="/register">立即注册</Link>
                    </div>
                </form>
            </Card>

            <p className={styles.footer}>© 2025 Public Opinion Analysis System</p>
        </div>
    );
};
