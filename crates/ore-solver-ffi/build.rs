use std::env;
use std::path::PathBuf;

fn main() {
    // Check if CUDA is available
    let cuda_available = check_cuda_available();

    if cuda_available {
        println!("cargo:warning=CUDA detected - building GPU solver");
        build_cuda_solver();
    } else {
        println!("cargo:warning=CUDA not detected - CPU-only mode");
        build_stub_solver();
    }
}

fn check_cuda_available() -> bool {
    // Check for CUDA toolkit
    if let Ok(cuda_path) = env::var("CUDA_PATH") {
        return std::path::Path::new(&cuda_path).exists();
    }

    // Common CUDA installation paths
    let common_paths = vec![
        "/usr/local/cuda",
        "/opt/cuda",
        "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA",
    ];

    for path in common_paths {
        if std::path::Path::new(path).exists() {
            return true;
        }
    }

    false
}

fn build_cuda_solver() {
    let cuda_path = env::var("CUDA_PATH")
        .unwrap_or_else(|_| "/usr/local/cuda".to_string());

    println!("cargo:rustc-link-search=native={}/lib64", cuda_path);
    println!("cargo:rustc-link-lib=cudart");

    // Build CUDA code using nvcc
    let cuda_file = "cuda/drillx_solver.cu";
    let out_dir = env::var("OUT_DIR").unwrap();
    let obj_file = format!("{}/drillx_solver.o", out_dir);

    let nvcc_status = std::process::Command::new("nvcc")
        .args(&[
            "-O3",
            "-gencode", "arch=compute_75,code=sm_75", // RTX 20xx series
            "-gencode", "arch=compute_80,code=sm_80", // A100
            "-gencode", "arch=compute_86,code=sm_86", // RTX 30xx series
            "-gencode", "arch=compute_89,code=sm_89", // RTX 40xx series
            "--compiler-options", "-fPIC",
            "-c",
            cuda_file,
            "-o", &obj_file,
        ])
        .status();

    match nvcc_status {
        Ok(status) if status.success() => {
            println!("cargo:rustc-link-search=native={}", out_dir);

            // Link the compiled CUDA object file
            cc::Build::new()
                .object(&obj_file)
                .compile("drillx_cuda");
        }
        _ => {
            println!("cargo:warning=nvcc compilation failed, falling back to stub");
            build_stub_solver();
        }
    }
}

fn build_stub_solver() {
    // Create a stub implementation for environments without CUDA
    let out_dir = env::var("OUT_DIR").unwrap();
    let stub_file = PathBuf::from(&out_dir).join("drillx_stub.c");

    std::fs::write(&stub_file, r#"
#include <stdint.h>
#include <stdio.h>

typedef struct {
    uint64_t nonce;
    uint8_t hash[32];
    uint32_t difficulty;
} Solution;

int drillx_cuda_init(int device_id) {
    fprintf(stderr, "CUDA not available - using CPU fallback\n");
    return -1; // Signal that CUDA is not available
}

int drillx_cuda_solve(
    const uint8_t* challenge,
    uint32_t challenge_len,
    uint32_t target_difficulty,
    uint64_t max_iterations,
    Solution* solution
) {
    return -1; // Not implemented - will use CPU fallback
}

int drillx_cuda_cleanup() {
    return 0;
}
"#).expect("Failed to write stub file");

    cc::Build::new()
        .file(&stub_file)
        .compile("drillx_stub");
}
