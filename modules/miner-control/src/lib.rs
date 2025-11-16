use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use tracing::{info, warn, error};

/// Miner state
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum MinerState {
    Stopped,
    Starting,
    Running,
    Stopping,
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MinerStatus {
    pub state: MinerState,
    pub uptime_seconds: u64,
    pub last_error: Option<String>,
    pub process_id: Option<u32>,
}

/// Miner control interface
///
/// This module provides an interface to start and stop an external
/// ORE mining process. It can work with:
/// - The official ORE CLI miner
/// - Custom Rust-based miners
/// - Any command-line mining client
pub struct MinerControl {
    /// Path to the miner executable
    miner_path: String,

    /// Command-line arguments for the miner
    miner_args: Vec<String>,

    /// Current miner process
    process: Arc<Mutex<Option<Child>>>,

    /// Miner state
    state: Arc<Mutex<MinerState>>,

    /// Start time (for uptime calculation)
    start_time: Arc<Mutex<Option<std::time::Instant>>>,

    /// Last error message
    last_error: Arc<Mutex<Option<String>>>,
}

impl MinerControl {
    /// Create a new MinerControl instance
    ///
    /// # Arguments
    /// * `miner_path` - Path to the miner executable (e.g., "./ore-cli" or "ore")
    /// * `miner_args` - Command-line arguments for the miner
    ///
    /// # Example
    /// ```no_run
    /// use miner_control::MinerControl;
    ///
    /// let miner = MinerControl::new(
    ///     "ore".to_string(),
    ///     vec!["mine".to_string(), "--keypair".to_string(), "wallet.json".to_string()]
    /// );
    /// ```
    pub fn new(miner_path: String, miner_args: Vec<String>) -> Self {
        Self {
            miner_path,
            miner_args,
            process: Arc::new(Mutex::new(None)),
            state: Arc::new(Mutex::new(MinerState::Stopped)),
            start_time: Arc::new(Mutex::new(None)),
            last_error: Arc::new(Mutex::new(None)),
        }
    }

    /// Start the miner
    ///
    /// Spawns the miner process as a child process
    pub fn start(&self) -> Result<()> {
        let mut state = self.state.lock().unwrap();

        if *state == MinerState::Running {
            warn!("Miner is already running");
            return Ok(());
        }

        *state = MinerState::Starting;
        drop(state);

        info!("Starting miner: {} {:?}", self.miner_path, self.miner_args);

        let child = Command::new(&self.miner_path)
            .args(&self.miner_args)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .context("Failed to spawn miner process")?;

        let pid = child.id();
        info!("Miner process started with PID: {}", pid);

        // Store process handle
        *self.process.lock().unwrap() = Some(child);

        // Update state
        *self.state.lock().unwrap() = MinerState::Running;
        *self.start_time.lock().unwrap() = Some(std::time::Instant::now());
        *self.last_error.lock().unwrap() = None;

        Ok(())
    }

    /// Stop the miner
    ///
    /// Gracefully stops the miner process
    pub fn stop(&self) -> Result<()> {
        let mut state = self.state.lock().unwrap();

        if *state == MinerState::Stopped {
            warn!("Miner is already stopped");
            return Ok(());
        }

        *state = MinerState::Stopping;
        drop(state);

        info!("Stopping miner...");

        let mut process = self.process.lock().unwrap();

        if let Some(child) = process.as_mut() {
            // Try graceful shutdown first
            #[cfg(unix)]
            {
                // Send SIGTERM
                unsafe {
                    libc::kill(child.id() as i32, libc::SIGTERM);
                }

                // Wait for up to 5 seconds
                let timeout = std::time::Duration::from_secs(5);
                let start = std::time::Instant::now();

                while start.elapsed() < timeout {
                    match child.try_wait() {
                        Ok(Some(_status)) => {
                            info!("Miner stopped gracefully");
                            break;
                        }
                        Ok(None) => {
                            std::thread::sleep(std::time::Duration::from_millis(100));
                        }
                        Err(e) => {
                            error!("Error waiting for miner: {}", e);
                            break;
                        }
                    }
                }
            }

            // Force kill if still running
            match child.kill() {
                Ok(_) => {
                    info!("Miner process killed");
                }
                Err(e) => {
                    warn!("Failed to kill miner process: {}", e);
                }
            }

            // Wait for process to exit
            match child.wait() {
                Ok(status) => {
                    info!("Miner exited with status: {}", status);
                }
                Err(e) => {
                    error!("Error waiting for miner to exit: {}", e);
                }
            }
        }

        *process = None;
        drop(process);

        // Update state
        *self.state.lock().unwrap() = MinerState::Stopped;
        *self.start_time.lock().unwrap() = None;

        Ok(())
    }

    /// Get the current status of the miner
    pub fn status(&self) -> MinerStatus {
        let state = self.state.lock().unwrap().clone();
        let start_time = *self.start_time.lock().unwrap();
        let last_error = self.last_error.lock().unwrap().clone();

        let uptime_seconds = match start_time {
            Some(start) => start.elapsed().as_secs(),
            None => 0,
        };

        let process_id = self.process.lock().unwrap()
            .as_ref()
            .map(|child| child.id());

        MinerStatus {
            state,
            uptime_seconds,
            last_error,
            process_id,
        }
    }

    /// Check if the miner is running
    pub fn is_running(&self) -> bool {
        let state = self.state.lock().unwrap();
        *state == MinerState::Running
    }

    /// Restart the miner
    pub fn restart(&self) -> Result<()> {
        info!("Restarting miner...");
        self.stop()?;
        std::thread::sleep(std::time::Duration::from_secs(2));
        self.start()?;
        Ok(())
    }

    /// Set error state
    fn set_error(&self, error: String) {
        *self.state.lock().unwrap() = MinerState::Error;
        *self.last_error.lock().unwrap() = Some(error);
    }
}

impl Drop for MinerControl {
    fn drop(&mut self) {
        // Ensure miner is stopped when control is dropped
        if self.is_running() {
            let _ = self.stop();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_miner_control_creation() {
        let miner = MinerControl::new(
            "ore".to_string(),
            vec!["mine".to_string()],
        );

        assert!(!miner.is_running());
        let status = miner.status();
        assert_eq!(status.state, MinerState::Stopped);
    }

    #[test]
    fn test_miner_status() {
        let miner = MinerControl::new(
            "ore".to_string(),
            vec!["mine".to_string()],
        );

        let status = miner.status();
        assert_eq!(status.uptime_seconds, 0);
        assert_eq!(status.process_id, None);
    }
}
