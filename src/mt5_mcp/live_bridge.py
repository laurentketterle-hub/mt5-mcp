"""
Live MetaTrader5 Python package bridge stub.

Provides a thin wrapper around the official `MetaTrader5` Python package
(pip install MetaTrader5). Falls back gracefully when the package is not
installed or no MT5 terminal is running — all methods return structured
results with ``ok``, ``error``, and ``meta`` fields.

Usage::

    from mt5_mcp.live_bridge import MT5LiveBridge
    bridge = MT5LiveBridge()
    result = bridge.initialize()
    if result["ok"]:
        print(bridge.account_info())
    bridge.shutdown()
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional import — MetaTrader5 is only available on Windows with MT5 installed
# ---------------------------------------------------------------------------
_MT5_AVAILABLE = False
_mt5_module: Any = None

try:
    import MetaTrader5 as _mt5_module  # type: ignore[import-untyped]

    _MT5_AVAILABLE = True
except ImportError:
    _mt5_module = None
    logger.debug("MetaTrader5 package not installed — live bridge will operate in stub mode")


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def is_mt5_available() -> bool:
    """Return True if the MetaTrader5 Python package is importable."""
    return _MT5_AVAILABLE


def mt5_version() -> str | None:
    """Return the MetaTrader5 package version string, or None."""
    if _mt5_module is not None and hasattr(_mt5_module, "__version__"):
        return str(_mt5_module.__version__)
    return None


# ---------------------------------------------------------------------------
# MT5LiveBridge
# ---------------------------------------------------------------------------


class MT5LiveBridge:
    """Stub bridge for the MetaTrader5 Python package.

    On hosts where ``MetaTrader5`` is installed and a terminal is running,
    methods delegate to the real package.  Otherwise every method returns a
    structured error so callers can handle the unavailability gracefully.
    """

    name = "live_bridge"

    def __init__(self) -> None:
        self._initialized = False
        self._login: int | None = None

    # -- lifecycle -----------------------------------------------------------

    def initialize(
        self,
        path: str | None = None,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        timeout: int = 60_000,
        portable: bool = False,
    ) -> dict[str, Any]:
        """Connect to the MT5 terminal.

        Parameters
        ----------
        path:
            Path to terminal.exe (auto-detect when omitted).
        login, password, server:
            Trading account credentials.
        timeout:
            Connection timeout in milliseconds.
        portable:
            Use portable mode.

        Returns
        -------
        dict with ``ok`` and optional ``login`` / ``error``.
        """
        if not _MT5_AVAILABLE:
            return {
                "ok": False,
                "error": (
                    "MetaTrader5 Python package is not installed. "
                    "Install it with: pip install MetaTrader5"
                ),
                "meta": {"mt5_available": False},
            }

        try:
            kwargs: dict[str, Any] = {"timeout": timeout, "portable": portable}
            if path:
                kwargs["path"] = path
            if login is not None:
                kwargs["login"] = login
            if password:
                kwargs["password"] = password
            if server:
                kwargs["server"] = server

            ok = bool(_mt5_module.initialize(**kwargs))
            if ok:
                self._initialized = True
                info = _mt5_module.terminal_info()
                if info is not None:
                    self._login = int(getattr(info, "login", 0) or 0)
                return {
                    "ok": True,
                    "login": self._login,
                    "terminal": str(info) if info else None,
                    "mt5_version": mt5_version(),
                }
            error = _mt5_module.last_error()
            return {
                "ok": False,
                "error": f"MT5 initialize failed: code={error[0]} {error[1]}"
                if error
                else "MT5 initialize returned False",
                "meta": {"mt5_available": True},
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": f"MT5 initialize exception: {exc}",
                "meta": {"mt5_available": True},
            }

    def shutdown(self) -> dict[str, Any]:
        """Disconnect from the MT5 terminal."""
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            _mt5_module.shutdown()
            self._initialized = False
            return {"ok": True, "message": "MT5 shutdown complete"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # -- account -------------------------------------------------------------

    def account_info(self) -> dict[str, Any]:
        """Return MT5 account information.

        Returns balance, equity, margin, currency, leverage, trade mode, etc.
        """
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            info = _mt5_module.account_info()
            if info is None:
                err = _mt5_module.last_error()
                return {
                    "ok": False,
                    "error": f"account_info returned None: {err}",
                }
            return {
                "ok": True,
                "login": int(info.login),
                "server": str(info.server),
                "currency": str(info.currency),
                "leverage": int(info.leverage),
                "trade_mode": int(info.trade_mode),
                "balance": float(info.balance),
                "credit": float(info.credit),
                "equity": float(info.equity),
                "margin": float(info.margin),
                "margin_free": float(info.margin_free),
                "margin_level": float(info.margin_level) if hasattr(info, "margin_level") else None,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def terminal_info(self) -> dict[str, Any]:
        """Return MT5 terminal information."""
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            info = _mt5_module.terminal_info()
            if info is None:
                return {"ok": False, "error": "terminal_info returned None"}
            return {
                "ok": True,
                "community_account": bool(info.community_account),
                "community_connection": bool(info.community_connection),
                "connected": bool(info.connected),
                "dlls_allowed": bool(info.dlls_allowed),
                "trade_allowed": bool(info.trade_allowed),
                "tradeapi_disabled": bool(info.tradeapi_disabled),
                "email_enabled": bool(info.email_enabled),
                "ftp_enabled": bool(info.ftp_enabled),
                "notifications_enabled": bool(info.notifications_enabled),
                "mqid": bool(info.mqid),
                "build": int(info.build),
                "maxbars": int(info.maxbars),
                "codepage": int(info.codepage),
                "ping_last": int(info.ping_last),
                "path": str(info.path),
                "data_path": str(info.data_path),
                "commondata_path": str(info.commondata_path),
                "name": str(info.name),
                "language": str(info.language),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # -- symbols -------------------------------------------------------------

    def symbols_get(self, group: str = "*") -> dict[str, Any]:
        """Return all symbols (or filtered by *group* wildcard).

        Returns
        -------
        dict with ``ok``, ``count``, and ``symbols`` (list of symbol dicts).
        """
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            symbols = _mt5_module.symbols_get(group)
            if symbols is None:
                return {"ok": False, "error": "symbols_get returned None — is terminal connected?"}
            # symbols_get returns a tuple of SymbolInfo objects
            result: list[dict[str, Any]] = []
            for s in symbols:
                result.append({
                    "name": s.name,
                    "description": getattr(s, "description", ""),
                    "digits": int(s.digits),
                    "spread": int(s.spread),
                    "trade_mode": int(s.trade_mode),
                    "contract_size": float(s.trade_contract_size),
                    "volume_min": float(s.volume_min),
                    "volume_max": float(s.volume_max),
                    "volume_step": float(s.volume_step),
                    "point": float(s.point),
                    "trade_tick_value": float(s.trade_tick_value),
                    "currency_base": str(s.currency_base),
                    "currency_profit": str(s.currency_profit),
                    "currency_margin": str(s.currency_margin),
                })
            return {"ok": True, "count": len(result), "symbols": result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def symbol_info(self, symbol: str) -> dict[str, Any]:
        """Return detailed info for a single symbol."""
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            info = _mt5_module.symbol_info(symbol)
            if info is None:
                return {"ok": False, "error": f"symbol_info returned None for {symbol}"}
            return {
                "ok": True,
                "name": info.name,
                "digits": int(info.digits),
                "spread": int(info.spread),
                "trade_mode": int(info.trade_mode),
                "contract_size": float(info.trade_contract_size),
                "volume_min": float(info.volume_min),
                "volume_max": float(info.volume_max),
                "volume_step": float(info.volume_step),
                "point": float(info.point),
                "trade_tick_value": float(info.trade_tick_value),
                "bid": float(info.bid),
                "ask": float(info.ask),
                "bidhigh": float(info.bidhigh) if hasattr(info, "bidhigh") else None,
                "bidlow": float(info.bidlow) if hasattr(info, "bidlow") else None,
                "askhigh": float(info.askhigh) if hasattr(info, "askhigh") else None,
                "asklow": float(info.asklow) if hasattr(info, "asklow") else None,
                "time": int(info.time) if hasattr(info, "time") else None,
                "currency_base": str(info.currency_base),
                "currency_profit": str(info.currency_profit),
                "currency_margin": str(info.currency_margin),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def symbol_info_tick(self, symbol: str) -> dict[str, Any]:
        """Return latest tick for *symbol*."""
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            tick = _mt5_module.symbol_info_tick(symbol)
            if tick is None:
                return {"ok": False, "error": f"symbol_info_tick returned None for {symbol}"}
            return {
                "ok": True,
                "symbol": symbol,
                "bid": float(tick.bid),
                "ask": float(tick.ask),
                "last": float(tick.last),
                "volume": int(tick.volume) if hasattr(tick, "volume") else None,
                "time": int(tick.time),
                "time_msc": int(tick.time_msc) if hasattr(tick, "time_msc") else None,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # -- rates ---------------------------------------------------------------

    def copy_rates_from_pos(
        self, symbol: str, timeframe: int, start_pos: int = 0, count: int = 100
    ) -> dict[str, Any]:
        """Return *count* bars from *start_pos* for *symbol*."""
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            rates = _mt5_module.copy_rates_from_pos(symbol, timeframe, start_pos, count)
            if rates is None:
                return {"ok": False, "error": f"copy_rates_from_pos returned None for {symbol}"}
            result = []
            for r in rates:
                result.append({
                    "time": int(r["time"]),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "tick_volume": int(r["tick_volume"]),
                    "spread": int(r["spread"]),
                    "real_volume": int(r["real_volume"]),
                })
            return {"ok": True, "count": len(result), "rates": result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def copy_rates_range(
        self,
        symbol: str,
        timeframe: int,
        date_from: int,
        date_to: int,
    ) -> dict[str, Any]:
        """Return bars between *date_from* and *date_to* for *symbol*."""
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            rates = _mt5_module.copy_rates_range(symbol, timeframe, date_from, date_to)
            if rates is None:
                return {"ok": False, "error": f"copy_rates_range returned None for {symbol}"}
            result = []
            for r in rates:
                result.append({
                    "time": int(r["time"]),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "tick_volume": int(r["tick_volume"]),
                    "spread": int(r["spread"]),
                    "real_volume": int(r["real_volume"]),
                })
            return {"ok": True, "count": len(result), "rates": result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # -- positions / orders --------------------------------------------------

    def positions_get(self, symbol: str | None = None, ticket: int | None = None) -> dict[str, Any]:
        """Return open positions, optionally filtered by *symbol* / *ticket*."""
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            kwargs: dict[str, Any] = {}
            if symbol:
                kwargs["symbol"] = symbol
            if ticket is not None:
                kwargs["ticket"] = ticket

            positions = _mt5_module.positions_get(**kwargs)
            if positions is None:
                # None means "no positions" — not an error
                return {"ok": True, "count": 0, "positions": []}
            result = []
            for p in positions:
                result.append({
                    "ticket": int(p.ticket),
                    "symbol": str(p.symbol),
                    "type": int(p.type),
                    "volume": float(p.volume),
                    "price_open": float(p.price_open),
                    "price_current": float(p.price_current),
                    "sl": float(p.sl),
                    "tp": float(p.tp),
                    "profit": float(p.profit),
                    "swap": float(p.swap),
                    "commission": float(p.commission),
                    "comment": str(p.comment),
                    "time": int(p.time),
                    "magic": int(p.magic),
                    "identifier": int(p.identifier),
                    "reason": int(p.reason),
                })
            return {"ok": True, "count": len(result), "positions": result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def orders_get(
        self, symbol: str | None = None, ticket: int | None = None
    ) -> dict[str, Any]:
        """Return pending orders, optionally filtered by *symbol* / *ticket*."""
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            kwargs: dict[str, Any] = {}
            if symbol:
                kwargs["symbol"] = symbol
            if ticket is not None:
                kwargs["ticket"] = ticket

            orders = _mt5_module.orders_get(**kwargs)
            if orders is None:
                return {"ok": True, "count": 0, "orders": []}
            result = []
            for o in orders:
                result.append({
                    "ticket": int(o.ticket),
                    "symbol": str(o.symbol),
                    "type": int(o.type),
                    "volume_initial": float(o.volume_initial),
                    "volume_current": float(o.volume_current),
                    "price_open": float(o.price_open),
                    "sl": float(o.sl),
                    "tp": float(o.tp),
                    "price_current": float(o.price_current),
                    "comment": str(o.comment),
                    "time_setup": int(o.time_setup),
                    "time_done": int(o.time_done) if hasattr(o, "time_done") else 0,
                    "magic": int(o.magic),
                    "reason": int(o.reason),
                })
            return {"ok": True, "count": len(result), "orders": result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # -- trading -------------------------------------------------------------

    def order_send(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send a trade order.

        Parameters
        ----------
        request:
            Dict with keys: ``action``, ``symbol``, ``volume``, ``type``,
            ``price`` (optional for market), ``sl``, ``tp``, ``deviation``,
            ``magic``, ``comment``, ``type_filling``, ``type_time``.

        Returns
        -------
        dict with ``ok``, ``retcode``, ``ticket``, ``comment`` (MT5 result fields).
        """
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            mt5_request = {
                "action": request.get("action", _mt5_module.TRADE_ACTION_DEAL),
                "symbol": request["symbol"],
                "volume": float(request["volume"]),
                "type": request.get("type", _mt5_module.ORDER_TYPE_BUY),
                "price": float(request.get("price", 0.0)),
                "sl": float(request.get("sl", 0.0)),
                "tp": float(request.get("tp", 0.0)),
                "deviation": int(request.get("deviation", 10)),
                "magic": int(request.get("magic", 0)),
                "comment": str(request.get("comment", "mt5-mcp")),
                "type_filling": int(
                    request.get("type_filling", _mt5_module.ORDER_FILLING_FOK)
                ),
                "type_time": int(request.get("type_time", _mt5_module.ORDER_TIME_GTC)),
            }
            result = _mt5_module.order_send(mt5_request)
            if result is None:
                return {"ok": False, "error": "order_send returned None"}
            return {
                "ok": result.retcode == _mt5_module.TRADE_RETCODE_DONE,
                "retcode": int(result.retcode),
                "ticket": int(result.order) if result.order else None,
                "volume": float(result.volume),
                "price": float(result.price),
                "bid": float(result.bid),
                "ask": float(result.ask),
                "comment": str(result.comment),
                "request_id": str(result.request_id) if hasattr(result, "request_id") else None,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # -- history -------------------------------------------------------------

    def history_deals_get(
        self,
        date_from: int | None = None,
        date_to: int | None = None,
        ticket: int | None = None,
        position: int | None = None,
    ) -> dict[str, Any]:
        """Return deal history between *date_from* and *date_to*."""
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            kwargs: dict[str, Any] = {}
            if date_from is not None:
                kwargs["date_from"] = date_from
            if date_to is not None:
                kwargs["date_to"] = date_to
            if ticket is not None:
                kwargs["ticket"] = ticket
            if position is not None:
                kwargs["position"] = position

            deals = _mt5_module.history_deals_get(**kwargs)
            if deals is None:
                return {"ok": True, "count": 0, "deals": []}
            result = []
            for d in deals:
                result.append({
                    "ticket": int(d.ticket),
                    "order": int(d.order),
                    "position_id": int(d.position_id),
                    "symbol": str(d.symbol),
                    "type": int(d.type),
                    "entry": int(d.entry),
                    "volume": float(d.volume),
                    "price": float(d.price),
                    "commission": float(d.commission),
                    "swap": float(d.swap),
                    "profit": float(d.profit),
                    "time": int(d.time),
                    "comment": str(d.comment),
                    "magic": int(d.magic),
                    "reason": int(d.reason),
                })
            return {"ok": True, "count": len(result), "deals": result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def history_orders_get(
        self,
        date_from: int | None = None,
        date_to: int | None = None,
        ticket: int | None = None,
        position: int | None = None,
    ) -> dict[str, Any]:
        """Return order history between *date_from* and *date_to*."""
        if not _MT5_AVAILABLE:
            return {"ok": False, "error": "MetaTrader5 not installed"}
        try:
            kwargs: dict[str, Any] = {}
            if date_from is not None:
                kwargs["date_from"] = date_from
            if date_to is not None:
                kwargs["date_to"] = date_to
            if ticket is not None:
                kwargs["ticket"] = ticket
            if position is not None:
                kwargs["position"] = position

            orders = _mt5_module.history_orders_get(**kwargs)
            if orders is None:
                return {"ok": True, "count": 0, "orders": []}
            result = []
            for o in orders:
                result.append({
                    "ticket": int(o.ticket),
                    "position_id": int(o.position_id),
                    "symbol": str(o.symbol),
                    "type": int(o.type),
                    "volume_initial": float(o.volume_initial),
                    "volume_current": float(o.volume_current),
                    "price_open": float(o.price_open),
                    "sl": float(o.sl),
                    "tp": float(o.tp),
                    "price_current": float(o.price_current),
                    "time_setup": int(o.time_setup),
                    "time_done": int(o.time_done),
                    "state": int(o.state),
                    "comment": str(o.comment),
                    "magic": int(o.magic),
                    "reason": int(o.reason),
                })
            return {"ok": True, "count": len(result), "orders": result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # -- convenience ---------------------------------------------------------

    def doctor(self) -> dict[str, Any]:
        """Quick health check: package presence, terminal connectivity, account info."""
        result: dict[str, Any] = {
            "ok": False,
            "mode": "live_bridge",
            "mt5_package_installed": _MT5_AVAILABLE,
        }
        if _mt5_module is not None:
            result["mt5_version"] = mt5_version()

        if not _MT5_AVAILABLE:
            result["error"] = (
                "MetaTrader5 Python package not installed. "
                "Install with: pip install MetaTrader5"
            )
            return result

        # Try to check if a terminal is already connected
        try:
            ti = _mt5_module.terminal_info()
            if ti is not None:
                result["terminal_connected"] = bool(ti.connected)
                result["terminal_name"] = str(ti.name)
                result["terminal_build"] = int(ti.build)
                result["terminal_path"] = str(ti.path)

            ai = _mt5_module.account_info()
            if ai is not None:
                result["ok"] = True
                result["login"] = int(ai.login)
                result["server"] = str(ai.server)
                result["balance"] = float(ai.balance)
                result["equity"] = float(ai.equity)
            else:
                result["ok"] = False
                result["error"] = "Terminal found but no account logged in"
        except Exception as exc:
            result["ok"] = False
            result["error"] = f"Terminal probe failed: {exc}"

        return result
