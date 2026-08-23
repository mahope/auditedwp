mod providers;

use crate::providers::{fetch_notifications, NotificationItem, Provider};
use std::sync::Mutex;
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, RunEvent, State, WindowEvent,
};

// ── Trial / license ──────────────────────────────────────────────
//
// ÆRLIG MODEL (så sitets løfter holder):
//  - Første app-start gemmer en "first_run"-tidsstempel lokalt → 7 dages trial.
//  - Efter 7 dage låser appen notifikations-fetching, indtil en licensnøgle er
//    indløst. Licensvalidering mod Lemon Squeezy aktiveres, når API-nøglen er
//    på plads (LICENSE_API_URL + LICENSE_API_KEY via compile-time env eller
//    offline-grace). Indtil da er unlock-kommandoen klar i UI og backend.

const TRIAL_DAYS: u64 = 7;

struct AppState {
    unread_count: Mutex<u32>,
    notifications: Mutex<Vec<NotificationItem>>,
    provider: Mutex<Provider>,
    token: Mutex<Option<String>>,
    last_check: Mutex<Option<String>>,
    license_key: Mutex<Option<String>>,
}

fn trial_file_path(app: &AppHandle) -> Result<std::path::PathBuf, String> {
    let dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    Ok(dir.join("trial.json"))
}

/// Sikrer at trial-filen findes; returnerer first-run ISO-tidsstempel.
fn ensure_trial_started(app: &AppHandle) -> Result<String, String> {
    let path = trial_file_path(app)?;
    if let Ok(existing) = std::fs::read_to_string(&path) {
        if let Ok(v) = serde_json::from_str::<serde_json::Value>(&existing) {
            if let Some(ts) = v["first_run"].as_str() {
                return Ok(ts.to_string());
            }
        }
    }
    let ts = get_now_iso();
    let doc = serde_json::json!({ "first_run": ts });
    std::fs::write(&path, doc.to_string()).map_err(|e| e.to_string())?;
    Ok(ts)
}

#[derive(serde::Serialize)]
struct TrialStatus {
    trial_started: String,
    trial_days_total: u64,
    trial_days_left: i64,
    expired: bool,
    licensed: bool,
}

fn read_license_key(app: &AppHandle) -> Option<String> {
    let path = trial_file_path(app).ok()?;
    let txt = std::fs::read_to_string(&path).ok()?;
    let v: serde_json::Value = serde_json::from_str(&txt).ok()?;
    v["license_key"].as_str().map(|s| s.to_string())
}

#[tauri::command]
fn get_trial_status(state: State<AppState>, app: AppHandle) -> Result<TrialStatus, String> {
    let started = ensure_trial_started(&app)?;
    let licensed = state.license_key.lock().unwrap().is_some();
    let first_run =
        chrono::NaiveDateTime::parse_from_str(&started, "%Y-%m-%dT%H:%M:%SZ")
            .map_err(|e| e.to_string())?;
    let elapsed = chrono::Utc::now().naive_utc() - first_run;
    let days_left = TRIAL_DAYS as i64 - elapsed.num_days();
    Ok(TrialStatus {
        trial_started: started,
        trial_days_total: TRIAL_DAYS,
        trial_days_left: days_left.max(0),
        expired: days_left <= 0,
        licensed,
    })
}

/// Aktiverer en licensnøgle. Remote-validering mod Lemon Squeezy tilføjes, når
/// API-nøglen er tilgængelig; indtil da gemmes nøglen og markere som aktiveret.
#[tauri::command]
fn activate_license(key: String, state: State<AppState>, app: AppHandle) -> Result<(), String> {
    let key = key.trim().to_string();
    if key.len() < 8 {
        return Err("That doesn't look like a valid license key.".into());
    }
    // TODO(LS): POST til LS license-validation endpoint når API-nøgle findes.
    let path = trial_file_path(&app)?;
    let mut doc: serde_json::Value = std::fs::read_to_string(&path)
        .ok()
        .and_then(|t| serde_json::from_str(&t).ok())
        .unwrap_or_else(|| serde_json::json!({}));
    doc["license_key"] = serde_json::Value::String(key.clone());
    std::fs::write(&path, doc.to_string()).map_err(|e| e.to_string())?;
    *state.license_key.lock().unwrap() = Some(key);
    Ok(())
}

#[tauri::command]
async fn check_now(app: AppHandle, state: State<'_, AppState>) -> Result<u32, String> {
    // Trial-gate: efter 7 dage uden licens nægtes fetch med en ærlig fejl.
    let started = ensure_trial_started(&app)?;
    let licensed = read_license_key(&app).is_some() || state.license_key.lock().unwrap().is_some();
    if !licensed {
        if let Ok(first_run) =
            chrono::NaiveDateTime::parse_from_str(&started, "%Y-%m-%dT%H:%M:%SZ")
        {
            let elapsed = chrono::Utc::now().naive_utc() - first_run;
            if elapsed.num_days() >= TRIAL_DAYS as i64 {
                return Err(
                    "Your free 7-day trial has ended. Buy a $19 lifetime license at \
                     https://auditedwp.pages.dev/devnotify/ to keep using DevNotify."
                        .into(),
                );
            }
        }
    }
    let token_opt = state.token.lock().unwrap().clone();
    let token = token_opt.ok_or("No access token configured")?;
    fetch_and_store(&app, &token).await
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
fn get_provider(state: State<AppState>) -> String {
    state.provider.lock().unwrap().as_str().to_string()
}

#[tauri::command]
fn save_provider(provider: String, state: State<AppState>, app: AppHandle) -> Result<(), String> {
    let p = Provider::from_str(&provider)
        .ok_or_else(|| format!("Unknown provider: {}", provider))?;
    let dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    std::fs::write(dir.join("provider.txt"), p.as_str()).map_err(|e| e.to_string())?;
    *state.provider.lock().unwrap() = p;
    Ok(())
}

#[tauri::command]
fn get_token(state: State<AppState>) -> Option<String> {
    state.token.lock().unwrap().clone()
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

// ── Fetch + store (kernen; provider-agnostisk) ───────────────────

async fn fetch_and_store(app: &AppHandle, token: &str) -> Result<u32, String> {
    let provider = {
        let state = app.state::<AppState>();
        let p = state.provider.lock().unwrap().clone();
        drop(state);
        p
    };
    let notifs = fetch_notifications(&provider, token).await?;
    let count = notifs.len() as u32;

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
            provider: Mutex::new(Provider::GitHub),
            token: Mutex::new(None),
            last_check: Mutex::new(None),
            license_key: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            get_notifications,
            get_unread_count,
            save_token,
            get_token,
            get_provider,
            save_provider,
            get_last_check,
            check_now,
            open_url,
            get_trial_status,
            activate_license,
        ])
        .setup(|app| {
            //── Load saved token + provider ─────────────────────────────────
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
            let provider_path = app_dir.join("provider.txt");
            if provider_path.exists() {
                if let Ok(p) = std::fs::read_to_string(&provider_path) {
                    if let Some(pv) = Provider::from_str(p.trim()) {
                        let state = app.state::<AppState>();
                        *state.provider.lock().unwrap() = pv;
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
            let _tray = TrayIconBuilder::with_id("main")
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
                                let _ = fetch_and_store(&app, token).await;
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
                        let _ = fetch_and_store(&app_handle, token).await;
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
