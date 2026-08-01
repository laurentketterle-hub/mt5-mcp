"""FastMCP server: MetaTrader 5 tools for AI agents."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from mt5_mcp.backend import get_backend, switch_mode
from mt5_mcp.config import get_mode
from mt5_mcp.live_bridge import MT5LiveBridge

_live_bridge = MT5LiveBridge()

mcp = FastMCP(
    "mt5-mcp",
    instructions=(
        "MetaTrader 5 MCP server. Prefer mock mode offline. "
        "Typical flow: mt5_doctor → mt5_account → mt5_quote → "
        "mt5_order_send → mt5_positions → mt5_position_close."
    ),
)


def _j(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def mt5_mode(mode: str | None = None) -> str:
    """Get or set MT5 backend mode (mock|live)."""
    if mode:
        return _j(switch_mode(mode))
    b = get_backend()
    return _j({"mode": get_mode(), "backend": b.name, "doctor": b.doctor()})


@mcp.tool()
def mt5_doctor() -> str:
    """Check mock/live connectivity and account health."""
    return _j(get_backend().doctor())


@mcp.tool()
def mt5_seed_demo() -> str:
    """Reset the mock MT5 demo account (mock only)."""
    return _j(get_backend().seed_demo())


@mcp.tool()
def mt5_account() -> str:
    """Account balance, equity, margin, trade mode."""
    return _j(get_backend().account())


@mcp.tool()
def mt5_symbols() -> str:
    """List tradeable symbols."""
    return _j(get_backend().symbols())


@mcp.tool()
def mt5_quote(symbol: str) -> str:
    """Bid/ask/last quote for a symbol."""
    return _j(get_backend().quote(symbol))


@mcp.tool()
def mt5_positions() -> str:
    """List open positions."""
    return _j(get_backend().positions())


@mcp.tool()
def mt5_orders() -> str:
    """List pending orders."""
    return _j(get_backend().orders())


@mcp.tool()
def mt5_order_send(
    symbol: str,
    side: str,
    volume: float,
    order_type: str = "market",
    price: float | None = None,
    sl: float | None = None,
    tp: float | None = None,
    comment: str = "",
) -> str:
    """Open market position or place pending order."""
    return _j(
        get_backend().order_send(symbol, side, volume, order_type, price, sl, tp, comment)
    )


@mcp.tool()
def mt5_position_close(ticket: int, volume: float | None = None) -> str:
    """Close position by ticket (optional partial volume)."""
    return _j(get_backend().position_close(ticket, volume))


@mcp.tool()
def mt5_order_cancel(ticket: int) -> str:
    """Cancel a pending order ticket."""
    return _j(get_backend().order_cancel(ticket))


@mcp.tool()
def mt5_history_deals(limit: int = 20) -> str:
    """Recent deal history."""
    return _j(get_backend().history_deals(limit=limit))


@mcp.tool()
def mt5_history_deals_paginated(limit: int = 20, offset: int = 0) -> str:
    """Paginated deal history with profit summary."""
    return _j(get_backend().history_deals_paginated(limit=limit, offset=offset))


@mcp.tool()
def mt5_symbol_spec(symbol: str) -> str:
    """Return trading constraints for a symbol (digits, lot_step, contract_size)."""
    return _j(get_backend().symbol_spec(symbol))


@mcp.tool()
def mt5_account_equity_curve() -> str:
    """Account metrics with equity curve time series."""
    return _j(get_backend().account_equity_curve())


@mcp.tool()
def mt5_positions_detailed() -> str:
    """Open positions with detailed PnL fields (floating profit, current price, margin)."""
    return _j(get_backend().positions())


# ---------------------------------------------------------------------------
# Live bridge tools — delegate to MetaTrader5 Python package when available
# ---------------------------------------------------------------------------


@mcp.tool()
def mt5_live_doctor() -> str:
    """Check live MT5 bridge health (package presence, terminal, account)."""
    return _j(_live_bridge.doctor())


@mcp.tool()
def mt5_live_account() -> str:
    """Live MT5 account info via MetaTrader5 Python package."""
    return _j(_live_bridge.account_info())


@mcp.tool()
def mt5_live_terminal_info() -> str:
    """Live MT5 terminal environment details."""
    return _j(_live_bridge.terminal_info())


@mcp.tool()
def mt5_live_symbols(group: str = "*") -> str:
    """List symbols visible in the live MT5 terminal (optionally filtered by group)."""
    return _j(_live_bridge.symbols_get(group))


@mcp.tool()
def mt5_live_symbol_info(symbol: str) -> str:
    """Detailed live symbol specification: digits, spread, contract size, limits."""
    return _j(_live_bridge.symbol_info(symbol))


@mcp.tool()
def mt5_live_quote(symbol: str) -> str:
    """Live bid/ask/last tick for a symbol."""
    return _j(_live_bridge.symbol_info_tick(symbol))


@mcp.tool()
def mt5_live_positions(symbol: str | None = None) -> str:
    """Live open positions (optionally filtered by symbol)."""
    return _j(_live_bridge.positions_get(symbol))


@mcp.tool()
def mt5_live_orders(symbol: str | None = None) -> str:
    """Live pending orders (optionally filtered by symbol)."""
    return _j(_live_bridge.orders_get(symbol))


@mcp.tool()
def mt5_live_order_send(
    symbol: str,
    volume: float,
    side: str = "buy",
    order_type: str = "market",
    price: float = 0.0,
    sl: float = 0.0,
    tp: float = 0.0,
    deviation: int = 10,
    magic: int = 0,
    comment: str = "mt5-mcp",
    type_filling: int = 0,
    type_time: int = 0,
) -> str:
    """Send a trade order to the live MT5 terminal.

    side maps to: buy→ORDER_TYPE_BUY(0), sell→ORDER_TYPE_SELL(1).
    order_type maps to: market→TRADE_ACTION_DEAL(1), limit→ORDER_TYPE_BUY_LIMIT(2)/SELL_LIMIT(3),
    stop→ORDER_TYPE_BUY_STOP(4)/SELL_STOP(5).
    """
    import MetaTrader5 as _mt5  # type: ignore[import-untyped]  # noqa: N813
    side_l = side.strip().lower()
    ot = (order_type or "market").strip().lower()
    action = _mt5.TRADE_ACTION_DEAL
    if ot == "market":
        order_type_id = _mt5.ORDER_TYPE_BUY if side_l == "buy" else _mt5.ORDER_TYPE_SELL
    elif ot == "limit":
        action = _mt5.TRADE_ACTION_PENDING
        order_type_id = _mt5.ORDER_TYPE_BUY_LIMIT if side_l == "buy" else _mt5.ORDER_TYPE_SELL_LIMIT
    elif ot == "stop":
        action = _mt5.TRADE_ACTION_PENDING
        order_type_id = _mt5.ORDER_TYPE_BUY_STOP if side_l == "buy" else _mt5.ORDER_TYPE_SELL_STOP
    else:
        return _j({"ok": False, "error": f"unsupported order_type: {order_type}"})
    request = {
        "action": action,
        "symbol": symbol,
        "volume": volume,
        "type": order_type_id,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": deviation,
        "magic": magic,
        "comment": comment,
        "type_filling": type_filling or _mt5.ORDER_FILLING_FOK,
        "type_time": type_time or _mt5.ORDER_TIME_GTC,
    }
    return _j(_live_bridge.order_send(request))


@mcp.tool()
def mt5_live_history_deals(
    date_from: int = 0,
    date_to: int = 0,
    ticket: int = 0,
    position: int = 0,
) -> str:
    """Live deal history from MT5 terminal."""
    kwargs: dict[str, int] = {}
    if date_from:
        kwargs["date_from"] = date_from
    if date_to:
        kwargs["date_to"] = date_to
    if ticket:
        kwargs["ticket"] = ticket
    if position:
        kwargs["position"] = position
    return _j(_live_bridge.history_deals_get(**kwargs))


@mcp.tool()
def mt5_live_rates(
    symbol: str,
    timeframe: int = 1,  # M1 by default
    start_pos: int = 0,
    count: int = 100,
) -> str:
    """Live OHLCV rates from MT5 terminal (M1=1, M5=5, M15=15, H1=16385, D1=16388)."""
    return _j(_live_bridge.copy_rates_from_pos(symbol, timeframe, start_pos, count))


def run_stdio() -> None:
    mcp.run(transport="stdio")
