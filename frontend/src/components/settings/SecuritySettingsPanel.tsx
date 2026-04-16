import { useState } from 'react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import api from '@/services/api';
import styles from './SettingsPanels.module.css';

export function SecuritySettingsPanel() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setMessage(null);
    setError(null);

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('请完整填写密码信息。');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('两次输入的新密码不一致。');
      return;
    }

    setIsSaving(true);
    try {
      const response = await api.put('/auth/password', {
        current_password: currentPassword,
        new_password: newPassword,
      });

      setMessage(response.data.message ?? '密码已更新。');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? '密码更新失败，请稍后重试。');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card title="安全设置" subtitle="桌面版仍沿用当前账号体系。">
      <div className={styles.panelBody}>
        <div className={styles.gridTwo}>
          <div className={styles.field}>
            <label className={styles.fieldLabel}>当前密码</label>
            <input
              className={styles.input}
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
            />
          </div>
          <div className={styles.field}>
            <label className={styles.fieldLabel}>新密码</label>
            <input
              className={styles.input}
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
          </div>
        </div>

        <div className={styles.field}>
          <label className={styles.fieldLabel}>确认新密码</label>
          <input
            className={styles.input}
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
          />
        </div>

        {message ? <div className={`${styles.statusText} ${styles.success}`}>{message}</div> : null}
        {error ? <div className={`${styles.statusText} ${styles.error}`}>{error}</div> : null}

        <div className={styles.footerActions}>
          <Button onClick={handleSave} isLoading={isSaving}>
            更新密码
          </Button>
        </div>
      </div>
    </Card>
  );
}
