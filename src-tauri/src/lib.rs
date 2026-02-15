use std::sync::Mutex;
use tauri_plugin_shell::process::CommandChild;

pub struct BackendPort(pub Mutex<Option<u16>>);

pub struct SidecarProcess(pub Mutex<Option<CommandChild>>);
