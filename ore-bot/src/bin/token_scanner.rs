use anyhow::Result;
use ore_bot::multi_token;

fn main() -> Result<()> {
    println!("\n🔍 Scanning all mineable tokens on Solana...\n");

    // Analyze all tokens
    let tokens = multi_token::analyze_all_tokens()?;

    // Print comparison
    multi_token::print_token_comparison(&tokens);

    // Generate optimal config
    let config = multi_token::generate_optimal_config(&tokens);

    println!("\n📝 OPTIMAL .ENV CONFIGURATION:\n");
    println!("{}", config);

    println!("\n✅ Analysis complete! Use the configuration above for maximum profit.\n");

    Ok(())
}
