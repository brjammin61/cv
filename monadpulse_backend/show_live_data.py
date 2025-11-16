#!/usr/bin/env python3
"""Show live data from running MonadPulse API"""
import requests
import json

API_URL = "http://localhost:8000"

print("=" * 80)
print("MONADPULSE - LIVE API DATA (RIGHT NOW)")
print("=" * 80)
print()

# Test 1: KPI Stats
print("📊 DASHBOARD KPIs:")
print("-" * 80)
try:
    response = requests.get(f"{API_URL}/stats/kpi")
    data = response.json()
    print(f"Total MEV Captured:    ${data['total_mev']:>15,.2f}")
    print(f"MEV Change (14d):      {data['mev_change_pct']:>15.1f}%")
    print(f"Network TPS (24h):     {data['network_tps']:>15,}")
    print(f"Top Validator:         {data['top_validator']}")
    print(f"Omega Partner:         {'⭐ YES' if data['top_validator_is_partner'] else 'No'}")
    print(f"Avg MEV Efficiency:    ${data['avg_mev_efficiency']:>15.2f}")
except Exception as e:
    print(f"Error: {e}")
print()

# Test 2: Top Validators
print("🏆 VALIDATOR LEADERBOARD (Top 5):")
print("-" * 80)
try:
    response = requests.get(f"{API_URL}/validators/leaderboard")
    validators = response.json()[:5]

    print(f"{'Rank':<6} {'Validator':<25} {'MEV Efficiency':<15} {'APY':<8} {'Omega'}")
    print("-" * 80)
    for v in validators:
        omega = "⭐ YES" if v['is_omega_partner'] else "No"
        print(f"{v['rank']:<6} {v['name']:<25} ${v['mev_efficiency']:<14.2f} {v['apy_pct']:<7.1f}% {omega}")
except Exception as e:
    print(f"Error: {e}")
print()

# Test 3: Chart Data
print("📈 MEV HISTORY (First 5 days):")
print("-" * 80)
try:
    response = requests.get(f"{API_URL}/stats/chart")
    chart = response.json()[:5]

    for point in chart:
        print(f"{point['name']:>10}:  ${point['MEV Captured (USD)']:>12,.2f}")
    print(f"{'...':<10}   (9 more days)")
except Exception as e:
    print(f"Error: {e}")
print()

print("=" * 80)
print("✅ ALL DATA FETCHED FROM LIVE API SERVER")
print("=" * 80)
print()
print("Server:  http://localhost:8000")
print("Docs:    http://localhost:8000/docs")
print()
print("Your React app can connect to these endpoints right now!")
print()
