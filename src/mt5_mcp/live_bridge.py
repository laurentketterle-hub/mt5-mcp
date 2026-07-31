"""
Live MetaTrader5 Python package bridge stub.
Optional live backend behind MT5_LIVE=1 env flag; mock remains default.

SAFETY WARNING:
- Live trading can result in real financial loss.
- Always test with MT5_LIVE=0 (mock) first.
- Use a demo account for initial live testing.
- Never run live trading unattended.
"""

import os


def is_live_enabled() -> bool:
    """Check if live MT5 bridge is enabled via environment variable."""
    return os.environ.get("MT5_LIVE", "0") == "1"


def get_live_backend():
    """
    Return a live MT5 backend if enabled, otherwise None.
    
    Returns:
        MT5LiveBackend | None: Live backend instance or None if mock.
        
    Raises:
        ImportError: If MetaTrader5 package is not installed.
    """
    if not is_live_enabled():
        return None
    
    try:
        import MetaTrader5 as mt5
    except ImportError:
        raise ImportError(
            "MetaTrader5 Python package not found. "
            "Install with: pip install MetaTrader5"
        )
    
    return MT5LiveBackend(mt5)


class MT5LiveBackend:
    """
    Live MetaTrader5 backend wrapper.
    
    Bridges MCP operations to real MT5 terminal.
    All operations are idempotent — check mt5.initialize() result
    before each call to ensure terminal connectivity.
    """
    
    def __init__(self, mt5_module):
        self._mt5 = mt5_module
        self._initialized = False
    
    def initialize(self, path: str = None, portable: bool = False) -> dict:
        """Initialize connection to MT5 terminal."""
        try:
            kwargs = {}
            if path:
                kwargs['path'] = path
            if portable:
                kwargs['portable'] = True
            
            result = self._mt5.initialize(**kwargs)
            self._initialized = result
            return {
                "ok": result,
                "version": self._mt5.version() if result else None,
                "error": self._mt5.last_error() if not result else None,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def shutdown(self) -> None:
        """Disconnect from MT5 terminal."""
        self._mt5.shutdown()
        self._initialized = False
    
    def is_initialized(self) -> bool:
        """Check if connected to MT5 terminal."""
        return self._initialized
    
    def get_terminal_info(self) -> dict:
        """Get MT5 terminal information."""
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        try:
            info = self._mt5.terminal_info()
            if info is None:
                return {"ok": False, "error": "terminal_info returned None"}
            return {
                "ok": True,
                "community_account": info.community_account,
                "community_connection": info.community_connection,
                "connected": info.connected,
                "dlls_allowed": info.dlls_allowed,
                "trade_allowed": info.trade_allowed,
                "tradeapi_disabled": info.tradeapi_disabled,
                "email_enabled": info.email_enabled,
                "ftp_enabled": info.ftp_enabled,
                "notifications_enabled": info.notifications_enabled,
                "mqid": info.mqid,
                "build": info.build,
                "maxbars": info.maxbars,
                "path": info.path,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def get_account_info(self) -> dict:
        """Get current account information."""
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        try:
            info = self._mt5.account_info()
            if info is None:
                return {"ok": False, "error": "account_info returned None"}
            return {
                "ok": True,
                "login": info.login,
                "trade_mode": info.trade_mode,
                "leverage": info.leverage,
                "limit_orders": info.limit_orders,
                "margin_so_mode": info.margin_so_mode,
                "trade_allowed": info.trade_allowed,
                "trade_expert": info.trade_expert,
                "balance": info.balance,
                "credit": info.credit,
                "profit": info.profit,
                "equity": info.equity,
                "margin": info.margin,
                "margin_free": info.margin_free,
                "margin_level": info.margin_level,
                "currency": info.currency,
                "server": info.server,
                "name": info.name,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
