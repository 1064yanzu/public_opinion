import { RefreshCcw, Server, Sparkles, FolderSearch } from 'lucide-react';
import { Button } from '@/components/common/Button';
import styles from './BootstrapScreen.module.css';

interface BootstrapScreenProps {
  mode: 'desktop' | 'web';
  error?: string | null;
  onRetry?: () => void;
}

const DESKTOP_STEPS = [
  {
    title: '正在唤起本地后端',
    text: '桌面版会拉起内置 FastAPI 服务，并准备数据库、配置文件与本地目录。',
    icon: Server,
  },
  {
    title: '正在装载分析能力',
    text: '调度器与 NLP 资源会在后台并行就绪，不阻塞主界面。',
    icon: Sparkles,
  },
  {
    title: '正在校验运行环境',
    text: '如果启动异常，可稍后在设置页直接打开日志目录查看 backend.log。',
    icon: FolderSearch,
  },
];

const WEB_STEPS = [
  {
    title: '正在建立应用会话',
    text: '浏览器模式会优先读取运行时配置，并准备前端路由与接口客户端。',
    icon: Server,
  },
  {
    title: '正在载入工作台',
    text: '页面资源与认证状态准备完成后，会自动进入主界面。',
    icon: Sparkles,
  },
];

export function BootstrapScreen({ mode, error, onRetry }: BootstrapScreenProps) {
  const steps = mode === 'desktop' ? DESKTOP_STEPS : WEB_STEPS;

  return (
    <div className={styles.shell}>
      <div className={styles.panel}>
        <div className={styles.eyebrow}>
          <span className={styles.dot} />
          {mode === 'desktop' ? 'Desktop Bootstrap' : 'Web Bootstrap'}
        </div>

        <h1 className={styles.title}>
          {mode === 'desktop' ? '正在准备桌面工作台' : '正在载入舆情工作台'}
        </h1>

        <p className={styles.description}>
          {mode === 'desktop'
            ? '通常只需几秒。后端准备完成后会自动进入应用，如果首次启动稍慢，多半是杀软在检查二进制——这是一次性的。'
            : '正在同步运行时配置与认证上下文，请稍候。'}
        </p>

        <div className={styles.timeline}>
          {steps.map(({ title, text, icon: Icon }) => (
            <div className={styles.step} key={title}>
              <div className={styles.stepIcon}>
                <Icon size={15} />
              </div>
              <div>
                <div className={styles.stepTitle}>{title}</div>
                <div className={styles.stepText}>{text}</div>
              </div>
            </div>
          ))}
        </div>

        {error ? (
          <div className={styles.errorBox}>
            <div className={styles.errorTitle}>启动遇到问题</div>
            <div className={styles.errorMessage}>{error}</div>
          </div>
        ) : null}

        <div className={styles.footer}>
          <div className={styles.hint}>
            {mode === 'desktop'
              ? '如果等待过久，通常先看设置页里的日志目录最有效。'
              : '运行时就绪后会自动切换到应用界面。'}
          </div>

          {error && onRetry ? (
            <Button variant="secondary" icon={<RefreshCcw size={15} />} onClick={onRetry}>
              重新尝试
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
