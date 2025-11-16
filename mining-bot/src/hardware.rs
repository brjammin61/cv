// src/hardware.rs
use drillx;
use std::time::Instant;
use std::sync::{Arc, atomic::{AtomicU64, Ordering}};
use std::thread;

/// Runs a local benchmark to determine hashes per minute (HPM).
/// This performs actual drillx mining to measure real hardware performance.
pub fn run_benchmark(duration_secs: u64, core_count: usize) -> u64 {
    println!("Running local benchmark for {} seconds on {} cores...", duration_secs, core_count);

    let hash_counter = Arc::new(AtomicU64::new(0));
    let start_time = Instant::now();
    let mut handles = vec![];

    // Spawn worker threads
    for thread_id in 0..core_count {
        let counter = Arc::clone(&hash_counter);
        let handle = thread::spawn(move || {
            // Create a challenge for mining (using dummy values for benchmark)
            let challenge = [thread_id as u8; 32];
            let mut nonce = thread_id as u64;

            loop {
                // Check if benchmark duration has elapsed
                if start_time.elapsed().as_secs() >= duration_secs {
                    break;
                }

                // Perform the actual drillx hash operation
                let _hash = drillx::hash(&challenge, &nonce.to_le_bytes());

                // Increment hash counter
                counter.fetch_add(1, Ordering::Relaxed);
                nonce += 1;
            }
        });
        handles.push(handle);
    }

    // Wait for all threads to complete
    for handle in handles {
        handle.join().unwrap();
    }

    let total_hashes = hash_counter.load(Ordering::Relaxed);
    let elapsed_secs = start_time.elapsed().as_secs();

    if elapsed_secs == 0 {
        println!("Benchmark failed: no time elapsed");
        return 0;
    }

    let hps = total_hashes / elapsed_secs;
    let hpm = hps * 60;

    println!("Benchmark complete:");
    println!("  Total hashes: {}", total_hashes);
    println!("  Elapsed time: {}s", elapsed_secs);
    println!("  Hashes/sec: {}", hps);
    println!("  Hashes/min (HPM): {}", hpm);

    hpm
}

/// Quick benchmark for testing (runs for shorter duration)
pub fn run_quick_benchmark(duration_secs: u64) -> u64 {
    let core_count = num_cpus::get();
    println!("Auto-detected {} CPU cores", core_count);
    run_benchmark(duration_secs, core_count)
}
