import os
from unittest.mock import MagicMock, patch
import pytest
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","src"))
from live_mt5_bridge import ConnectionState, LiveMT5Bridge, MT5Config, SymbolInfo, _is_live_mode, _MOCK_SYMBOLS

class TestConnectionState:
    def test_all_states_exist(self):
        assert ConnectionState.DISCONNECTED.value == 1
        assert ConnectionState.CONNECTING.value == 2
        assert ConnectionState.CONNECTED.value == 3
        assert ConnectionState.ERROR.value == 4

    def test_str_representation(self):
        assert str(ConnectionState.DISCONNECTED) == "disconnected"
        assert str(ConnectionState.CONNECTED) == "connected"
        assert str(ConnectionState.ERROR) == "error"

class TestMT5Config:
    def test_defaults(self):
        cfg = MT5Config()
        assert cfg.login is None
        assert cfg.password is None
        assert cfg.server is None
        assert cfg.timeout == 60_000
        assert cfg.portable is False

    def test_from_env_populated(self, monkeypatch):
        monkeypatch.setenv("MT5_LOGIN","12345678")
        monkeypatch.setenv("MT5_PASSWORD","s3cret")
        monkeypatch.setenv("MT5_SERVER","Broker-Demo")
        monkeypatch.setenv("MT5_PATH","/opt/mt5/terminal64.exe")
        monkeypatch.setenv("MT5_TIMEOUT","30000")
        monkeypatch.setenv("MT5_PORTABLE","1")
        cfg = MT5Config.from_env()
        assert cfg.login == 12345678
        assert cfg.password == "s3cret"
        assert cfg.server == "Broker-Demo"
        assert cfg.timeout == 30_000
        assert cfg.portable is True

    def test_from_env_invalid_login(self, monkeypatch):
        monkeypatch.setenv("MT5_LOGIN","not-a-number")
        cfg = MT5Config.from_env()
        assert cfg.login is None

class TestSymbolInfo:
    def test_fields(self):
        s = SymbolInfo(symbol="EURUSD",bid=1.08515,ask=1.08535,spread=20,digits=5,contract_size=100000,lot_step=0.01,point=0.00001)
        assert s.symbol == "EURUSD"
        assert s.bid == 1.08515
        assert s.contract_size == 100000

    def test_to_dict(self):
        s = SymbolInfo(symbol="XAUUSD",bid=2324.10,ask=2324.50,spread=40,digits=2,contract_size=100,lot_step=0.01,point=0.01,trade_mode="full",description="Gold")
        d = s.to_dict()
        assert d["symbol"] == "XAUUSD"
        assert d["spread"] == 40
        assert d["description"] == "Gold"

class TestIsLiveMode:
    def test_default_off(self, monkeypatch):
        monkeypatch.delenv("MT5_LIVE_MODE", raising=False)
        assert _is_live_mode() is False

    def test_explicit_on(self, monkeypatch):
        for val in ("1","true","ye"+"s","on"):
            monkeypatch.setenv("MT5_LIVE_MODE", val)
            assert _is_live_mode() is True

    def test_explicit_off(self, monkeypatch):
        for val in ("0","false","no","off",""):
            monkeypatch.setenv("MT5_LIVE_MODE", val)
            assert _is_live_mode() is False

class TestLiveMT5BridgeMock:
    @pytest.fixture(autouse=True)
    def _no_live_env(self, monkeypatch):
        monkeypatch.delenv("MT5_LIVE_MODE", raising=False)

    def test_initial_state(self):
        b = LiveMT5Bridge()
        assert b.state == ConnectionState.DISCONNECTED
        assert b.live_mode is False

    def test_initialize_mock(self):
        b = LiveMT5Bridge()
        r = b.initialize()
        assert r == ConnectionState.CONNECTED

    def test_shutdown_mock(self):
        b = LiveMT5Bridge()
        b.initialize()
        b.shutdown()
        assert b.state == ConnectionState.DISCONNECTED

    def test_get_symbol_info_known(self):
        b = LiveMT5Bridge()
        b.initialize()
        info = b.get_symbol_info("EURUSD")
        assert info is not None
        assert info.symbol == "EURUSD"
        assert info.bid > 0

    def test_get_symbol_info_unknown(self):
        b = LiveMT5Bridge()
        b.initialize()
        assert b.get_symbol_info("NONEXIST") is None

    def test_all_mock_symbols(self):
        b = LiveMT5Bridge()
        b.initialize()
        for sym in _MOCK_SYMBOLS:
            info = b.get_symbol_info(sym)
            assert info is not None, f"{sym} should resolve"
            assert info.symbol == sym

class TestLiveMT5BridgeLiveFallback:
    @pytest.fixture(autouse=True)
    def _live_env(self, monkeypatch):
        monkeypatch.setenv("MT5_LIVE_MODE","1")

    def test_graceful_fallback_import_error(self):
        import builtins
        orig = builtins.__import__
        def block_mt5(name,*a,**kw):
            if name == "MetaTrader5":
                raise ImportError("No MetaTrader5")
            return orig(name,*a,**kw)
        b = LiveMT5Bridge(live_mode=True)
        with patch.object(builtins,"__import__", side_effect=block_mt5):
            r = b.initialize()
        assert r == ConnectionState.CONNECTED
        assert b.live_mode is False

class TestLiveMT5BridgeLiveHappy:
    @pytest.fixture(autouse=True)
    def _live_env(self, monkeypatch):
        monkeypatch.setenv("MT5_LIVE_MODE","1")

    def test_initialize_success(self):
        fake = MagicMock()
        fake.initialize.return_value = True
        b = LiveMT5Bridge(live_mode=True)
        b._mt5 = fake
        r = b.initialize()
        assert r == ConnectionState.CONNECTED
        fake.initialize.assert_called_once()

    def test_initialize_failure(self):
        fake = MagicMock()
        fake.initialize.return_value = False
        fake.last_error.return_value = (1,"fail")
        b = LiveMT5Bridge(live_mode=True)
        b._mt5 = fake
        b.live_mode = True
        r = b.initialize()
        assert r == ConnectionState.ERROR

    def test_get_symbol_info_live(self):
        fake = MagicMock()
        raw = MagicMock()
        raw.name = "EURUSD"
        raw.bid = 1.0850
        raw.ask = 1.0852
        raw.spread = 20
        raw.digits = 5
        raw.trade_contract_size = 100000
        raw.volume_step = 0.01
        raw.point = 0.00001
        raw.trade_mode = 0
        raw.description = "Euro"
        fake.symbol_info.return_value = raw
        b = LiveMT5Bridge(live_mode=True)
        b._mt5 = fake
        b.state = ConnectionState.CONNECTED
        info = b.get_symbol_info("EURUSD")
        assert info is not None
        assert info.bid == 1.0850
        assert info.description == "Euro"

    def test_shutdown_live(self):
        fake = MagicMock()
        b = LiveMT5Bridge(live_mode=True)
        b._mt5 = fake
        b.state = ConnectionState.CONNECTED
        b.shutdown()
        fake.shutdown.assert_called_once()
        assert b.state == ConnectionState.DISCONNECTED
