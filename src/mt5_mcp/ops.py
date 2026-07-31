
"""Order operations for MT5 MCP."""

def place_market_order(symbol: str, volume: float, order_type: str = "buy",
                       sl: float = 0.0, tp: float = 0.0, comment: str = "") -> dict:
    """Validate and place a market order with optional SL/TP."""
    if not symbol:
        return {"ok": False, "error": "Symbol is required"}
    if volume <= 0:
        return {"ok": False, "error": "Volume must be positive"}
    if order_type not in ("buy", "sell"):
        return {"ok": False, "error": "order_type must be 'buy' or 'sell'"}
    if sl < 0 or tp < 0:
        return {"ok": False, "error": "SL/TP must be >= 0"}
    if order_type == "buy" and sl > 0 and tp > 0 and tp <= sl:
        return {"ok": False, "error": "For buy orders, TP must be above SL"}
    if order_type == "sell" and sl > 0 and tp > 0 and sl <= tp:
        return {"ok": False, "error": "For sell orders, SL must be above TP"}
    
    return {
        "ok": True,
        "symbol": symbol,
        "volume": volume,
        "order_type": order_type,
        "sl": sl,
        "tp": tp,
        "comment": comment,
        "order_id": f"order_{symbol}_{order_type}_{int(volume * 1000)}",
    }


def symbol_spec(symbol: str) -> dict:
    """Return trading constraints for a symbol from mock specs."""
    MOCK_SPECS = {
        "EURUSD": {"digits": 5, "lot_step": 0.01, "min_lot": 0.01, "max_lot": 100.0,
                   "contract_size": 100000, "swap_long": -3.2, "swap_short": 1.5},
        "GBPUSD": {"digits": 5, "lot_step": 0.01, "min_lot": 0.01, "max_lot": 100.0,
                   "contract_size": 100000, "swap_long": -2.8, "swap_short": 1.2},
        "USDJPY": {"digits": 3, "lot_step": 0.01, "min_lot": 0.01, "max_lot": 100.0,
                   "contract_size": 100000, "swap_long": -4.1, "swap_short": 2.3},
        "XAUUSD": {"digits": 2, "lot_step": 0.01, "min_lot": 0.01, "max_lot": 50.0,
                   "contract_size": 100, "swap_long": -15.0, "swap_short": 8.0},
    }
    default_spec = {"digits": 5, "lot_step": 0.01, "min_lot": 0.01, "max_lot": 100.0,
                    "contract_size": 100000, "swap_long": 0.0, "swap_short": 0.0}
    
    return MOCK_SPECS.get(symbol.upper(), {**default_spec, "symbol": symbol})

