import { useEffect, useState } from 'react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { useAppRuntime } from '@/hooks/useAppRuntime';
import {
  openPathInSystem,
  pickDirectory,
  restartDesktopBackend,
} from '@/services/runtime';
import {
  fetchRuntimeStatus,
  fetchSystemConfig,
  saveSystemConfig,
  testWeiboConnection,
} from '@/services/system';
import type {
  DesktopRuntimeStatus,
  SystemConfigPayload,
  SystemConfigResponse,
} from '@/types';
import styles from './SettingsPanels.module.css';

const EMPTY_CONFIG: SystemConfigPayload = {
  app_name: '',
  ai_model_type: 'zhipuai',
  ai_api_key: '',
  ai_base_url: '',
  ai_model_id: '',
  weibo_cookie: '',
  douyin_cookie: '',
  crawler_max_page: 10,
  crawler_timeout: 30,
  crawler_delay: 1,
  data_dir: '',
  static_dir: '',
  wordcloud_dir: '',
  reports_dir: '',
  upload_dir: '',
  database_path: '',
  log_dir: '',
};

function normalizeConfig(source?: SystemConfigPayload): SystemConfigPayload {
  return {
    ...EMPTY_CONFIG,
    ...source,
  };
}

function resolveBackendLogPath(logDir?: string | null) {
  if (!logDir) {
    return '';
  }

  if (logDir.includes('\\')) {
    return `${logDir}\\backend.log`;
  }

  return `${logDir}/backend.log`;
}

export function SystemSettingsPanel() {
  const runtime = useAppRuntime();
  const [form, setForm] = useState<SystemConfigPayload>(EMPTY_CONFIG);
  const [runtimeStatus, setRuntimeStatus] = useState<DesktopRuntimeStatus | null>(null);
  const [configMeta, setConfigMeta] = useState<SystemConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingWeibo, setTestingWeibo] = useState(false);
  const [importingWeiboCookie, setImportingWeiboCookie] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [weiboStatus, setWeiboStatus] = useState<{ type: 'success' | 'warning' | 'error'; text: string } | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [config, status] = await Promise.all([
          fetchSystemConfig(),
          fetchRuntimeStatus(),
        ]);
        setForm(normalizeConfig(config.config));
        setConfigMeta(config);
        setRuntimeStatus(status);
      } catch (err: any) {
        setError(err?.response?.data?.detail ?? '系统配置读取失败。');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const updateField = <K extends keyof SystemConfigPayload>(key: K, value: SystemConfigPayload[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handlePickDirectory = async (key: keyof SystemConfigPayload) => {
    const selected = await pickDirectory();
    if (selected) {
      updateField(key, selected);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    setError(null);

    try {
      const response = await saveSystemConfig(form);
      setConfigMeta(response);
      setForm(normalizeConfig(response.config));
      setMessage(
        response.restart_required
          ? '配置已保存，部分路径变更需要重启内置后端后才会完全生效。'
          : '系统配置已保存并立即生效。'
      );
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? '系统配置保存失败。');
    } finally {
      setSaving(false);
    }
  };

  const handleImportWeiboCookie = async () => {
    setImportingWeiboCookie(true);
    setError(null);
    setMessage(null);

    try {
      const cookie = await navigator.clipboard.readText();
      if (!cookie.trim()) {
        setError('剪贴板里没有可用的微博 Cookie。');
        return;
      }

      updateField('weibo_cookie', cookie.trim());
      setMessage('已从剪贴板导入微博 Cookie。');
    } catch {
      setError('读取剪贴板失败，请检查系统剪贴板权限。');
    } finally {
      setImportingWeiboCookie(false);
    }
  };

  const handleTestWeibo = async () => {
    setTestingWeibo(true);
    setError(null);
    setMessage(null);
    try {
      const result = await testWeiboConnection();
      setWeiboStatus({
        type: result.success ? 'success' : result.mode === 'visitor' ? 'warning' : 'error',
        text: `${result.mode === 'cookie' ? '登录 Cookie 模式' : '自动访客模式'}：${result.message}${result.sample_count ? `（样本 ${result.sample_count} 条）` : ''}`,
      });
    } catch (err: any) {
      setWeiboStatus({
        type: 'error',
        text: err?.response?.data?.detail ?? '微博连接测试失败。',
      });
    } finally {
      setTestingWeibo(false);
    }
  };

  const handleSaveAndTestWeibo = async () => {
    setSaving(true);
    setTestingWeibo(true);
    setError(null);
    setMessage(null);
    setWeiboStatus(null);

    try {
      const response = await saveSystemConfig(form);
      setConfigMeta(response);
      setForm(normalizeConfig(response.config));

      if (response.restart_required && runtime.mode === 'desktop') {
        const restarted = await restartDesktopBackend();
        if (!restarted) {
          throw new Error('配置已保存，但自动重启内置后端失败。');
        }
        setMessage('配置已保存并自动重启内置后端，正在测试微博连接...');
      } else {
        setMessage('配置已保存，正在测试微博连接...');
      }

      const result = await testWeiboConnection();
      setWeiboStatus({
        type: result.success ? 'success' : result.mode === 'visitor' ? 'warning' : 'error',
        text: `${result.mode === 'cookie' ? '登录 Cookie 模式' : '自动访客模式'}：${result.message}${result.sample_count ? `（样本 ${result.sample_count} 条）` : ''}`,
      });
    } catch (err: any) {
      setWeiboStatus({
        type: 'error',
        text: err?.message ?? err?.response?.data?.detail ?? '保存并测试微博连接失败。',
      });
    } finally {
      setSaving(false);
      setTestingWeibo(false);
    }
  };

  const handleRestart = async () => {
    setMessage(null);
    setError(null);

    const restarted = await restartDesktopBackend();
    if (!restarted) {
      setError('当前不是桌面运行模式，无法从页面重启后端。');
      return;
    }

    setMessage('后端已重启，正在刷新界面。');
    window.location.reload();
  };

  if (loading) {
    return (
      <Card title="系统配置">
        <div className={styles.statusText}>正在读取桌面运行时配置...</div>
      </Card>
    );
  }

  return (
    <div className={styles.stack}>
      <Card title="桌面运行状态" subtitle="这里展示当前内置后端和本地存储路径。">
        <div className={styles.panelBody}>
          <div className={styles.metaGrid}>
            <div className={styles.metaCard}>
              <p className={styles.metaTitle}>运行模式</p>
              <p className={styles.metaValue}>{runtime.mode === 'desktop' ? 'Tauri 桌面版' : 'Web 调试模式'}</p>
            </div>
            <div className={styles.metaCard}>
              <p className={styles.metaTitle}>后端地址</p>
              <p className={styles.metaValue}>{runtime.backendOrigin || '通过前端代理访问'}</p>
            </div>
            <div className={styles.metaCard}>
              <p className={styles.metaTitle}>应用数据目录</p>
              <p className={styles.metaValue}>{runtimeStatus?.app_data_dir ?? runtime.appDataDir ?? '未启用'}</p>
            </div>
            <div className={styles.metaCard}>
              <p className={styles.metaTitle}>配置文件</p>
              <p className={styles.metaValue}>{runtimeStatus?.config_path ?? configMeta?.config_path ?? '未生成'}</p>
            </div>
            <div className={styles.metaCard}>
              <p className={styles.metaTitle}>日志目录</p>
              <p className={styles.metaValue}>{runtimeStatus?.log_dir ?? form.log_dir ?? '未设置'}</p>
            </div>
          </div>

          <div className={styles.inlineActions}>
            <Button variant="outline" onClick={() => openPathInSystem(runtimeStatus?.app_data_dir ?? '')}>
              打开数据目录
            </Button>
            <Button variant="outline" onClick={() => openPathInSystem(runtimeStatus?.config_path ?? '')}>
              打开配置文件
            </Button>
            <Button variant="outline" onClick={() => openPathInSystem(runtimeStatus?.log_dir ?? '')}>
              打开日志目录
            </Button>
            <Button variant="outline" onClick={() => openPathInSystem(resolveBackendLogPath(runtimeStatus?.log_dir))}>
              打开 backend.log
            </Button>
            <Button variant="secondary" onClick={handleRestart} disabled={runtime.mode !== 'desktop'}>
              重启内置后端
            </Button>
          </div>
        </div>
      </Card>

      <Card title="AI 与采集配置" subtitle="桌面版不再要求用户手动改 `.env`。">
        <div className={styles.panelBody}>
          <div className={styles.tipCard}>
            <p className={styles.tipTitle}>微博采集策略</p>
            <p className={styles.tipText}>
              系统会默认先尝试自动访客模式；如果微博官方搜索接口仍要求登录态，再回退使用你粘贴的完整 Cookie header。
            </p>
            <div className={styles.inlineActions}>
              <Button variant="outline" onClick={handleImportWeiboCookie} isLoading={importingWeiboCookie}>
                从剪贴板导入 Cookie
              </Button>
              <Button variant="secondary" onClick={handleSaveAndTestWeibo} isLoading={saving || testingWeibo}>
                保存并测试
              </Button>
              <Button variant="outline" onClick={handleTestWeibo} isLoading={testingWeibo}>
                测试微博连接
              </Button>
            </div>
            {weiboStatus ? (
              <div className={`${styles.statusText} ${styles[weiboStatus.type]}`}>{weiboStatus.text}</div>
            ) : null}
          </div>

          <div className={styles.gridTwo}>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>应用名称</label>
              <input
                className={styles.input}
                value={form.app_name ?? ''}
                onChange={(event) => updateField('app_name', event.target.value)}
              />
            </div>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>AI 服务类型</label>
              <select
                className={styles.select}
                value={form.ai_model_type ?? 'zhipuai'}
                onChange={(event) => updateField('ai_model_type', event.target.value)}
              >
                <option value="zhipuai">智谱</option>
                <option value="openai">OpenAI 兼容接口</option>
              </select>
            </div>
          </div>

          <div className={styles.gridTwo}>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>AI API Key</label>
              <input
                className={styles.input}
                type="password"
                value={form.ai_api_key ?? ''}
                onChange={(event) => updateField('ai_api_key', event.target.value)}
              />
            </div>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>模型 ID</label>
              <input
                className={styles.input}
                value={form.ai_model_id ?? ''}
                onChange={(event) => updateField('ai_model_id', event.target.value)}
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.fieldLabel}>AI Base URL</label>
            <input
              className={styles.input}
              value={form.ai_base_url ?? ''}
              onChange={(event) => updateField('ai_base_url', event.target.value)}
              placeholder="例如 https://api.openai.com/v1"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.fieldLabel}>微博 Cookie</label>
            <textarea
              className={styles.textarea}
              value={form.weibo_cookie ?? ''}
              onChange={(event) => updateField('weibo_cookie', event.target.value)}
              placeholder="可直接粘贴浏览器请求头中的完整 cookie 字符串；如果留空，系统会先尝试自动访客模式。"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.fieldLabel}>抖音 Cookie</label>
            <textarea
              className={styles.textarea}
              value={form.douyin_cookie ?? ''}
              onChange={(event) => updateField('douyin_cookie', event.target.value)}
              placeholder="需要采集抖音数据时再填写。"
            />
          </div>

          <div className={styles.gridTwo}>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>默认最大页数</label>
              <input
                className={styles.input}
                type="number"
                value={form.crawler_max_page ?? 10}
                onChange={(event) => updateField('crawler_max_page', Number(event.target.value))}
              />
            </div>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>超时时间（秒）</label>
              <input
                className={styles.input}
                type="number"
                value={form.crawler_timeout ?? 30}
                onChange={(event) => updateField('crawler_timeout', Number(event.target.value))}
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.fieldLabel}>请求间隔（秒）</label>
            <input
              className={styles.input}
              type="number"
              step="0.1"
              value={form.crawler_delay ?? 1}
              onChange={(event) => updateField('crawler_delay', Number(event.target.value))}
            />
          </div>
        </div>
      </Card>

      <Card title="本地存储目录" subtitle="桌面端默认会把数据、报告和词云输出到本地应用目录。">
        <div className={styles.panelBody}>
          <div className={styles.inputRow}>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>数据目录</label>
              <input
                className={styles.input}
                value={form.data_dir ?? ''}
                onChange={(event) => updateField('data_dir', event.target.value)}
              />
            </div>
            <Button variant="outline" onClick={() => handlePickDirectory('data_dir')}>
              选择目录
            </Button>
            <Button variant="ghost" onClick={() => openPathInSystem(form.data_dir ?? '')}>
              打开
            </Button>
          </div>

          <div className={styles.inputRow}>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>报告目录</label>
              <input
                className={styles.input}
                value={form.reports_dir ?? ''}
                onChange={(event) => updateField('reports_dir', event.target.value)}
              />
            </div>
            <Button variant="outline" onClick={() => handlePickDirectory('reports_dir')}>
              选择目录
            </Button>
            <Button variant="ghost" onClick={() => openPathInSystem(form.reports_dir ?? '')}>
              打开
            </Button>
          </div>

          <div className={styles.inputRow}>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>词云静态目录</label>
              <input
                className={styles.input}
                value={form.wordcloud_dir ?? ''}
                onChange={(event) => updateField('wordcloud_dir', event.target.value)}
              />
            </div>
            <Button variant="outline" onClick={() => handlePickDirectory('wordcloud_dir')}>
              选择目录
            </Button>
            <Button variant="ghost" onClick={() => openPathInSystem(form.wordcloud_dir ?? '')}>
              打开
            </Button>
          </div>

          <div className={styles.gridTwo}>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>数据库文件</label>
              <input
                className={styles.input}
                value={form.database_path ?? ''}
                onChange={(event) => updateField('database_path', event.target.value)}
              />
            </div>
            <div className={styles.field}>
              <label className={styles.fieldLabel}>日志目录</label>
              <input
                className={styles.input}
                value={form.log_dir ?? ''}
                onChange={(event) => updateField('log_dir', event.target.value)}
              />
            </div>
          </div>

          <div className={styles.divider} />

          {message ? (
            <div className={`${styles.statusText} ${configMeta?.restart_required ? styles.warning : styles.success}`}>
              {message}
            </div>
          ) : null}
          {error ? <div className={`${styles.statusText} ${styles.error}`}>{error}</div> : null}

          <div className={styles.footerActions}>
            <Button onClick={handleSave} isLoading={saving}>
              保存系统配置
            </Button>
            <Button variant="outline" onClick={() => openPathInSystem(runtimeStatus?.reports_dir ?? '')}>
              打开当前报告目录
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
