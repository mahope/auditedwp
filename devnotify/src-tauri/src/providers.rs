// ── Provider abstraction ─────────────────────────────────────────
//
// Kernen: en normaliseret notifications-liste fra enhver REST-API der kan
// levere "ulæste ting for mig". GitHub og GitLab er adapters. En ny provider
// tilføjes her uden ændringer i UI eller tray-logik.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Provider {
    GitHub,
    GitLab,
}

impl Provider {
    pub fn as_str(&self) -> &'static str {
        match self {
            Provider::GitHub => "github",
            Provider::GitLab => "gitlab",
        }
    }

    pub fn from_str(s: &str) -> Option<Provider> {
        match s {
            "github" => Some(Provider::GitHub),
            "gitlab" => Some(Provider::GitLab),
            _ => None,
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            Provider::GitHub => "GitHub",
            Provider::GitLab => "GitLab",
        }
    }

    /// URL hvor brugeren opretter en personal access token.
    pub fn token_url(&self) -> &'static str {
        match self {
            Provider::GitHub => "https://github.com/settings/tokens",
            Provider::GitLab => "https://gitlab.com/-/user_settings/personal_access_tokens",
        }
    }

    pub fn token_hint(&self) -> &'static str {
        match self {
            Provider::GitHub => {
                "Create a token at github.com/settings/tokens with 'notifications' and 'repo' scopes."
            }
            Provider::GitLab => {
                "Create a token at GitLab → User Settings → Access Tokens with the read_api scope."
            }
        }
    }
}

/// Normaliseret notifikation — kernen i produktet. Alle adapters mapper til denne.
#[derive(Debug, Clone, serde::Serialize)]
pub struct NotificationItem {
    pub id: String,
    pub title: String,
    pub repo: String,
    pub repo_url: String,
    pub notification_type: String,
    pub updated_at: String,
    pub url: Option<String>,
}

// ── GitHub adapter ───────────────────────────────────────────────

#[derive(serde::Deserialize)]
struct GhNotification {
    id: String,
    subject: GhSubject,
    repository: GhRepo,
    #[allow(dead_code)]
    unread: bool,
    updated_at: String,
}

#[derive(serde::Deserialize)]
struct GhSubject {
    title: String,
    url: Option<String>,
    #[serde(rename = "type")]
    subject_type: String,
}

#[derive(serde::Deserialize)]
struct GhRepo {
    full_name: String,
    html_url: String,
}

pub async fn fetch_github(token: &str) -> Result<Vec<NotificationItem>, String> {
    let client = reqwest::Client::builder()
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

    let items: Vec<GhNotification> = resp
        .json()
        .await
        .map_err(|e| format!("JSON parse error: {}", e))?;

    Ok(items
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
        .collect())
}

// ── GitLab adapter (todos) ───────────────────────────────────────

#[derive(serde::Deserialize)]
struct GlTodo {
    id: u64,
    target_type: Option<String>,
    target_url: Option<String>,
    project: Option<GlProject>,
    body: Option<String>,
    created_at: String,
}

#[derive(serde::Deserialize)]
struct GlProject {
    path_with_namespace: String,
    web_url: String,
}

pub async fn fetch_gitlab(token: &str) -> Result<Vec<NotificationItem>, String> {
    let client = reqwest::Client::builder()
        .user_agent("DevNotify/0.1")
        .build()
        .map_err(|e| e.to_string())?;

    let resp = client
        // 20 er API-max for todos; det er fint — det er "ting du skal se på".
        .get("https://gitlab.com/api/v4/todos?state=pending&per_page=20")
        .header("PRIVATE-TOKEN", token)
        .send()
        .await
        .map_err(|e| format!("HTTP error: {}", e))?;

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(format!("GitLab API {}: {}", status, body));
    }

    let items: Vec<GlTodo> = resp
        .json()
        .await
        .map_err(|e| format!("JSON parse error: {}", e))?;

    Ok(items
        .into_iter()
        .map(|t| {
            let (repo, repo_url) = match t.project {
                Some(p) => (p.path_with_namespace, p.web_url),
                None => (String::new(), String::new()),
            };
            NotificationItem {
                id: t.id.to_string(),
                title: t.body.unwrap_or_else(|| "Todo".to_string()),
                repo,
                repo_url,
                notification_type: t.target_type.unwrap_or_else(|| "todo".to_string()),
                updated_at: t.created_at,
                url: t.target_url,
            }
        })
        .collect())
}

// ── Dispatch ─────────────────────────────────────────────────────

pub async fn fetch_notifications(provider: &Provider, token: &str) -> Result<Vec<NotificationItem>, String> {
    match provider {
        Provider::GitHub => fetch_github(token).await,
        Provider::GitLab => fetch_gitlab(token).await,
    }
}
