import { useEffect, useState } from 'react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { useAuth } from '@/context/AuthContext';
import api from '@/services/api';
import styles from './SettingsPanels.module.css';

export function ProfileSettingsPanel() {
  const { user, updateUser } = useAuth();
  const [email, setEmail] = useState(user?.email ?? '');
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setEmail(user?.email ?? '');
  }, [user?.email]);

  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);
    setError(null);

    try {
      const response = await api.put('/auth/me', { email });
      updateUser(response.data);
      setMessage('账户信息已更新。');
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? '保存失败，请稍后重试。');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card title="基本信息" subtitle="账户信息仍由后端统一鉴权。">
      <div className={styles.panelBody}>
        <div className={styles.gridTwo}>
          <div className={styles.field}>
            <label className={styles.fieldLabel}>用户名</label>
            <input className={styles.input} value={user?.username ?? ''} disabled />
          </div>
          <div className={styles.field}>
            <label className={styles.fieldLabel}>邮箱</label>
            <input
              className={styles.input}
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
        </div>

        {message ? <div className={`${styles.statusText} ${styles.success}`}>{message}</div> : null}
        {error ? <div className={`${styles.statusText} ${styles.error}`}>{error}</div> : null}

        <div className={styles.footerActions}>
          <Button onClick={handleSave} isLoading={isSaving}>
            保存账户信息
          </Button>
        </div>
      </div>
    </Card>
  );
}
