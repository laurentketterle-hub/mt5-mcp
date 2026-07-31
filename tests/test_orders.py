"""Tests for mt5-mcp order operations."""
from src.mt5_mcp.ops import place_market_order, symbol_spec


def test_place_market_order_buy():
    result = place_market_order("EURUSD", 0.1, "buy", sl=1.0500, tp=1.0600)
    assert result["ok"] is True
    assert result["symbol"] == "EURUSD"
    assert result["order_type"] == "buy"
    assert result["sl"] == 1.05
    assert result["tp"] == 1.06
    assert "order_id" in result


def test_place_market_order_sell():
    result = place_market_order("GBPUSD", 0.5, "sell", sl=1.2600, tp=1.2500)
    assert result["ok"] is True
    assert result["order_type"] == "sell"


def test_place_market_order_no_sltp():
    result = place_market_order("USDJPY", 1.0, "buy")
    assert result["ok"] is True
    assert result["sl"] == 0.0
    assert result["tp"] == 0.0


def test_place_market_order_invalid_symbol():
    result = place_market_order("", 0.1, "buy")
    assert result["ok"] is False
    assert "Symbol" in result["error"]


def test_place_market_order_negative_volume():
    result = place_market_order("EURUSD", -1, "buy")
    assert result["ok"] is False
    assert "positive" in result["error"]


def test_place_market_order_invalid_type():
    result = place_market_order("EURUSD", 0.1, "hold")
    assert result["ok"] is False
    assert "buy" in result["error"]


def test_place_market_order_buy_tp_below_sl():
    result = place_market_order("EURUSD", 0.1, "buy", sl=1.0600, tp=1.0500)
    assert result["ok"] is False
    assert "TP must be above SL" in result["error"]


def test_place_market_order_sell_sl_below_tp():
    result = place_market_order("GBPUSD", 0.5, "sell", sl=1.2500, tp=1.2600)
    assert result["ok"] is False
    assert "SL must be above TP" in result["error"]


def test_symbol_spec_eurusd():
    spec = symbol_spec("EURUSD")
    assert spec["digits"] == 5
    assert spec["lot_step"] == 0.01
    assert spec["contract_size"] == 100000


def test_symbol_spec_xauusd():
    spec = symbol_spec("XAUUSD")
    assert spec["digits"] == 2
    assert spec["contract_size"] == 100


def test_symbol_spec_unknown():
    spec = symbol_spec("UNKNOWN")
    assert spec["digits"] == 5  # default
    assert spec["symbol"] == "UNKNOWN"
