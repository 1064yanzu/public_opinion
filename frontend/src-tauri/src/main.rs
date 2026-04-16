#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::Serialize;
use std::fs::{self, OpenOptions};
use std::net::{TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use tauri::{AppHandle, Manager, State, WindowEvent};

#[derive(Default)]
struct BackendState {
    manager: Mutex<Option<BackendManager>>,
}

struct BackendManager {
    child: Child,
    backend_url: String,
    app_data_dir: PathBuf,
    config_path: PathBuf,
    project_root: PathBuf,
    is_packaged: bool,
    port: u16,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct DesktopRuntime {
    backend_url: String,
    app_data_dir: String,
    config_path: String,
    platform: String,
    is_packaged: bool,
}

const BACKEND_STARTUP_MAX_RETRIES: usize = 480;
const BACKEND_STARTUP_POLL_INTERVAL_MS: u64 = 250;

fn project_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .canonicalize()
        .unwrap_or_else(|_| PathBuf::from(env!("CARGO_MANIFEST_DIR")))
}

fn allocate_port() -> Result<u16, String> {
    let listener = TcpListener::bind("127.0.0.1:0").map_err(|err| err.to_string())?;
    let port = listener.local_addr().map_err(|err| err.to_string())?.port();
    drop(listener);
    Ok(port)
}

fn wait_for_backend(port: u16) -> Result<(), String> {
    for _ in 0..BACKEND_STARTUP_MAX_RETRIES {
        if TcpStream::connect(("127.0.0.1", port)).is_ok() {
            return Ok(());
        }
        thread::sleep(Duration::from_millis(BACKEND_STARTUP_POLL_INTERVAL_MS));
    }

    Err(format!(
        "后端启动超时，超过 {} 秒仍未就绪，请检查应用数据目录 logs/backend.log",
        (BACKEND_STARTUP_MAX_RETRIES as u64 * BACKEND_STARTUP_POLL_INTERVAL_MS) / 1000
    ))
}

fn find_python(project_root: &Path) -> String {
    let candidates = [
        project_root.join(".venv/bin/python"),
        project_root.join(".venv/Scripts/python.exe"),
    ];

    for candidate in candidates {
        if candidate.exists() {
            return candidate.to_string_lossy().to_string();
        }
    }

    if cfg!(target_os = "windows") {
        "python".to_string()
    } else {
        "python3".to_string()
    }
}

fn packaged_backend_path(app_handle: &AppHandle) -> Result<PathBuf, String> {
    let resource_dir = app_handle
        .path()
        .resource_dir()
        .map_err(|err| err.to_string())?;

    let executable = if cfg!(target_os = "windows") {
        "public_opinion_backend.exe"
    } else {
        "public_opinion_backend"
    };

    let candidates = [
        resource_dir.join("backend").join(executable),
        resource_dir
            .join("backend")
            .join("public_opinion_backend")
            .join(executable),
        resource_dir
            .join("resources")
            .join("backend")
            .join(executable),
        resource_dir
            .join("resources")
            .join("backend")
            .join("public_opinion_backend")
            .join(executable),
    ];

    for candidate in candidates {
        if candidate.exists() {
            return Ok(candidate);
        }
    }

    Err(format!(
        "缺少打包后的后端二进制，已检查资源目录: {}",
        resource_dir.display()
    ))
}

fn spawn_backend(
    app_handle: &AppHandle,
    project_root: &Path,
    app_data_dir: &Path,
    port: u16,
    is_packaged: bool,
) -> Result<Child, String> {
    fs::create_dir_all(app_data_dir.join("config")).map_err(|err| err.to_string())?;
    fs::create_dir_all(app_data_dir.join("logs")).map_err(|err| err.to_string())?;

    let working_dir = if is_packaged {
        app_data_dir.to_path_buf()
    } else {
        project_root.to_path_buf()
    };

    let mut command = if is_packaged {
        let backend_binary = packaged_backend_path(app_handle)?;
        Command::new(backend_binary)
    } else {
        let python = find_python(project_root);
        let mut command = Command::new(python);
        command.arg(project_root.join("backend/run_desktop.py"));
        command
    };

    let backend_log_path = app_data_dir.join("logs/backend.log");
    let backend_log = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&backend_log_path)
        .map_err(|err| format!("无法打开后端日志文件 {}: {err}", backend_log_path.display()))?;
    let backend_log_err = backend_log
        .try_clone()
        .map_err(|err| format!("无法复制后端日志句柄 {}: {err}", backend_log_path.display()))?;

    command
        .current_dir(working_dir)
        .env("API_HOST", "127.0.0.1")
        .env("API_PORT", port.to_string())
        .env("DESKTOP_MODE", "true")
        .env("APP_DATA_DIR", app_data_dir)
        .stdin(Stdio::null())
        .stdout(Stdio::from(backend_log))
        .stderr(Stdio::from(backend_log_err));

    command.spawn().map_err(|err| err.to_string())
}

fn stop_backend(manager: &mut BackendManager) {
    let _ = manager.child.kill();
    let _ = manager.child.wait();
}

fn init_backend(app_handle: &AppHandle, state: &BackendState) -> Result<(), String> {
    let project_root = project_root();
    let app_data_dir = app_handle
        .path()
        .app_data_dir()
        .unwrap_or_else(|_| project_root.join(".runtime-desktop"));
    let port = allocate_port()?;
    let backend_url = format!("http://127.0.0.1:{port}");
    let config_path = app_data_dir.join("config/runtime-config.json");
    let is_packaged = !cfg!(debug_assertions);
    let child = spawn_backend(app_handle, &project_root, &app_data_dir, port, is_packaged)?;

    let mut guard = state.manager.lock().map_err(|err| err.to_string())?;
    *guard = Some(BackendManager {
        child,
        backend_url,
        app_data_dir,
        config_path,
        project_root,
        is_packaged,
        port,
    });
    drop(guard);

    wait_for_backend(port)
}

#[tauri::command]
fn get_desktop_runtime(state: State<BackendState>) -> Result<DesktopRuntime, String> {
    let guard = state.manager.lock().map_err(|err| err.to_string())?;
    let manager = guard
        .as_ref()
        .ok_or_else(|| "桌面后端尚未初始化".to_string())?;

    Ok(DesktopRuntime {
        backend_url: manager.backend_url.clone(),
        app_data_dir: manager.app_data_dir.display().to_string(),
        config_path: manager.config_path.display().to_string(),
        platform: std::env::consts::OS.to_string(),
        is_packaged: manager.is_packaged,
    })
}

#[tauri::command]
fn restart_backend(app_handle: AppHandle, state: State<BackendState>) -> Result<bool, String> {
    let mut guard = state.manager.lock().map_err(|err| err.to_string())?;
    let manager = guard
        .as_mut()
        .ok_or_else(|| "桌面后端尚未初始化".to_string())?;

    stop_backend(manager);
    manager.child = spawn_backend(
        &app_handle,
        &manager.project_root,
        &manager.app_data_dir,
        manager.port,
        manager.is_packaged,
    )?;
    drop(guard);

    wait_for_backend(
        state
            .manager
            .lock()
            .map_err(|err| err.to_string())?
            .as_ref()
            .ok_or_else(|| "桌面后端尚未初始化".to_string())?
            .port,
    )?;

    Ok(true)
}

#[tauri::command]
fn pick_directory() -> Option<String> {
    rfd::FileDialog::new()
        .pick_folder()
        .map(|path| path.display().to_string())
}

#[tauri::command]
fn open_path_in_system(path: String) -> Result<bool, String> {
    if path.trim().is_empty() {
        return Ok(false);
    }

    let target = PathBuf::from(path);
    if !target.exists() {
        return Ok(false);
    }

    #[cfg(target_os = "macos")]
    let mut command = {
        let mut command = Command::new("open");
        command.arg(&target);
        command
    };

    #[cfg(target_os = "windows")]
    let mut command = {
        let mut command = Command::new("explorer");
        command.arg(&target);
        command
    };

    #[cfg(all(unix, not(target_os = "macos")))]
    let mut command = {
        let mut command = Command::new("xdg-open");
        command.arg(&target);
        command
    };

    command.spawn().map_err(|err| err.to_string())?;
    Ok(true)
}

fn main() {
    tauri::Builder::default()
        .manage(BackendState::default())
        .setup(|app| {
            let state = app.state::<BackendState>();
            init_backend(&app.handle(), &state).map_err(|err| std::io::Error::other(err))?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_desktop_runtime,
            restart_backend,
            pick_directory,
            open_path_in_system
        ])
        .on_window_event(|window, event| {
            if matches!(event, WindowEvent::Destroyed) {
                if let Ok(mut guard) = window.app_handle().state::<BackendState>().manager.lock() {
                    if let Some(manager) = guard.as_mut() {
                        stop_backend(manager);
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
