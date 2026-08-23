use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, RunEvent, State, WindowEvent,
};

// ── GitHub API types ──────────────────────────────────────────────────────────

#[derive(Debug, Deserialize)]
struct GitHubNotification {
    id: String,
    subject: GitHubSubject,
    repository: GitHubRepo,
    unread: bool,
    updated_at: String,
    #[serde(default)]
    last_read_at: Option<String>,
}

#[derive(Debug, Deserialize)]
struct GitHubSubject {
    title: String,
    url: Option<String>,
    #[serde(rename = "type")]
    subject_type: String,
}

#[derive(Debug, Deserialize)]
struct GitHubRepo {
    full_name: String,
    html_url: String,
}

// ── App state ─────────────────────────────────────────────────────────────────

struct AppState {
    unread_count: Mutex<u32>,
    notifications: Mutex<Vec<NotificationItem>>,
    token: Mutex<Option<String>>,
    last_check: Mutex<Option<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct NotificationItem {
    id: String,
    title: String,
    repo: String,
    repo_url: String,
    notification_type: String,
    updated_at: String,
    url: Option<String>,
}

// ── Tauri commands ────────────────────────────────────────────────────────────

#[tauri::command]
fn get_notifications(state: State<AppState>) -> Vec<NotificationItem> {
    state.notifications.lock().unwrap().clone()
}

#[tauri::command]
fn get_unread_count(state: State<AppState>) -> u32 {
    *state.unread_count.lock().unwrap()
}

#[tauri::command]
fn save_token(token: String, state: State<AppState>, app: AppHandle) -> Result<(), String> {
    *state.token.lock().unwrap() = Some(token.clone());
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    std::fs::create_dir_all(&app_dir).map_err(|e| e.to_string())?;
    std::fs::write(app_dir.join("token.txt"), &token).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_token(state: State<AppState>) -> Option<String> {
    state.token.lock().unwrap().clone()
}

#[tauri::command]
fn get_last_check(state: State<AppState>) -> Option<String> {
    state.last_check.lock().unwrap().clone()
}

#[tauri::command]
fn open_url(url: String) -> Result<(), String> {
    std::process::Command::new("open")
        .arg(&url)
        .spawn()
        .map_err(|e| format!("Failed to open URL: {}", e))?;
    Ok(())
}

#[tauri::command]
async fn check_now(app: AppHandle, state: State<'_, AppState>) -> Result<u32, String> {
    let token_opt = state.token.lock().unwrap().clone();
    let token = token_opt.ok_or("No GitHub token configured")?;
    fetch_notifications(&app, &token).await
}

// ── GitHub API ────────────────────────────────────────────────────────────────

async fn fetch_notifications(app: &AppHandle, token: &str) -> Result<u32, String> {
    let client = Client::builder()
        .user_agent("DevNotify/0.1")
        .build()
        .map_err(|e| e.to_string())?;

    let resp = client
        .get("https://api.github.com/notifications")
        .header("Authorization", format!("Bearer {}", token))
        .header("Accept", "application/vnd.github+json")
        .send()
        .await
        .map_err(|e| format!("HTTP error: {}", e))?;

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(format!("GitHub API {}: {}", status, body));
    }

    let items: Vec<GitHubNotification> = resp
        .json()
        .await
        .map_err(|e| format!("JSON parse error: {}", e))?;

    let count = items.len() as u32;
    let notifs: Vec<NotificationItem> = items
        .into_iter()
        .map(|n| NotificationItem {
            id: n.id,
            title: n.subject.title,
            repo: n.repository.full_name,
            repo_url: n.repository.html_url,
            notification_type: n.subject.subject_type,
            updated_at: n.updated_at,
            url: n.subject.url,
        })
        .collect();

    let state = app.state::<AppState>();
    *state.unread_count.lock().unwrap() = count;
    *state.notifications.lock().unwrap() = notifs;
    *state.last_check.lock().unwrap() = Some(get_now_iso());

    // Update tray tooltip
    if let Some(tray) = app.tray_by_id("main") {
        let tooltip = if count > 0 {
            format!("DevNotify — {} unread", count)
        } else {
            "DevNotify — all clear".to_string()
        };
        let _ = tray.set_tooltip(Some(&tooltip));
    }

    Ok(count)
}

fn get_now_iso() -> String {
    use chrono::Utc;
    Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string()
}

// ── App entry ─────────────────────────────────────────────────────────────────

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(AppState {
            unread_count: Mutex::new(0),
            notifications: Mutex::new(vec![]),
            token: Mutex::new(None),
            last_check: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            get_notifications,
            get_unread_count,
            save_token,
            get_token,
            get_last_check,
            check_now,
            open_url,
        ])
        .setup(|app| {
            //── Load saved token ──────────────────────────────────────────────
            let app_dir = app.path().app_data_dir()?;
            let token_path = app_dir.join("token.txt");
            if token_path.exists() {
                if let Ok(token) = std::fs::read_to_string(&token_path) {
                    let token = token.trim().to_string();
                    if !token.is_empty() {
                        let state = app.state::<AppState>();
                        *state.token.lock().unwrap() = Some(token.clone());
                    }
                }
            }

            //── Build tray menu ───────────────────────────────────────────────
            let check_now =
                MenuItemBuilder::with_id("check_now", "Check Now").build(app)?;
            let preferences = MenuItemBuilder::with_id("preferences", "Preferences…")
                .accelerator("Cmd+,")
                .build(app)?;
            let separator = PredefinedMenuItem::separator(app)?;
            let quit =
                MenuItemBuilder::with_id("quit", "Quit DevNotify")
                    .accelerator("Cmd+Q")
                    .build(app)?;

            let menu = MenuBuilder::new(app)
                .item(&check_now)
                .item(&preferences)
                .item(&separator)
                .item(&quit)
                .build()?;

            //── Create tray icon ──────────────────────────────────────────────
            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("DevNotify")
                .menu(&menu)
                .on_menu_event(move |app, event| match event.id().as_ref() {
                    "check_now" => {
                        let app = app.clone();
                        tauri::async_runtime::spawn(async move {
                            let state = app.state::<AppState>();
                            let token_str = state.token.lock().unwrap().clone();
                            if let Some(ref token) = token_str {
                                let _ = fetch_notifications(&app, token).await;
                            }
                            // Refresh window if open
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.eval("window.refreshNotifications?.()");
                            }
                        });
                    }
                    "preferences" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "quit" => {
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            if window.is_visible().unwrap_or(false) {
                                let _ = window.hide();
                            } else {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                    }
                })
                .build(app)?;

            //── Start background polling ──────────────────────────────────────
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                // Initial check after 2 seconds
                tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
                loop {
                    let state = app_handle.state::<AppState>();
                    let token_str = state.token.lock().unwrap().clone();
                    if let Some(ref token) = token_str {
                        let _ = fetch_notifications(&app_handle, token).await;
                    }
                    // Poll every 60 seconds
                    tokio::time::sleep(tokio::time::Duration::from_secs(60)).await;
                }
            });

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error building tauri application");

    //── Handle window close → hide instead of quit ──────────────────────────
    app.run(|app_handle, event| {
        if let RunEvent::WindowEvent {
            label,
            event: WindowEvent::CloseRequested { .. },
            ..
        } = &event
        {
            if label == "main" {
                if let Some(window) = app_handle.get_webview_window("main") {
                    let _ = window.hide();
                }
            }
        }
    });
}