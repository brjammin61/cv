use chrono::Utc;

/// Get current timestamp in seconds
pub fn current_timestamp() -> i64 {
    Utc::now().timestamp()
}

/// Get current timestamp in milliseconds
pub fn current_timestamp_ms() -> i64 {
    Utc::now().timestamp_millis()
}

/// Calculate time remaining in current round
pub fn time_remaining_in_round(round_start: i64) -> u64 {
    use crate::constants::ROUND_DURATION_SECS;
    let now = current_timestamp();
    let elapsed = (now - round_start) as u64;
    if elapsed >= ROUND_DURATION_SECS {
        0
    } else {
        ROUND_DURATION_SECS - elapsed
    }
}

/// Check if we're in the sniper window
pub fn is_sniper_window(round_start: i64) -> bool {
    use crate::constants::SNIPER_WINDOW_SECS;
    time_remaining_in_round(round_start) <= SNIPER_WINDOW_SECS
}

/// Convert lamports to SOL
pub fn lamports_to_sol(lamports: u64) -> f64 {
    lamports as f64 / 1_000_000_000.0
}

/// Convert SOL to lamports
pub fn sol_to_lamports(sol: f64) -> u64 {
    (sol * 1_000_000_000.0) as u64
}

/// Calculate grid index from (x, y) coordinates
pub fn coords_to_index(x: usize, y: usize) -> u8 {
    use crate::constants::GRID_WIDTH;
    (y * GRID_WIDTH + x) as u8
}

/// Calculate (x, y) coordinates from grid index
pub fn index_to_coords(index: u8) -> (usize, usize) {
    use crate::constants::GRID_WIDTH;
    let index = index as usize;
    (index % GRID_WIDTH, index / GRID_WIDTH)
}

/// Format difficulty as leading zeros
pub fn format_difficulty(difficulty: u32) -> String {
    format!("{} leading zeros", difficulty)
}

/// Validate grid index
pub fn is_valid_grid_index(index: u8) -> bool {
    use crate::constants::GRID_SIZE;
    (index as usize) < GRID_SIZE
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_coords_conversion() {
        assert_eq!(coords_to_index(0, 0), 0);
        assert_eq!(coords_to_index(4, 4), 24);
        assert_eq!(coords_to_index(2, 1), 7);

        assert_eq!(index_to_coords(0), (0, 0));
        assert_eq!(index_to_coords(24), (4, 4));
        assert_eq!(index_to_coords(7), (2, 1));
    }

    #[test]
    fn test_lamports_conversion() {
        assert_eq!(lamports_to_sol(1_000_000_000), 1.0);
        assert_eq!(sol_to_lamports(1.0), 1_000_000_000);
    }

    #[test]
    fn test_grid_index_validation() {
        assert!(is_valid_grid_index(0));
        assert!(is_valid_grid_index(24));
        assert!(!is_valid_grid_index(25));
    }
}
