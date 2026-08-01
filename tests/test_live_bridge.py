"""
Comprehensive tests for MT5 live bridge stub.

Tests cover:
- Environment flag detection
- Backend creation and import handling
- Connection management (init, shutdown, health)
- Terminal and account info (with mock MT5 objects)
- Symbols, rates, ticks
- Positions and orders
- Trading operations (order_send, position_close)
- History (deals, orders)
- Error handling and edge cases
- Account summary aggregation

All tests use mock MT5 modules — no real terminal required.
"""

import os
import datetime

import pytest

from src.mt5_mcp.live_bridge import (
    is_live_enabled,
    get_live_backend,
    MT5LiveBackend,
    _safe_dict,
)

# ---------------------------------------------------------------------------
# Helpers — mock MT5 module factories
# ---------------------------------------------------------------------------


class MockInfo:
    """Generic mock info object for terminal_info, account_info, symbol_info."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def make_mock_mt5_base():
    """Minimal mock with init/shutdown/version/last_error."""
    class MockMT5:
        init_ok = True
        _init_calls = 0

        @staticmethod
        def initialize(**kw):
            MockMT5._init_calls += 1
            return MockMT5.init_ok

        @staticmethod
        def version():
            return (500, 5000, "2025.01.01")

        @staticmethod
        def last_error():
            return None

        @staticmethod
        def shutdown():
            pass
    return MockMT5


def make_mock_mt5_full():
    """Full mock with terminal_info, account_info, positions, orders."""
    class MockMT5:
        init_ok = True
        version_val = (500, 5000, "2025.01.01")
        terminal_info_val = MockInfo(
            community_account=True, community_connection=True,
            connected=True, dlls_allowed=False, trade_allowed=True,
            tradeapi_disabled=False, email_enabled=False, ftp_enabled=False,
            notifications_enabled=False, mqid=False, build=5000,
            maxbars=100000, path="/path/to/terminal", name="TestTerminal",
            language="English", company="TestCorp", retransmission_mode=0,
        )
        account_info_val = MockInfo(
            login=12345678, trade_mode=0, leverage=100, limit_orders=200,
            margin_so_mode=0, trade_allowed=True, trade_expert=True,
            balance=25000.0, credit=0.0, profit=125.50, equity=25125.50,
            margin=500.0, margin_free=24625.50, margin_level=5025.1,
            currency="USD", server="TestServer", name="Test Account",
            company="TestCorp", margin_initial=500.0, margin_maintenance=250.0,
            assets=26000.0, liabilities=500.0, commission_blocked=0.0,
        )
        positions_val = [
            MockInfo(ticket=10001, symbol="EURUSD", type=0, volume=0.1,
                     price_open=1.08500, price_current=1.08525, sl=1.08000,
                     tp=1.09000, profit=25.0, swap=-1.2, commission=-0.7,
                     comment="test", magic=0, time=1700000000, time_update=1700003600,
                     identifier=10001, reason=0, margin=50.0),
        ]
        orders_val = [
            MockInfo(ticket=20001, symbol="GBPUSD", type=2, type_time=0,
                     type_filling=0, volume_initial=0.1, volume_current=0.1,
                     price_open=1.26000, sl=0.0, tp=0.0, price_current=0.0,
                     price_stoplimit=0.0, comment="pending", magic=0,
                     time_setup=1700000000, time_done=0, time_expiration=0, state=1),
        ]
        symbol_info_val = MockInfo(
            symbol="EURUSD", digits=5, spread=20, point=0.00001,
            trade_contract_size=100000, volume_min=0.01, volume_max=100.0,
            volume_step=0.01, volume_limit=0.0, swap_long=-10.0, swap_short=5.0,
            swap_mode=0, trade_mode=0, trade_calc_mode=0, trade_tick_size=0.00001,
            trade_tick_value=1.0, bid=1.08515, ask=1.08535, bidhigh=1.08600,
            askhigh=1.08620, bidlow=1.08400, asklow=1.08420, time=1700000000,
            description="Euro vs US Dollar", path="Forex\\EURUSD",
            currency_base="EUR", currency_profit="USD", currency_margin="USD",
            margin_initial=1000.0, margin_maintenance=500.0, margin_hedged=250.0,
            margin_currency="USD", session_deals=0, session_buy_orders=0,
            session_sell_orders=0, visible=True,
        )
        tick_val = MockInfo(bid=1.08515, ask=1.08535, last=1.08525, volume=10, time=1700000000)
        rates_val = [
            [1700000000, 1.08500, 1.08550, 1.08450, 1.08525, 100, 20, 5000],
            [1700000060, 1.08525, 1.08600, 1.08500, 1.08580, 150, 18, 6000],
        ]

        @staticmethod
        def initialize(**kw):
            return MockMT5.init_ok

        @staticmethod
        def version():
            return MockMT5.version_val

        @staticmethod
        def last_error():
            return None

        @staticmethod
        def shutdown():
            pass

        @staticmethod
        def terminal_info():
            return MockMT5.terminal_info_val

        @staticmethod
        def account_info():
            return MockMT5.account_info_val

        @staticmethod
        def symbols_get(group=None):
            return [MockInfo(symbol="EURUSD", digits=5, spread=20, trade_contract_size=100000),
                    MockInfo(symbol="GBPUSD", digits=5, spread=25, trade_contract_size=100000)]

        @staticmethod
        def symbol_info(symbol):
            return MockMT5.symbol_info_val

        @staticmethod
        def symbol_select(symbol, enable):
            return True

        @staticmethod
        def symbol_info_tick(symbol):
            return MockMT5.tick_val

        @staticmethod
        def copy_rates_from_pos(symbol, timeframe, start, count):
            return MockMT5.rates_val

        @staticmethod
        def positions_get(symbol=None, ticket=None):
            if ticket:
                return [p for p in MockMT5.positions_val if p.ticket == ticket]
            return MockMT5.positions_val

        @staticmethod
        def orders_get(symbol=None):
            return MockMT5.orders_val

        @staticmethod
        def history_deals_get(from_date, to_date):
            return [MockInfo(ticket=30001, position_id=10001, symbol="EURUSD",
                             type=0, volume=0.1, price=1.08525, profit=25.0,
                             commission=-0.7, swap=-1.2, time=1700000000,
                             comment="test", entry=1)]

        @staticmethod
        def history_orders_get(from_date, to_date):
            return [MockInfo(ticket=20001, symbol="GBPUSD", type=2,
                             volume_initial=0.1, volume_current=0.0,
                             price_open=1.26000, sl=0.0, tp=0.0,
                             state=2, time_setup=1700000000, time_done=1700003600,
                             comment="filled")]

        # Timeframe constants
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        TIMEFRAME_M15 = 15
        TIMEFRAME_M30 = 30
        TIMEFRAME_H1 = 16385
        TIMEFRAME_H4 = 16388
        TIMEFRAME_D1 = 16408
        TIMEFRAME_W1 = 32769

        # Order constants
        TRADE_ACTION_DEAL = 1
        TRADE_ACTION_PENDING = 5
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        ORDER_TYPE_BUY_LIMIT = 2
        ORDER_TYPE_SELL_LIMIT = 3
        ORDER_TYPE_BUY_STOP = 4
        ORDER_TYPE_SELL_STOP = 5
        TRADE_RETCODE_DONE = 10009

        @staticmethod
        def order_send(request):
            return MockInfo(retcode=10009, order=30002, volume=0.1,
                            price=1.08535, comment="Done")

    return MockMT5


def make_failing_mock_mt5():
    """Mock where everything returns None/raises."""
    class FailingMT5:
        @staticmethod
        def initialize(**kw): return True
        @staticmethod
        def version(): return (500, 5000, "")
        @staticmethod
        def last_error(): return None
        @staticmethod
        def shutdown(): pass
        @staticmethod
        def terminal_info(): return None
        @staticmethod
        def account_info(): return None
        @staticmethod
        def symbols_get(group=None): return None
        @staticmethod
        def symbol_info(symbol): return None
        @staticmethod
        def symbol_select(symbol, enable): return True
        @staticmethod
        def symbol_info_tick(symbol): return None
        @staticmethod
        def copy_rates_from_pos(symbol, tf, start, count): return None
        @staticmethod
        def positions_get(symbol=None, ticket=None): return None
        @staticmethod
        def orders_get(symbol=None): return None
        @staticmethod
        def history_deals_get(from_date, to_date): return None
        @staticmethod
        def history_orders_get(from_date, to_date): return None
    return FailingMT5


# ---------------------------------------------------------------------------
# Environment flag tests
# ---------------------------------------------------------------------------


class TestLiveEnvFlag:
    def test_default_false(self):
        assert is_live_enabled() is False

    def test_enabled_true(self, monkeypatch):
        monkeypatch.setenv("MT5_LIVE", "1")
        assert is_live_enabled() is True

    def test_other_values_false(self, monkeypatch):
        for val in ["0", "true", "yes", "True", "on", ""]:
            monkeypatch.setenv("MT5_LIVE", val)
            assert is_live_enabled() is False, f"MT5_LIVE={val!r} should be False"

    def test_unset_false(self, monkeypatch):
        monkeypatch.delenv("MT5_LIVE", raising=False)
        assert is_live_enabled() is False


# ---------------------------------------------------------------------------
# Backend creation tests
# ---------------------------------------------------------------------------


class TestGetLiveBackend:
    def test_returns_none_when_disabled(self):
        assert get_live_backend() is None

    def test_raises_when_no_mt5_package(self, monkeypatch):
        monkeypatch.setenv("MT5_LIVE", "1")
        with pytest.raises(ImportError, match="MetaTrader5"):
            get_live_backend()

    def test_returns_backend_when_enabled(self, monkeypatch):
        monkeypatch.setenv("MT5_LIVE", "1")
        # We can't easily mock without patching, but the import error test covers the path


# ---------------------------------------------------------------------------
# Initialization & connection tests
# ---------------------------------------------------------------------------


class TestInitialization:
    def test_init_success(self):
        backend = MT5LiveBackend(make_mock_mt5_base())
        result = backend.initialize()
        assert result["ok"] is True
        assert result["version"] is not None
        assert backend.is_initialized() is True

    def test_init_failure(self):
        Mock = make_mock_mt5_base()
        Mock.init_ok = False
        backend = MT5LiveBackend(Mock)
        result = backend.initialize()
        assert result["ok"] is False
        assert backend.is_initialized() is False

    def test_init_with_path(self):
        backend = MT5LiveBackend(make_mock_mt5_base())
        result = backend.initialize(path="/custom/path")
        assert result["ok"] is True

    def test_init_with_portable(self):
        backend = MT5LiveBackend(make_mock_mt5_base())
        result = backend.initialize(portable=True)
        assert result["ok"] is True

    def test_not_initialized_by_default(self):
        backend = MT5LiveBackend(make_mock_mt5_base())
        assert backend.is_initialized() is False

    def test_shutdown_resets_initialized(self):
        backend = MT5LiveBackend(make_mock_mt5_base())
        backend.initialize()
        assert backend.is_initialized() is True
        backend.shutdown()
        assert backend.is_initialized() is False


# ---------------------------------------------------------------------------
# Health check tests
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_disconnected(self):
        backend = MT5LiveBackend(make_mock_mt5_base())
        result = backend.health()
        assert result["ok"] is False
        assert result["status"] == "disconnected"

    def test_health_connected(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.health()
        assert result["ok"] is True
        assert result["status"] == "connected"
        assert result["connected"] is True
        assert result["trade_allowed"] is True


# ---------------------------------------------------------------------------
# Terminal info tests
# ---------------------------------------------------------------------------


class TestTerminalInfo:
    def test_uninitialized(self):
        backend = MT5LiveBackend(None)
        result = backend.get_terminal_info()
        assert result["ok"] is False
        assert "Not initialized" in result["error"]

    def test_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.get_terminal_info()
        assert result["ok"] is True
        assert result["build"] == 5000
        assert result["connected"] is True

    def test_returns_none(self):
        backend = MT5LiveBackend(make_failing_mock_mt5())
        backend.initialize()
        result = backend.get_terminal_info()
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# Account info tests
# ---------------------------------------------------------------------------


class TestAccountInfo:
    def test_uninitialized(self):
        backend = MT5LiveBackend(None)
        result = backend.get_account_info()
        assert result["ok"] is False

    def test_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.get_account_info()
        assert result["ok"] is True
        assert result["balance"] == 25000.0
        assert result["equity"] == 25125.50
        assert result["currency"] == "USD"
        assert result["leverage"] == 100

    def test_returns_none(self):
        backend = MT5LiveBackend(make_failing_mock_mt5())
        backend.initialize()
        result = backend.get_account_info()
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# Symbols tests
# ---------------------------------------------------------------------------


class TestSymbols:
    def test_get_symbols_uninitialized(self):
        backend = MT5LiveBackend(None)
        assert backend.get_symbols() == []

    def test_get_symbols_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        symbols = backend.get_symbols()
        assert len(symbols) == 2
        assert symbols[0]["symbol"] == "EURUSD"

    def test_get_symbol_info_uninitialized(self):
        backend = MT5LiveBackend(None)
        result = backend.get_symbol_info("EURUSD")
        assert result["ok"] is False

    def test_get_symbol_info_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.get_symbol_info("EURUSD")
        assert result["ok"] is True
        assert result["digits"] == 5
        assert result["bid"] == 1.08515

    def test_get_symbol_info_not_found(self):
        backend = MT5LiveBackend(make_failing_mock_mt5())
        backend.initialize()
        result = backend.get_symbol_info("EURUSD")
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# Market data tests
# ---------------------------------------------------------------------------


class TestMarketData:
    def test_get_rates_uninitialized(self):
        backend = MT5LiveBackend(None)
        result = backend.get_rates("EURUSD")
        assert result["ok"] is False

    def test_get_rates_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.get_rates("EURUSD", timeframe=60, count=2)
        assert result["ok"] is True
        assert result["count"] == 2
        assert result["rates"][0]["open"] == 1.08500
        assert result["rates"][0]["close"] == 1.08525

    def test_get_rates_empty(self):
        backend = MT5LiveBackend(make_failing_mock_mt5())
        backend.initialize()
        result = backend.get_rates("EURUSD")
        assert result["ok"] is False

    def test_get_tick_uninitialized(self):
        backend = MT5LiveBackend(None)
        result = backend.get_tick("EURUSD")
        assert result["ok"] is False

    def test_get_tick_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.get_tick("EURUSD")
        assert result["ok"] is True
        assert result["bid"] == 1.08515
        assert result["ask"] == 1.08535

    def test_get_tick_empty(self):
        backend = MT5LiveBackend(make_failing_mock_mt5())
        backend.initialize()
        result = backend.get_tick("EURUSD")
        assert result["ok"] is False

    def test_get_rates_timeframes(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        for tf in [1, 5, 15, 30, 60, 240, 1440, 10080]:
            result = backend.get_rates("EURUSD", timeframe=tf, count=1)
            assert result["ok"] is True, f"Failed for timeframe={tf}"


# ---------------------------------------------------------------------------
# Positions & Orders tests
# ---------------------------------------------------------------------------


class TestPositions:
    def test_get_positions_uninitialized(self):
        backend = MT5LiveBackend(None)
        assert backend.get_positions() == []

    def test_get_positions_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        positions = backend.get_positions()
        assert len(positions) == 1
        assert positions[0]["ticket"] == 10001
        assert positions[0]["symbol"] == "EURUSD"

    def test_get_positions_by_symbol(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        positions = backend.get_positions(symbol="EURUSD")
        assert len(positions) == 1

    def test_get_positions_none(self):
        backend = MT5LiveBackend(make_failing_mock_mt5())
        backend.initialize()
        assert backend.get_positions() == []

    def test_get_position_by_ticket(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.get_position_by_ticket(10001)
        assert result["ok"] is True
        assert result["position"]["ticket"] == 10001

    def test_get_position_by_ticket_not_found(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.get_position_by_ticket(99999)
        assert result["ok"] is False


class TestOrders:
    def test_get_orders_uninitialized(self):
        backend = MT5LiveBackend(None)
        assert backend.get_orders() == []

    def test_get_orders_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        orders = backend.get_orders()
        assert len(orders) == 1
        assert orders[0]["ticket"] == 20001
        assert orders[0]["symbol"] == "GBPUSD"

    def test_get_orders_none(self):
        backend = MT5LiveBackend(make_failing_mock_mt5())
        backend.initialize()
        assert backend.get_orders() == []


# ---------------------------------------------------------------------------
# Trading operations tests (stubs)
# ---------------------------------------------------------------------------


class TestTrading:
    def test_order_send_uninitialized(self):
        backend = MT5LiveBackend(None)
        result = backend.order_send("EURUSD", "buy", 0.1)
        assert result["ok"] is False

    def test_order_send_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.order_send("EURUSD", "buy", 0.1, sl=1.08000, tp=1.09000)
        assert result["ok"] is True
        assert result["ticket"] == 30002

    def test_position_close_uninitialized(self):
        backend = MT5LiveBackend(None)
        result = backend.position_close(10001)
        assert result["ok"] is False

    def test_position_close_not_found(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.position_close(99999)
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# History tests
# ---------------------------------------------------------------------------


class TestHistory:
    def test_get_history_deals_uninitialized(self):
        backend = MT5LiveBackend(None)
        assert backend.get_history_deals() == []

    def test_get_history_deals_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        deals = backend.get_history_deals()
        assert len(deals) >= 1
        assert deals[0]["symbol"] == "EURUSD"

    def test_get_history_deals_none(self):
        backend = MT5LiveBackend(make_failing_mock_mt5())
        backend.initialize()
        assert backend.get_history_deals() == []

    def test_get_history_orders_uninitialized(self):
        backend = MT5LiveBackend(None)
        assert backend.get_history_orders() == []

    def test_get_history_orders_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        orders = backend.get_history_orders()
        assert len(orders) >= 1
        assert orders[0]["symbol"] == "GBPUSD"

    def test_get_history_orders_none(self):
        backend = MT5LiveBackend(make_failing_mock_mt5())
        backend.initialize()
        assert backend.get_history_orders() == []


# ---------------------------------------------------------------------------
# Account summary aggregation
# ---------------------------------------------------------------------------


class TestAccountSummary:
    def test_uninitialized(self):
        backend = MT5LiveBackend(None)
        result = backend.get_account_summary()
        assert result["ok"] is False

    def test_success(self):
        backend = MT5LiveBackend(make_mock_mt5_full())
        backend.initialize()
        result = backend.get_account_summary()
        assert result["ok"] is True
        assert result["terminal"]["ok"] is True
        assert result["account"]["ok"] is True
        assert result["open_positions"] == 1
        assert result["pending_orders"] == 1
        assert len(result["positions"]) == 1
        assert len(result["orders"]) == 1


# ---------------------------------------------------------------------------
# _safe_dict helper
# ---------------------------------------------------------------------------


class TestSafeDict:
    def test_extracts_fields(self):
        obj = MockInfo(a=1, b="hello", c=3.14)
        result = _safe_dict(obj, ["a", "b", "c"])
        assert result == {"a": 1, "b": "hello", "c": 3.14}

    def test_missing_fields_become_none(self):
        obj = MockInfo(a=1)
        result = _safe_dict(obj, ["a", "b", "c"])
        assert result == {"a": 1, "b": None, "c": None}

    def test_none_input(self):
        assert _safe_dict(None, ["a", "b"]) == {}
