import { useEffect, useMemo, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, HashRouter } from 'react-router-dom';
import App from '@/App';
import { AuthProvider } from '@/context/AuthContext';
import { configureApiClient } from '@/services/api';
import { loadAppRuntime } from '@/services/runtime';
import type { AppRuntime } from '@/services/runtime';
import { BootstrapScreen } from './BootstrapScreen';

function detectBootstrapMode(): 'desktop' | 'web' {
  if (typeof window === 'undefined') {
    return 'web';
  }

  return '__TAURI__' in window || '__TAURI_INTERNALS__' in window ? 'desktop' : 'web';
}

function BootstrapApp() {
  const [runtime, setRuntime] = useState<AppRuntime | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bootstrapMode = useMemo(() => detectBootstrapMode(), []);

  const boot = async () => {
    setError(null);

    try {
      const nextRuntime = await loadAppRuntime();
      configureApiClient();
      setRuntime(nextRuntime);
    } catch (bootError: any) {
      setError(bootError?.message ?? '运行时初始化失败，请重试。');
    }
  };

  useEffect(() => {
    void boot();
  }, []);

  if (!runtime) {
    return <BootstrapScreen mode={bootstrapMode} error={error} onRetry={() => void boot()} />;
  }

  const Router = runtime.routerStrategy === 'hash' ? HashRouter : BrowserRouter;

  return (
    <Router>
      <AuthProvider>
        <App />
      </AuthProvider>
    </Router>
  );
}

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('找不到应用挂载节点 #root');
}

ReactDOM.createRoot(rootElement).render(<BootstrapApp />);
