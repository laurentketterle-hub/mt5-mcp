"""
Live MetaTrader5 Python package bridge stub.
Optional live backend behind MT5_LIVE=1 env flag; mock remains default.

SAFETY WARNING:
- Live trading can result in real financial loss.
- Always test with MT5_LIVE=0 (mock) first.
- Use a demo account for initial live testing.
- Never run live trading unattended.
"""

from __future__ import annotations

import os
from typing import Any


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


def _safe_dict(info, fields: list[str]) -> dict[str, Any]:
    """Extract fields from an MT5 info object into a dict, handling None."""
    if info is None:
        return {}
    result = {}
    for field in fields:
        try:
            result[field] = getattr(info, field)
        except (AttributeError, Exception):
            result[field] = None
    return result


class MT5LiveBackend:
    """
    Live MetaTrader5 backend wrapper.

    Bridges MCP operations to real MT5 terminal.
    All operations are idempotent — check mt5.initialize() result
    before each call to ensure terminal connectivity.

    Supports full MT5 API surface: account info, positions, orders,
    market data, symbol specs, trading operations, and deal history.
    """

    # Fields exposed by terminal_info()
    _TERMINAL_FIELDS = [
        "community_account", "community_connection", "connected",
        "dlls_allowed", "trade_allowed", "tradeapi_disabled",
        "email_enabled", "ftp_enabled", "notifications_enabled",
        "mqid", "build", "maxbars", "path", "name", "language",
        "company", "retransmission_mode",
    ]

    # Fields exposed by account_info()
    _ACCOUNT_FIELDS = [
        "login", "trade_mode", "leverage", "limit_orders",
        "margin_so_mode", "trade_allowed", "trade_expert",
        "balance", "credit", "profit", "equity", "margin",
        "margin_free", "margin_level", "currency", "server", "name",
        "company", "margin_initial", "margin_maintenance",
        "assets", "liabilities", "commission_blocked",
    ]

    # Fields exposed by symbol_info()
    _SYMBOL_FIELDS = [
        "symbol", "digits", "spread", "point", "trade_contract_size",
        "volume_min", "volume_max", "volume_step", "volume_limit",
        "swap_long", "swap_short", "swap_mode", "trade_mode",
        "trade_calc_mode", "trade_tick_size", "trade_tick_value",
        "bid", "ask", "bidhigh", "askhigh", "bidlow", "asklow",
        "time", "description", "path", "currency_base", "currency_profit",
        "currency_margin", "margin_initial", "margin_maintenance",
        "margin_hedged", "margin_currency", "session_deals",
        "session_buy_orders", "session_sell_orders",
    ]

    # Fields exposed by positions_get()
    _POSITION_FIELDS = [
        "ticket", "symbol", "type", "volume", "price_open",
        "price_current", "sl", "tp", "profit", "swap", "commission",
        "comment", "magic", "time", "time_update", "identifier",
        "reason", "margin",
    ]

    # Fields exposed by orders_get()
    _ORDER_FIELDS = [
        "ticket", "symbol", "type", "type_time", "type_filling",
        "volume_initial", "volume_current", "price_open", "sl", "tp",
        "price_current", "price_stoplimit", "comment", "magic",
        "time_setup", "time_done", "time_expiration", "state",
    ]

    def __init__(self, mt5_module):
        self._mt5 = mt5_module
        self._initialized = False

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

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

    def health(self) -> dict[str, Any]:
        """Quick connectivity health check (non-destructive)."""
        if not self._initialized:
            return {"ok": False, "status": "disconnected", "error": "Not initialized"}
        try:
            info = self._mt5.terminal_info()
            return {
                "ok": info is not None,
                "status": "connected" if info and info.connected else "no_terminal",
                "connected": info.connected if info else False,
                "trade_allowed": info.trade_allowed if info else False,
                "build": info.build if info else None,
                "community_connected": info.community_connection if info else False,
            }
        except Exception as e:
            return {"ok": False, "status": "error", "error": str(e)}

    # ------------------------------------------------------------------
    # Terminal & Account info
    # ------------------------------------------------------------------

    def get_terminal_info(self) -> dict:
        """Get MT5 terminal information."""
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        try:
            info = self._mt5.terminal_info()
            if info is None:
                return {"ok": False, "error": "terminal_info returned None"}
            return {"ok": True, **_safe_dict(info, self._TERMINAL_FIELDS)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_account_info(self) -> dict:
        """Get current account information with full metrics."""
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        try:
            info = self._mt5.account_info()
            if info is None:
                return {"ok": False, "error": "account_info returned None"}
            return {"ok": True, **_safe_dict(info, self._ACCOUNT_FIELDS)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Symbols & Market data
    # ------------------------------------------------------------------

    def get_symbols(self, group: str = None) -> list[dict[str, Any]]:
        """Get all available symbols, optionally filtered by group."""
        if not self._initialized:
            return []
        try:
            symbols = self._mt5.symbols_get(group) if group else self._mt5.symbols_get()
            if symbols is None:
                return []
            return [_safe_dict(s, ["symbol", "digits", "spread", "trade_contract_size"]) for s in symbols]
        except Exception:
            return []

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Get detailed symbol specification."""
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        try:
            info = self._mt5.symbol_info(symbol.upper())
            if info is None:
                return {"ok": False, "error": f"Symbol {symbol} not found"}
            # Always select the symbol first
            if not info.visible:
                self._mt5.symbol_select(symbol.upper(), True)
                info = self._mt5.symbol_info(symbol.upper())
                if info is None:
                    return {"ok": False, "error": f"Symbol {symbol} not available"}
            return {"ok": True, **_safe_dict(info, self._SYMBOL_FIELDS)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_rates(self, symbol: str, timeframe: int = 1, count: int = 100) -> dict[str, Any]:
        """Get OHLCV rates for a symbol. Timeframe in minutes (1=M1, 60=H1, 1440=D1)."""
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        try:
            tf_map = {
                1: self._mt5.TIMEFRAME_M1,
                5: self._mt5.TIMEFRAME_M5,
                15: self._mt5.TIMEFRAME_M15,
                30: self._mt5.TIMEFRAME_M30,
                60: self._mt5.TIMEFRAME_H1,
                240: self._mt5.TIMEFRAME_H4,
                1440: self._mt5.TIMEFRAME_D1,
                10080: self._mt5.TIMEFRAME_W1,
            }
            mt5_tf = tf_map.get(timeframe, self._mt5.TIMEFRAME_M1)
            rates = self._mt5.copy_rates_from_pos(symbol.upper(), mt5_tf, 0, count)
            if rates is None or len(rates) == 0:
                return {"ok": False, "error": f"No rates for {symbol}"}
            candles = []
            for r in rates:
                candles.append({
                    "time": int(r[0]),
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "tick_volume": int(r[5]) if len(r) > 5 else 0,
                    "spread": int(r[6]) if len(r) > 6 else 0,
                    "real_volume": int(r[7]) if len(r) > 7 else 0,
                })
            return {"ok": True, "symbol": symbol.upper(), "timeframe": timeframe, "count": len(candles), "rates": candles}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_tick(self, symbol: str) -> dict[str, Any]:
        """Get last tick (bid/ask) for a symbol."""
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        try:
            tick = self._mt5.symbol_info_tick(symbol.upper())
            if tick is None:
                return {"ok": False, "error": f"No tick for {symbol}"}
            return {
                "ok": True,
                "symbol": symbol.upper(),
                "bid": tick.bid,
                "ask": tick.ask,
                "last": tick.last,
                "volume": tick.volume if hasattr(tick, 'volume') else None,
                "time": tick.time,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Positions & Orders
    # ------------------------------------------------------------------

    def get_positions(self, symbol: str = None) -> list[dict[str, Any]]:
        """Get open positions, optionally filtered by symbol."""
        if not self._initialized:
            return []
        try:
            positions = self._mt5.positions_get(symbol=symbol.upper()) if symbol else self._mt5.positions_get()
            if positions is None:
                return []
            return [_safe_dict(p, self._POSITION_FIELDS) for p in positions]
        except Exception:
            return []

    def get_orders(self, symbol: str = None) -> list[dict[str, Any]]:
        """Get pending orders, optionally filtered by symbol."""
        if not self._initialized:
            return []
        try:
            orders = self._mt5.orders_get(symbol=symbol.upper()) if symbol else self._mt5.orders_get()
            if orders is None:
                return []
            return [_safe_dict(o, self._ORDER_FIELDS) for o in orders]
        except Exception:
            return []

    def get_position_by_ticket(self, ticket: int) -> dict[str, Any]:
        """Get a specific position by ticket number."""
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        try:
            pos = self._mt5.positions_get(ticket=ticket)
            if pos is None or len(pos) == 0:
                return {"ok": False, "error": f"Position {ticket} not found"}
            return {"ok": True, "position": _safe_dict(pos[0], self._POSITION_FIELDS)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Trading operations (stubs — require explicit live confirmation)
    # ------------------------------------------------------------------

    def order_send(self, symbol: str, side: str, volume: float,
                   order_type: str = "market", price: float = None,
                   sl: float = None, tp: float = None,
                   comment: str = "") -> dict[str, Any]:
        """
        Send a trading order to the live MT5 terminal.

        WARNING: This executes REAL trades on a live/demo account.
        Only call when you are certain live trading is intended.
        """
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        try:
            request = {
                "action": self._mt5.TRADE_ACTION_DEAL,
                "symbol": symbol.upper(),
                "volume": float(volume),
                "type": self._mt5.ORDER_TYPE_BUY if side.lower() == "buy" else self._mt5.ORDER_TYPE_SELL,
                "price": float(price) if price else 0.0,
                "sl": float(sl) if sl else 0.0,
                "tp": float(tp) if tp else 0.0,
                "deviation": 20,
                "magic": 0,
                "comment": comment or "mt5-mcp",
            }

            if order_type != "market":
                type_map = {
                    "buy_limit": self._mt5.ORDER_TYPE_BUY_LIMIT,
                    "sell_limit": self._mt5.ORDER_TYPE_SELL_LIMIT,
                    "buy_stop": self._mt5.ORDER_TYPE_BUY_STOP,
                    "sell_stop": self._mt5.ORDER_TYPE_SELL_STOP,
                }
                request["type"] = type_map.get(order_type, request["type"])
                request["action"] = self._mt5.TRADE_ACTION_PENDING

            result = self._mt5.order_send(request)
            return {
                "ok": result.retcode == self._mt5.TRADE_RETCODE_DONE if hasattr(self._mt5, 'TRADE_RETCODE_DONE') else result.retcode == 10009,
                "retcode": result.retcode,
                "ticket": result.order if result.order else None,
                "volume": result.volume,
                "price": result.price,
                "comment": result.comment,
                "error": result.comment if result.retcode != (self._mt5.TRADE_RETCODE_DONE if hasattr(self._mt5, 'TRADE_RETCODE_DONE') else 10009) else None,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def position_close(self, ticket: int, volume: float = None) -> dict[str, Any]:
        """
        Close a position by ticket number.

        WARNING: This executes REAL position closes on a live/demo account.
        """
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        try:
            pos_info = self._mt5.positions_get(ticket=ticket)
            if pos_info is None or len(pos_info) == 0:
                return {"ok": False, "error": f"Position {ticket} not found"}
            pos = pos_info[0]

            close_volume = float(volume) if volume else pos.volume

            request = {
                "action": self._mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": pos.symbol,
                "volume": close_volume,
                "type": self._mt5.ORDER_TYPE_SELL if pos.type == 0 else self._mt5.ORDER_TYPE_BUY,
                "price": self._mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else self._mt5.symbol_info_tick(pos.symbol).ask,
                "deviation": 20,
                "magic": 0,
                "comment": "mt5-mcp close",
            }
            result = self._mt5.order_send(request)
            return {
                "ok": result.retcode == (self._mt5.TRADE_RETCODE_DONE if hasattr(self._mt5, 'TRADE_RETCODE_DONE') else 10009),
                "retcode": result.retcode,
                "ticket": ticket,
                "deal": result.order if result.order else None,
                "price": result.price,
                "volume": result.volume,
                "error": result.comment if result.retcode != (self._mt5.TRADE_RETCODE_DONE if hasattr(self._mt5, 'TRADE_RETCODE_DONE') else 10009) else None,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Deal history
    # ------------------------------------------------------------------

    def get_history_deals(self, from_date=None, to_date=None, limit: int = 100) -> list[dict[str, Any]]:
        """Get deal history within a date range."""
        if not self._initialized:
            return []
        try:
            import datetime
            if from_date is None:
                from_date = datetime.datetime.now() - datetime.timedelta(days=7)
            if to_date is None:
                to_date = datetime.datetime.now()
            deals = self._mt5.history_deals_get(from_date, to_date)
            if deals is None:
                return []
            result = []
            for d in deals[:limit]:
                result.append({
                    "ticket": d.ticket,
                    "position_id": d.position_id if hasattr(d, 'position_id') else None,
                    "symbol": d.symbol,
                    "type": d.type,
                    "volume": d.volume,
                    "price": d.price,
                    "profit": d.profit,
                    "commission": d.commission,
                    "swap": d.swap,
                    "time": d.time,
                    "comment": d.comment,
                    "entry": d.entry if hasattr(d, 'entry') else None,
                })
            return result
        except Exception:
            return []

    def get_history_orders(self, from_date=None, to_date=None, limit: int = 100) -> list[dict[str, Any]]:
        """Get order history within a date range."""
        if not self._initialized:
            return []
        try:
            import datetime
            if from_date is None:
                from_date = datetime.datetime.now() - datetime.timedelta(days=7)
            if to_date is None:
                to_date = datetime.datetime.now()
            orders = self._mt5.history_orders_get(from_date, to_date)
            if orders is None:
                return []
            result = []
            for o in orders[:limit]:
                result.append({
                    "ticket": o.ticket,
                    "symbol": o.symbol,
                    "type": o.type,
                    "volume_initial": o.volume_initial,
                    "volume_current": o.volume_current,
                    "price_open": o.price_open,
                    "sl": o.sl,
                    "tp": o.tp,
                    "state": o.state,
                    "time_setup": o.time_setup,
                    "time_done": o.time_done,
                    "comment": o.comment,
                })
            return result
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Account summary
    # ------------------------------------------------------------------

    def get_account_summary(self) -> dict[str, Any]:
        """Get comprehensive account summary combining terminal + account info + positions."""
        if not self._initialized:
            return {"ok": False, "error": "Not initialized"}
        terminal = self.get_terminal_info()
        account = self.get_account_info()
        positions = self.get_positions()
        orders = self.get_orders()
        return {
            "ok": True,
            "terminal": terminal,
            "account": account,
            "open_positions": len(positions),
            "pending_orders": len(orders),
            "positions": positions,
            "orders": orders,
        }
