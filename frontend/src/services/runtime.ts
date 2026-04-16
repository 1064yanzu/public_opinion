export type RouterStrategy = 'browser' | 'hash';
export type RuntimeMode = 'web' | 'desktop';

export interface DesktopHostRuntime {
  backendUrl: string;
  appDataDir: string;
  configPath: string;
  platform: string;
  isPackaged: boolean;
}

export interface AppRuntime {
  mode: RuntimeMode;
  routerStrategy: RouterStrategy;
  backendOrigin: string;
  apiBaseUrl: string;
  staticBaseUrl: string;
  appDataDir?: string;
  configPath?: string;
  platform: string;
  isPackaged: boolean;
}

declare global {
  interface Window {
    __TAURI__?: unknown;
    __TAURI_INTERNALS__?: unknown;
  }
}

let runtimePromise: Promise<AppRuntime> | null = null;
let runtimeSnapshot: AppRuntime | null = null;

function hasTauriRuntime() {
  return typeof window !== 'undefined' && (
    '__TAURI__' in window || '__TAURI_INTERNALS__' in window
  );
}

function buildWebRuntime(): AppRuntime {
  const backendOrigin = import.meta.env.VITE_BACKEND_ORIGIN ?? '';

  return {
    mode: 'web',
    routerStrategy: 'browser',
    backendOrigin,
    apiBaseUrl: backendOrigin ? `${backendOrigin}/api` : '/api',
    staticBaseUrl: backendOrigin ? `${backendOrigin}/static` : '/static',
    platform: typeof navigator !== 'undefined' ? navigator.platform : 'web',
    isPackaged: false,
  };
}

async function fetchDesktopRuntime(): Promise<AppRuntime> {
  const { invoke } = await import('@tauri-apps/api/core');
  const payload = await invoke<DesktopHostRuntime>('get_desktop_runtime');

  return {
    mode: 'desktop',
    routerStrategy: 'hash',
    backendOrigin: payload.backendUrl,
    apiBaseUrl: `${payload.backendUrl}/api`,
    staticBaseUrl: `${payload.backendUrl}/static`,
    appDataDir: payload.appDataDir,
    configPath: payload.configPath,
    platform: payload.platform,
    isPackaged: payload.isPackaged,
  };
}

export async function loadAppRuntime(): Promise<AppRuntime> {
  if (!runtimePromise) {
    runtimePromise = (async () => {
      if (!hasTauriRuntime()) {
        runtimeSnapshot = buildWebRuntime();
        return runtimeSnapshot;
      }

      try {
        runtimeSnapshot = await fetchDesktopRuntime();
        return runtimeSnapshot;
      } catch (error) {
        console.warn('读取桌面运行时失败，回退到 Web 模式。', error);
        runtimeSnapshot = buildWebRuntime();
        return runtimeSnapshot;
      }
    })();
  }

  return runtimePromise;
}

export function getAppRuntime(): AppRuntime {
  if (!runtimeSnapshot) {
    throw new Error('应用运行时尚未初始化');
  }

  return runtimeSnapshot;
}

export function isDesktopRuntime() {
  return getAppRuntime().mode === 'desktop';
}

export function resolveBackendUrl(path: string) {
  if (!path) {
    return path;
  }

  if (/^https?:\/\//.test(path)) {
    return path;
  }

  const runtime = getAppRuntime();
  if (path.startsWith('/')) {
    return runtime.backendOrigin ? `${runtime.backendOrigin}${path}` : path;
  }

  return runtime.backendOrigin ? `${runtime.backendOrigin}/${path}` : path;
}

export async function pickDirectory() {
  if (!hasTauriRuntime()) {
    return null;
  }

  const { invoke } = await import('@tauri-apps/api/core');
  return invoke<string | null>('pick_directory');
}

export async function restartDesktopBackend() {
  if (!hasTauriRuntime()) {
    return false;
  }

  const { invoke } = await import('@tauri-apps/api/core');
  return invoke<boolean>('restart_backend');
}

export async function openPathInSystem(path: string) {
  if (!hasTauriRuntime()) {
    return false;
  }

  const { invoke } = await import('@tauri-apps/api/core');
  return invoke<boolean>('open_path_in_system', { path });
}
