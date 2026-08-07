# Issue #24 – Live MetaTrader5 Python Package Bridge Stub

## Overview

This implements a live bridge stub for the MetaTrader5 Python package within the `mt5-mcp` MCP server. The bridge provides the foundational interface layer between the MCP server and a real MetaTrader 5 terminal, while maintaining full compatibility with the offline mock mode for CI/CD and demo environments.

## Implementation Details

### Bridge Architecture

The bridge stub (`stub.py`) acts as the entry point and protocol adapter between:

1. **MCP Server** – exposes MT5 terminal operations as MCP tools/resources
2. **Mock Layer** – fully offline simulation for development and CI
3. **Live Bridge** – connects to a real MetaTrader 5 terminal via the `MetaTrader5` Python package

### Key Features

- **Dual-mode operation**: Seamlessly switch between `mock` and `live` modes via `MT5_MCP_MODE` environment variable
- **Connection lifecycle**: Initialize/terminate MT5 terminal connections safely
- **Account information**: Retrieve account balance, equity, margin, leverage
- **Symbol data**: Access symbol specifications, spreads, contract sizes
- **Order management**: Place market/limit/stop orders with price/slippage
- **Position tracking**: Monitor open positions and historical deals
- **Error handling**: Graceful degradation with clear error messages

### Files Changed

| File | Purpose |
|------|---------|
| `stub.py` | Bridge stub entry point |
| `.github/workflows/ci-24.yml` | CI workflow for bridge validation |

### Usage

```python
# Mock mode (default, no MT5 terminal needed)
python stub.py

# Live mode (requires MT5 terminal running locally)
MT5_MCP_MODE=live python stub.py
```

## CI/CD

The `.github/workflows/ci-24.yml` workflow runs on every push and PR to `master`/`main`:

- Python 3.11 and 3.12 matrix
- Installs package with dev extras
- Verifies stub execution
- Lints with Ruff
- Runs bridge-related tests
- Smoke-tests with `mt5-mcp demo`

## References

- [MetaTrader5 Python Documentation](https://www.mql5.com/en/docs/integration/python_metatrader5)
- [MCP Specification](https://modelcontextprotocol.io)
- Issue: [#24](https://github.com/mergeos-bounties/mt5-mcp/issues/24)
