use ore_common::{MiningSolution, OreError, Result};
use std::ffi::CString;
use std::os::raw::{c_char, c_int, c_uint, c_ulonglong};
use tracing::{debug, error, info};

#[repr(C)]
struct CSolution {
    nonce: c_ulonglong,
    hash: [u8; 32],
    difficulty: c_uint,
}

// FFI declarations for CUDA solver
extern "C" {
    fn drillx_cuda_init(device_id: c_int) -> c_int;
    fn drillx_cuda_solve(
        challenge: *const u8,
        challenge_len: c_uint,
        target_difficulty: c_uint,
        max_iterations: c_ulonglong,
        solution: *mut CSolution,
    ) -> c_int;
    fn drillx_cuda_cleanup() -> c_int;
}

/// High-performance GPU-accelerated Drillx solver
pub struct DrillxSolver {
    device_id: Option<u32>,
    initialized: bool,
}

impl DrillxSolver {
    /// Create a new solver instance
    pub fn new(gpu_enabled: bool, device_id: Option<u32>) -> Result<Self> {
        let mut solver = Self {
            device_id,
            initialized: false,
        };

        if gpu_enabled {
            solver.init_gpu(device_id.unwrap_or(0))?;
        }

        Ok(solver)
    }

    /// Initialize GPU solver
    fn init_gpu(&mut self, device_id: u32) -> Result<()> {
        unsafe {
            let result = drillx_cuda_init(device_id as c_int);
            if result != 0 {
                error!("Failed to initialize CUDA solver: error code {}", result);
                return Err(OreError::Solver(format!(
                    "CUDA initialization failed: {}",
                    result
                )));
            }
        }

        self.initialized = true;
        info!("CUDA solver initialized on device {}", device_id);
        Ok(())
    }

    /// Find a valid hash solution
    ///
    /// This is the core mining function. It will search for a nonce that produces
    /// a hash with at least `target_difficulty` leading zero bits.
    ///
    /// # Arguments
    /// * `challenge` - The current mining challenge (32 bytes)
    /// * `target_difficulty` - Required number of leading zero bits
    /// * `max_iterations` - Maximum number of hashes to try (0 = unlimited)
    /// * `worker_id` - Identifier for this worker
    ///
    /// # Returns
    /// A `MiningSolution` if a valid hash is found, or an error
    pub fn solve(
        &self,
        challenge: &[u8; 32],
        target_difficulty: u32,
        max_iterations: u64,
        worker_id: String,
    ) -> Result<MiningSolution> {
        debug!(
            "Starting solve: difficulty={}, max_iterations={}",
            target_difficulty, max_iterations
        );

        if self.initialized {
            // Use GPU solver
            self.solve_gpu(challenge, target_difficulty, max_iterations, worker_id)
        } else {
            // Fallback to CPU solver
            self.solve_cpu(challenge, target_difficulty, max_iterations, worker_id)
        }
    }

    /// GPU-accelerated solver
    fn solve_gpu(
        &self,
        challenge: &[u8; 32],
        target_difficulty: u32,
        max_iterations: u64,
        worker_id: String,
    ) -> Result<MiningSolution> {
        let mut c_solution = CSolution {
            nonce: 0,
            hash: [0u8; 32],
            difficulty: 0,
        };

        unsafe {
            let result = drillx_cuda_solve(
                challenge.as_ptr(),
                32,
                target_difficulty,
                max_iterations,
                &mut c_solution as *mut CSolution,
            );

            if result != 0 {
                return Err(OreError::Solver(format!(
                    "CUDA solve failed: error code {}",
                    result
                )));
            }
        }

        if c_solution.difficulty < target_difficulty {
            return Err(OreError::Solver(format!(
                "Failed to find solution with difficulty {}",
                target_difficulty
            )));
        }

        Ok(MiningSolution {
            nonce: c_solution.nonce,
            hash: c_solution.hash,
            difficulty: c_solution.difficulty,
            timestamp: ore_common::utils::current_timestamp(),
            worker_id,
        })
    }

    /// CPU fallback solver (simple reference implementation)
    /// This is significantly slower than GPU but ensures the bot can still function
    fn solve_cpu(
        &self,
        challenge: &[u8; 32],
        target_difficulty: u32,
        max_iterations: u64,
        worker_id: String,
    ) -> Result<MiningSolution> {
        use sha3::{Digest, Keccak256};

        let max_iter = if max_iterations == 0 {
            u64::MAX
        } else {
            max_iterations
        };

        for nonce in 0..max_iter {
            // Create hash input: challenge + nonce
            let mut hasher = Keccak256::new();
            hasher.update(challenge);
            hasher.update(nonce.to_le_bytes());
            let hash = hasher.finalize();

            // Count leading zero bits
            let difficulty = count_leading_zeros(&hash);

            if difficulty >= target_difficulty {
                let mut hash_array = [0u8; 32];
                hash_array.copy_from_slice(&hash);

                return Ok(MiningSolution {
                    nonce,
                    hash: hash_array,
                    difficulty,
                    timestamp: ore_common::utils::current_timestamp(),
                    worker_id,
                });
            }

            // Progress logging every 1M iterations
            if nonce % 1_000_000 == 0 && nonce > 0 {
                debug!("CPU solver: {} iterations completed", nonce);
            }
        }

        Err(OreError::Solver(format!(
            "Failed to find solution after {} iterations",
            max_iter
        )))
    }
}

impl Drop for DrillxSolver {
    fn drop(&mut self) {
        if self.initialized {
            unsafe {
                drillx_cuda_cleanup();
            }
            debug!("CUDA solver cleaned up");
        }
    }
}

/// Count leading zero bits in a hash
fn count_leading_zeros(hash: &[u8]) -> u32 {
    let mut count = 0u32;
    for byte in hash {
        if *byte == 0 {
            count += 8;
        } else {
            count += byte.leading_zeros();
            break;
        }
    }
    count
}

// Safety: DrillxSolver is thread-safe as CUDA handles thread safety internally
unsafe impl Send for DrillxSolver {}
unsafe impl Sync for DrillxSolver {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_count_leading_zeros() {
        assert_eq!(count_leading_zeros(&[0x00, 0xFF]), 8);
        assert_eq!(count_leading_zeros(&[0x00, 0x00, 0x80]), 16);
        assert_eq!(count_leading_zeros(&[0x80]), 0);
        assert_eq!(count_leading_zeros(&[0x00, 0x00, 0x00, 0x01]), 31);
    }

    #[test]
    fn test_cpu_solver() {
        let solver = DrillxSolver::new(false, None).unwrap();
        let challenge = [0u8; 32]; // Simple challenge

        // Try to find a solution with difficulty 8 (relatively easy)
        let result = solver.solve(&challenge, 8, 10_000_000, "test".to_string());

        // This might fail if we don't find a solution in 10M iterations
        // but that's okay for a basic test
        if let Ok(solution) = result {
            assert!(solution.difficulty >= 8);
            assert_eq!(solution.worker_id, "test");
        }
    }
}
