#!/usr/bin/env python3
"""
Installation Test Script for The Oracle

Run this script to verify that all components are installed correctly.

Usage:
    python test_installation.py
"""

import sys
import importlib


def test_python_version():
    """Test Python version compatibility."""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} (compatible)")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (need 3.9+)")
        return False


def test_module_import(module_name, display_name=None):
    """Test if a module can be imported."""
    display_name = display_name or module_name
    try:
        importlib.import_module(module_name)
        print(f"  ✅ {display_name}")
        return True
    except ImportError as e:
        print(f"  ❌ {display_name} - {str(e)}")
        return False


def test_oracle_modules():
    """Test Oracle analytical modules."""
    print("\nTesting Oracle analytical modules...")

    modules = [
        ("modules.mod_01_bias_corrector", "BiasCorrector"),
        ("modules.mod_02_flb_adjuster", "FavoriteLongshotAdjuster"),
        ("modules.mod_03_rfr_adjuster", "RiskFreeRateAdjuster"),
        ("modules.mod_04_dutchbook_detector", "DutchBookDetector"),
        ("modules.mod_05_spatial_arb_detector", "SpatialArbitrageDetector"),
    ]

    results = [test_module_import(mod, name) for mod, name in modules]
    return all(results)


def test_connectors():
    """Test data connectors."""
    print("\nTesting data connectors...")

    connectors = [
        ("connectors.kalshi_connector", "KalshiConnector"),
        ("connectors.polymarket_connector", "PolymarketConnector"),
        ("connectors.data_models", "DataModels"),
    ]

    results = [test_module_import(conn, name) for conn, name in connectors]
    return all(results)


def test_config():
    """Test configuration modules."""
    print("\nTesting configuration modules...")

    configs = [
        ("config.parameters", "Parameters"),
        ("config.markets", "Markets"),
    ]

    results = [test_module_import(conf, name) for conf, name in configs]
    return all(results)


def test_dependencies():
    """Test external dependencies."""
    print("\nTesting external dependencies...")

    deps = [
        ("streamlit", "Streamlit"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        # ("kalshi_python", "Kalshi Python"),  # May not be installed
        # ("py_clob_client", "Polymarket CLOB Client"),  # May not be installed
    ]

    results = [test_module_import(dep, name) for dep, name in deps]
    return all(results)


def test_module_functionality():
    """Test basic functionality of core modules."""
    print("\nTesting module functionality...")

    try:
        from modules import BiasCorrector
        corrector = BiasCorrector(shy_voter_weight=0.75)
        result = corrector.calculate_fair_value(0.48, 0.52)
        assert 0.0 <= result <= 1.0
        print("  ✅ BiasCorrector calculation works")
    except Exception as e:
        print(f"  ❌ BiasCorrector calculation failed: {e}")
        return False

    try:
        from modules import FavoriteLongshotAdjuster
        adjuster = FavoriteLongshotAdjuster()
        conviction, rationale = adjuster.analyze_conviction(0.90, 0.85)
        assert conviction in ["NONE", "LOW", "MEDIUM", "HIGH"]
        print("  ✅ FLB Adjuster analysis works")
    except Exception as e:
        print(f"  ❌ FLB Adjuster analysis failed: {e}")
        return False

    try:
        from modules import DutchBookDetector
        detector = DutchBookDetector()
        signal, _ = detector.find_arbitrage({"A": 0.4, "B": 0.3, "C": 0.25})
        assert signal in ["BUY_ALL", "SELL_ALL", "HOLD"]
        print("  ✅ DutchBook Detector works")
    except Exception as e:
        print(f"  ❌ DutchBook Detector failed: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("=" * 80)
    print("THE ORACLE - Installation Test")
    print("=" * 80)

    tests = [
        ("Python Version", test_python_version),
        ("Oracle Modules", test_oracle_modules),
        ("Data Connectors", test_connectors),
        ("Configuration", test_config),
        ("External Dependencies", test_dependencies),
        ("Module Functionality", test_module_functionality),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 80)
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🎉 The Oracle is ready to launch!")
        print("\nNext steps:")
        print("  1. Configure API keys in config/api_keys.py")
        print("  2. Add your markets in config/markets.py")
        print("  3. Run: streamlit run oracle_dashboard.py")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        print("\n⚠️  Fix the errors above before running the dashboard.")
        print("\nCommon fixes:")
        print("  - Install missing dependencies: pip install -r requirements.txt")
        print("  - Check Python version (need 3.9+)")
        print("  - Verify all files are present")
        return 1


if __name__ == "__main__":
    sys.exit(main())
