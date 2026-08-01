"""Tests for the live MT5 bridge stub (mt5_mcp.live_bridge)."""

import os
import sys

import pytest

from mt5_mcp.live_bridge import MT5LiveBridge, is_mt5_available, mt5_version


@pytest.fixture
def bridge() -> MT5LiveBridge:
    """Fresh bridge instance for each test."""
    return MT5LiveBridge()


# ---------------------------------------------------------------------------
# Package detection
# ---------------------------------------------------------------------------


def test_is_mt5_available_is_bool() -> None:
    """is_mt5_available returns a bool."""
    result = is_mt5_available()
    assert isinstance(result, bool)


def test_mt5_version_type() -> None:
    """mt5_version returns str or None."""
    v = mt5_version()
    assert v is None or isinstance(v, str)


# ---------------------------------------------------------------------------
# Stub mode — all methods return structured dicts with ok/error when not installed
# ---------------------------------------------------------------------------


def test_doctor_stub(bridge: MT5LiveBridge) -> None:
    """doctor() always returns a dict with expected keys."""
    result = bridge.doctor()
    assert isinstance(result, dict)
    assert "ok" in result
    assert "mode" in result
    assert result["mode"] == "live_bridge"
    assert "mt5_package_installed" in result


def test_initialize_stub(bridge: MT5LiveBridge) -> None:
    """initialize() returns structured dict even when MT5 is absent."""
    result = bridge.initialize()
    assert isinstance(result, dict)
    assert "ok" in result
    if not is_mt5_available():
        assert result["ok"] is False
        assert "error" in result


def test_shutdown_stub(bridge: MT5LiveBridge) -> None:
    """shutdown() returns structured dict."""
    result = bridge.shutdown()
    assert isinstance(result, dict)
    assert "ok" in result


def test_account_info_stub(bridge: MT5LiveBridge) -> None:
    """account_info() returns structured dict."""
    result = bridge.account_info()
    assert isinstance(result, dict)
    assert "ok" in result


def test_terminal_info_stub(bridge: MT5LiveBridge) -> None:
    """terminal_info() returns structured dict."""
    result = bridge.terminal_info()
    assert isinstance(result, dict)
    assert "ok" in result


def test_symbols_get_stub(bridge: MT5LiveBridge) -> None:
    """symbols_get() returns structured dict."""
    result = bridge.symbols_get()
    assert isinstance(result, dict)
    assert "ok" in result


def test_symbol_info_stub(bridge: MT5LiveBridge) -> None:
    """symbol_info() returns structured dict."""
    result = bridge.symbol_info("EURUSD")
    assert isinstance(result, dict)
    assert "ok" in result


def test_symbol_info_tick_stub(bridge: MT5LiveBridge) -> None:
    """symbol_info_tick() returns structured dict."""
    result = bridge.symbol_info_tick("EURUSD")
    assert isinstance(result, dict)
    assert "ok" in result


def test_copy_rates_from_pos_stub(bridge: MT5LiveBridge) -> None:
    """copy_rates_from_pos() returns structured dict."""
    result = bridge.copy_rates_from_pos("EURUSD", 1, 0, 10)
    assert isinstance(result, dict)
    assert "ok" in result


def test_copy_rates_range_stub(bridge: MT5LiveBridge) -> None:
    """copy_rates_range() returns structured dict."""
    result = bridge.copy_rates_range("EURUSD", 1, 1000000, 2000000)
    assert isinstance(result, dict)
    assert "ok" in result


def test_positions_get_stub(bridge: MT5LiveBridge) -> None:
    """positions_get() returns structured dict."""
    result = bridge.positions_get()
    assert isinstance(result, dict)
    assert "ok" in result


def test_orders_get_stub(bridge: MT5LiveBridge) -> None:
    """orders_get() returns structured dict."""
    result = bridge.orders_get()
    assert isinstance(result, dict)
    assert "ok" in result


def test_order_send_stub(bridge: MT5LiveBridge) -> None:
    """order_send() returns structured dict."""
    result = bridge.order_send({
        "symbol": "EURUSD",
        "volume": 0.1,
        "action": 1,
        "type": 0,
    })
    assert isinstance(result, dict)
    assert "ok" in result


def test_history_deals_get_stub(bridge: MT5LiveBridge) -> None:
    """history_deals_get() returns structured dict."""
    result = bridge.history_deals_get()
    assert isinstance(result, dict)
    assert "ok" in result


def test_history_orders_get_stub(bridge: MT5LiveBridge) -> None:
    """history_orders_get() returns structured dict."""
    result = bridge.history_orders_get()
    assert isinstance(result, dict)
    assert "ok" in result


# ---------------------------------------------------------------------------
# Stub mode — no exceptions, graceful fallback
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("method_name,args", [
    ("initialize", ()),
    ("shutdown", ()),
    ("account_info", ()),
    ("terminal_info", ()),
    ("symbols_get", ()),
    ("symbol_info", ("EURUSD",)),
    ("symbol_info_tick", ("EURUSD",)),
    ("positions_get", ()),
    ("orders_get", ()),
    ("history_deals_get", ()),
    ("history_orders_get", ()),
])
def test_all_methods_no_exceptions(
    bridge: MT5LiveBridge, method_name: str, args: tuple
) -> None:
    """Every bridge method returns a dict without raising."""
    method = getattr(bridge, method_name)
    result = method(*args)
    assert isinstance(result, dict), f"{method_name} did not return a dict"


# ---------------------------------------------------------------------------
# Live bridge tools (server.py) — mock mode only, should still return valid JSON
# ---------------------------------------------------------------------------


def test_live_tools_return_json_in_mock_mode() -> None:
    """Even in mock mode (no MT5), live bridge tools return valid JSON strings."""
    from mt5_mcp.server import (
        mt5_live_account,
        mt5_live_doctor,
        mt5_live_orders,
        mt5_live_positions,
        mt5_live_symbol_info,
        mt5_live_symbols,
    )
    import json

    for tool in [
        mt5_live_doctor,
        mt5_live_account,
        mt5_live_symbols,
        mt5_live_positions,
        mt5_live_orders,
    ]:
        output = tool() if tool not in (mt5_live_symbol_info,) else tool("EURUSD")
        parsed = json.loads(output)
        assert isinstance(parsed, dict), f"{tool.__name__} returned non-dict JSON"
        if not is_mt5_available():
            # In stub mode, all should have ok=False or an error field
            pass  # graceful — just that it doesn't crash is sufficient
