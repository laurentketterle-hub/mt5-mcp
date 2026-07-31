"""Tests for MT5 live bridge stub (mock-only, no real MT5 terminal needed)."""
import os
from src.mt5_mcp.live_bridge import is_live_enabled, get_live_backend, MT5LiveBackend


def test_is_live_enabled_default_false():
    assert is_live_enabled() is False


def test_is_live_enabled_true(monkeypatch):
    monkeypatch.setenv("MT5_LIVE", "1")
    assert is_live_enabled() is True


def test_is_live_enabled_other_values():
    os.environ["MT5_LIVE"] = "true"
    assert is_live_enabled() is False  # not "1"
    os.environ["MT5_LIVE"] = "0"


def test_get_live_backend_returns_none_when_disabled():
    assert get_live_backend() is None


def test_get_live_backend_raises_when_no_mt5_package(monkeypatch):
    monkeypatch.setenv("MT5_LIVE", "1")
    try:
        get_live_backend()
    except ImportError as e:
        assert "MetaTrader5" in str(e)


def test_mt5livebackend_init_sets_initialized():
    class FakeMT5:
        @staticmethod
        def initialize(**kw): return True
        @staticmethod
        def version(): return (500, 5000, "2024.01.01")
        @staticmethod
        def last_error(): return None
    backend = MT5LiveBackend(FakeMT5)
    result = backend.initialize()
    assert result["ok"] is True
    assert backend.is_initialized() is True


def test_mt5livebackend_get_account_info_uninit():
    backend = MT5LiveBackend(None)
    result = backend.get_account_info()
    assert result["ok"] is False
    assert "Not initialized" in result["error"]


def test_mt5livebackend_get_terminal_info_uninit():
    backend = MT5LiveBackend(None)
    result = backend.get_terminal_info()
    assert result["ok"] is False


def test_mt5livebackend_shutdown():
    class FakeMT5:
        @staticmethod
        def initialize(**kw): return True
        @staticmethod
        def version(): return (500, 5000, "")
        @staticmethod
        def last_error(): return None
        @staticmethod
        def shutdown(): pass
    backend = MT5LiveBackend(FakeMT5)
    backend.initialize()
    backend.shutdown()
    assert not backend.is_initialized()
