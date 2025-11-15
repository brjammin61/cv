# Data Directory

This directory stores market data, polling data, and other data files used by The Oracle system.

## Contents

- **market_snapshots/**: Cached order book snapshots
- **polling_data/**: Scraped polling data (self and neighbor preferences)
- **trade_history/**: Historical trade logs (if logging enabled)
- **backtest_results/**: Backtesting output files

## File Formats

### Market Data (CSV)
```csv
timestamp,exchange,market_id,best_bid,best_ask,mid_price,volume
2025-11-15 10:00:00,kalshi,PREZ-28,0.50,0.51,0.505,12500
```

### Polling Data (CSV)
```csv
date,poll_name,pollster,self_pref,neighbor_pref,sample_size
2025-11-14,Harris X,Harris,0.48,0.53,1500
```

## Notes

- This directory is gitignored to protect sensitive data
- Backup important data files regularly
- Large files (>100MB) should be compressed
- Clean old data periodically to save space

## Data Sources

Add your data files here from:
- Manual polling data collection
- API snapshots
- Third-party data providers
- Custom scraping scripts
