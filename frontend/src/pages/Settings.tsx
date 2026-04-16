import { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProfileSettingsPanel } from '@/components/settings/ProfileSettingsPanel';
import { SecuritySettingsPanel } from '@/components/settings/SecuritySettingsPanel';
import { SystemSettingsPanel } from '@/components/settings/SystemSettingsPanel';
import styles from './Settings.module.css';

const TABS = [
  { key: 'profile', label: '个人资料' },
  { key: 'security', label: '安全设置' },
  { key: 'system', label: '桌面运行' },
] as const;

type SettingsTab = (typeof TABS)[number]['key'];

export const Settings = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('system');

  return (
    <MainLayout>
      <div className={styles.header}>
        <h1 className={styles.title}>设置</h1>
        <p className={styles.subtitle}>
          桌面版的运行目录、AI Key、采集配置与账户信息都在这里闭环管理。
        </p>
      </div>

      <div className={styles.container}>
        <aside className={styles.sidebar}>
          {TABS.map((tab) => (
            <button
              key={tab.key}
              className={`${styles.tabBtn} ${activeTab === tab.key ? styles.active : ''}`}
              onClick={() => setActiveTab(tab.key)}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </aside>

        <section className={styles.content}>
          {activeTab === 'profile' ? <ProfileSettingsPanel /> : null}
          {activeTab === 'security' ? <SecuritySettingsPanel /> : null}
          {activeTab === 'system' ? <SystemSettingsPanel /> : null}
        </section>
      </div>
    </MainLayout>
  );
};
