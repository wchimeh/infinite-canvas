#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{process::{Child, Command}, sync::Mutex, time::{Duration, Instant}};
use tauri::Manager;

struct Backend(Mutex<Option<Child>>);

fn stop_backend(child: &mut Child) {
    #[cfg(windows)] {
        use std::os::windows::process::CommandExt;
        let _ = Command::new("taskkill").args(["/PID", &child.id().to_string(), "/T", "/F"])
            .creation_flags(0x08000000).output();
    }
    let _ = child.kill();
    let _ = child.wait();
}

fn main() {
    let app = tauri::Builder::default()
        .manage(Backend(Mutex::new(None)))
        .setup(|app| {
            let data = match std::env::var_os("CANVAS_DESKTOP_DATA_DIR") {
                Some(path) => std::path::PathBuf::from(path),
                None => app.path().app_data_dir()?,
            };
            if !data.is_absolute() { return Err("应用数据目录必须是绝对路径".into()); }
            std::fs::create_dir_all(&data)?;
            let handshake = data.join("launch-session.json");
            let _ = std::fs::remove_file(&handshake);
            let mut command;
            if cfg!(debug_assertions) {
                let repo = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..").canonicalize()?;
                command = Command::new(repo.join("services/backend/.venv/Scripts/python.exe"));
                command.arg(repo.join("scripts/backend_entry.py"));
                command.current_dir(repo);
            } else {
                command = Command::new(std::env::current_exe()?.parent().ok_or("缺少程序目录")?.join("canvas-backend.exe"));
            }
            command.arg("--handshake").arg(&handshake).arg("--data-dir").arg(data.join("projects"));
            #[cfg(windows)] {
                use std::os::windows::process::CommandExt;
                command.creation_flags(0x08000000);
            }
            let mut child = command.spawn()?;
            let deadline = Instant::now() + Duration::from_secs(30);
            while !handshake.exists() {
                if child.try_wait()?.is_some() || Instant::now() > deadline {
                    stop_backend(&mut child);
                    return Err("本地服务启动失败；请检查依赖、配置及数据目录权限".into());
                }
                std::thread::sleep(Duration::from_millis(100));
            }
            let result = (|| -> Result<(), Box<dyn std::error::Error>> {
                let session: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(&handshake)?)?;
                let url: tauri::Url = session["url"].as_str().ok_or("本地服务握手失败")?.parse()?;
                let origin = url.origin().ascii_serialization();
                let downloads = if std::env::var_os("CANVAS_DESKTOP_DATA_DIR").is_some() {
                    data.join("downloads")
                } else {
                    app.path().download_dir()?.join("InfiniteCanvas")
                };
                let mut window = tauri::WebviewWindowBuilder::new(app, "main", tauri::WebviewUrl::External(url))
                    .title("无限画布 · 短剧创作工作台").inner_size(1500.0, 960.0).min_inner_size(980.0, 680.0)
                    .on_download(move |window, event| {
                        let notify = |status: &str, path: Option<&std::path::Path>| {
                            let detail = serde_json::json!({"status": status, "path": path.map(|p| p.to_string_lossy().into_owned())});
                            let _ = window.eval(&format!("window.dispatchEvent(new CustomEvent('canvas-download', {{detail:{detail}}}))"));
                        };
                        match event {
                            tauri::webview::DownloadEvent::Requested { url, destination } => {
                                let allowed = url.origin().ascii_serialization() == origin
                                    || (url.scheme() == "blob" && url.as_str().starts_with(&format!("blob:{origin}/")));
                                if !allowed || std::fs::create_dir_all(&downloads).is_err() {
                                    notify("failed", None); return false;
                                }
                                let filename = destination.file_name().unwrap_or(std::ffi::OsStr::new("download")).to_owned();
                                let original = std::path::Path::new(&filename);
                                let stem = original.file_stem().unwrap_or(std::ffi::OsStr::new("download")).to_string_lossy();
                                let extension = original.extension().map(|e| format!(".{}", e.to_string_lossy())).unwrap_or_default();
                                for index in 0..10000 {
                                    let candidate = downloads.join(if index == 0 { filename.clone() } else { format!("{stem} ({index}){extension}").into() });
                                    match std::fs::OpenOptions::new().write(true).create_new(true).open(&candidate) {
                                        Ok(_) => { *destination = candidate; notify("started", None); return true; }
                                        Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => continue,
                                        Err(_) => break,
                                    }
                                }
                                notify("failed", None); false
                            }
                            tauri::webview::DownloadEvent::Finished { path, success, .. } => {
                                notify(if success { "completed" } else { "failed" }, path.as_deref()); true
                            }
                            _ => true,
                        }
                    });
                if std::env::var_os("CANVAS_DESKTOP_DATA_DIR").is_some() {
                    if let Ok(port) = std::env::var("CANVAS_QA_DEBUG_PORT") {
                        let port: u16 = port.parse()?;
                        if port == 0 { return Err("调试端口无效".into()); }
                        window = window.additional_browser_args(&format!("--remote-debugging-address=127.0.0.1 --remote-debugging-port={port}"));
                    }
                }
                window.build()?;
                Ok(())
            })();
            let _ = std::fs::remove_file(&handshake);
            if let Err(error) = result { stop_backend(&mut child); return Err(error); }
            *app.state::<Backend>().0.lock().unwrap() = Some(child);
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("无法启动无限画布");
    app.run(|app, event| {
        if matches!(event, tauri::RunEvent::Exit) {
            if let Some(mut child) = app.state::<Backend>().0.lock().unwrap().take() {
                stop_backend(&mut child);
            }
        }
    });
}
