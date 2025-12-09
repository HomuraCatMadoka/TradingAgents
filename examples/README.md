# Examples

This directory contains example scripts demonstrating how to use the DeFi Agents framework.

## Available Examples

### `example_usage.py`
Basic example showing how to:
- Initialize the DeFi Agents graph with custom configuration
- Configure data vendors
- Run analysis on a protocol/asset
- Use the reflection and memory system

## Running Examples

```bash
# Make sure you have configured your .env file with necessary API keys
python3 examples/example_usage.py
```

## Configuration

Before running examples, ensure:
1. Copy `.env.example` to `.env` and fill in your API keys
2. Review `defiagents/default_config.py` for available configuration options
3. Install dependencies: `pip install -e .`

## Creating New Examples

When creating new examples:
- Add clear comments explaining each step
- Include error handling
- Document required API keys/configuration
- Follow the naming convention: `example_*.py`
