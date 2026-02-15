use tauri::{command, State};
use std::sync::Mutex;
use tauri_plugin_shell::process::CommandChild;

pub struct BackendPort(pub Mutex<Option<u16>>);

pub struct SidecarProcess(pub Mutex<Option<CommandChild>>);

#[command]
pub fn get_backend_port(state: State<BackendPort>) -> Result<u16, String> {
    state.0.lock()
        .map_err(|e| format!("Failed to lock backend port: {}", e))?
        .ok_or_else(|| "Backend port not yet set".to_string())
}
