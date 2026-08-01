# Live MetaTrader5 Bridge

The `mt5-mcp` package includes an optional **live bridge** that connects to a real MetaTrader 5 terminal via the official [MetaTrader5 Python package](https://pypi.org/project/MetaTrader5/).

By default, all operations run against the **mock backend** (no terminal required). The live bridge activates via the `MT5_LIVE=1` environment variable.

## Quick Start

```bash
# 1. Install MetaTrader5 Python package
pip install MetaTrader5

# 2. Set environment variable
export MT5_LIVE=1

# 3. Run MCP server (auto-selects live backend)
mt5-mcp serve
```

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  MCP Client │────▶│  FastMCP Server  │────▶│  MT5LiveBackend  │
│  (Claude,   │     │  (server.py)     │     │  (live_bridge.py)│
│   Cursor)   │◀────│                  │◀────│                  │
└─────────────┘     └──────────────────┘     └────────┬─────────┘
                                                      │
                                             ┌────────▼─────────┐
                                             │  MetaTrader5      │
                                             │  Python Package   │
                                             │  (MetaTrader5)    │
                                             └────────┬─────────┘
                                                      │
                                             ┌────────▼─────────┐
                                             │  MT5 Terminal     │
                                             │  (Desktop app)    │
                                             └──────────────────┘
```

## Backend Selection Logic

```
get_live_backend():
  1. Check MT5_LIVE env var → if not "1", return None → use MockBackend
  2. Try import MetaTrader5 → if fails, raise ImportError
  3. Return MT5LiveBackend instance
```

## Supported Operations

| Method | Description | Requires Init |
|--------|-------------|:---:|
| `initialize(path?, portable?)` | Connect to MT5 terminal | No |
| `shutdown()` | Disconnect from terminal | No |
| `health()` | Quick connectivity check | Yes |
| `get_terminal_info()` | Terminal metadata (build, path, etc.) | Yes |
| `get_account_info()` | Account balance, equity, margin | Yes |
| `get_symbols(group?)` | List available symbols | Yes |
| `get_symbol_info(symbol)` | Detailed symbol specification | Yes |
| `get_rates(symbol, timeframe?, count?)` | OHLCV candles | Yes |
| `get_tick(symbol)` | Last bid/ask tick | Yes |
| `get_positions(symbol?)` | Open positions | Yes |
| `get_orders(symbol?)` | Pending orders | Yes |
| `get_position_by_ticket(ticket)` | Single position by ticket | Yes |
| `order_send(...)` | Send trade order ⚠️ LIVE | Yes |
| `position_close(ticket, volume?)` | Close position ⚠️ LIVE | Yes |
| `get_history_deals(from?, to?, limit?)` | Deal history | Yes |
| `get_history_orders(from?, to?, limit?)` | Order history | Yes |
| `get_account_summary()` | Combined terminal + account + positions | Yes |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MT5_LIVE` | Enable live bridge (`"1"` to enable) | `"0"` |
| `MT5_MCP_MODE` | Backend mode (`mock` or `live`) | `mock` |
| `MT5_MCP_BRIDGE_URL` | External bridge URL (alternative) | None |
| `MT5_MCP_BRIDGE_FILE` | Bridge file path (alternative) | None |
| `MT5_MCP_MAGIC` | Magic number for trade identification | None |
| `MT5_MCP_MAX_VOLUME` | Maximum order volume | 100.0 |
| `MT5_MCP_SYMBOL_ALLOWLIST` | Comma-separated allowed symbols | None (all) |

## Safety Features

1. **Opt-in only**: `MT5_LIVE=1` must be explicitly set.
2. **Idempotent operations**: Every call checks `is_initialized()` before executing.
3. **Graceful degradation**: When uninitialized, all methods return safe error dicts or empty lists.
4. **Mock-first development**: All CI runs default to mock mode.
5. **Explicit warnings**: Trading operations (`order_send`, `position_close`) include docstring warnings.

## Testing

```bash
# Run live bridge tests (mock mode — no terminal needed)
pytest tests/test_live_bridge.py -v

# With coverage
pytest tests/test_live_bridge.py --cov=src.mt5_mcp.live_bridge --cov-report=term
```

Tests use mock MT5 modules to simulate terminal responses. No live terminal is needed for CI or development.

## Error Handling Patterns

All methods that require initialization return safe values when disconnected:

```python
# Positions/Orders → empty list (safe for iteration)
backend.get_positions()       # → []
backend.get_orders()          # → []

# Info getters → {"ok": False, "error": "Not initialized"}
backend.get_account_info()    # → {"ok": False, "error": "..."}
backend.get_symbol_info("X")  # → {"ok": False, "error": "..."}

# Health → explicit status
backend.health()              # → {"ok": False, "status": "disconnected", ...}
```

## Common Issues

### "MetaTrader5 package not found"
Install the MetaTrader5 Python package:
```bash
pip install MetaTrader5
```

### "Not initialized"
Call `backend.initialize()` before using other methods. Ensure the MT5 desktop terminal is running.

### "terminal_info returned None"
The MT5 terminal process may not be running or the Python package cannot find it.

### Rate limit errors
MT5 terminals have built-in rate limits. Space requests by at least 50-100ms.

## Migration from Mock to Live

1. Start with `MT5_LIVE=0` (default): develop and test with mock data
2. Set `MT5_LIVE=1` on a demo account: validate connectivity and operations
3. Review all trade operations before going live on a real account
4. Never run unattended live trading
