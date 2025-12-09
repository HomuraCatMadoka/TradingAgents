# Tests

This directory contains all test files for the DeFi Agents project.

## Test Files

- `test_defi_datasources_only.py` - Tests for DeFi data sources (DeFi Llama, The Graph, CoinGecko, On-chain)
- `test_defi_integration.py` - Comprehensive integration tests including tools
- `test_legacy.py` - Legacy test file from original TradingAgents project

## Running Tests

### Run all data source tests:
```bash
python3 tests/test_defi_datasources_only.py
```

### Run full integration tests:
```bash
python3 tests/test_defi_integration.py
```

### Run with pytest (recommended):
```bash
pytest tests/
```

## Test Requirements

Some tests require:
- API keys configured in environment variables or `.env` file
- RPC endpoints configured in `defiagents/default_config.py`
- DeFi data source dependencies installed (`pip install -e .`)

Note: Some test failures are expected if API keys are not configured.
