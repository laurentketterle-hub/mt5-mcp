import os
import sys
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

class ConnectionState(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ERROR = auto()
    def __str__(self): return self.name.lower()

@dataclass
class MT5Config:
    login: int | None = None
    password: str | None = None
    server: str | None = None
    path: str | None = None
    timeout: int = 60_000
    portable: bool = False
    @classmethod
    def from_env(cls):
        raw = os.environ.get("MT5_LOGIN","")
        login = int(raw) if raw.isdigit() else None
        return cls(login=login, password=os.environ.get("MT5_PASSWORD"), server=os.environ.get("MT5_SERVER"), path=os.environ.get("MT5_PATH"), timeout=int(os.environ.get("MT5_TIMEOUT","60000")), portable=os.environ.get("MT5_PORTABLE","0").lower() in ("1","true","ye"+"s"))

@dataclass
class SymbolInfo:
    symbol: str
    bid: float
    ask: float
    spread: int
    digits: int
    contract_size: float
    lot_step: float
    point: float
    trade_mode: str = "full"
    description: str = ""
    def to_dict(self): return {"symbol":self.symbol,"bid":self.bid,"ask":self.ask,"spread":self.spread,"digits":self.digits,"contract_size":self.contract_size,"lot_step":self.lot_step,"point":self.point,"trade_mode":self.trade_mode,"description":self.description}
_MOCK_SYMBOLS = {
    "EURUSD": {"bid": 1.08515, "ask": 1.08535, "digits": 5, "contract_size": 100000, "lot_step": 0.01, "point": 0.00001},
    "GBPUSD": {"bid": 1.26490, "ask": 1.26515, "digits": 5, "contract_size": 100000, "lot_step": 0.01, "point": 0.00001},
    "USDJPY": {"bid": 149.510, "ask": 149.535, "digits": 3, "contract_size": 100000, "lot_step": 0.01, "point": 0.001},
    "XAUUSD": {"bid": 2324.10, "ask": 2324.50, "digits": 2, "contract_size": 100, "lot_step": 0.01, "point": 0.01},
    "BTCUSD": {"bid": 67500.00, "ask": 67550.00, "digits": 2, "contract_size": 1, "lot_step": 0.01, "point": 1.0},
}

def _is_live_mode():
    v = (os.environ.get("MT5_LIVE_MODE") or "").strip().lower()
    return v in ("1","true","ye"+"s","on")

class LiveMT5Bridge:
    state: ConnectionState
    config: MT5Config
    live_mode: bool

    def __init__(self, config: MT5Config | None = None, *, live_mode: bool | None = None):
        self.config = config or MT5Config.from_env()
        self.live_mode = live_mode if live_mode is not None else _is_live_mode()
        self.state = ConnectionState.DISCONNECTED
        self._mt5: Any = None

    def initialize(self):
        if not self.live_mode:
            self.state = ConnectionState.CONNECTED
            return self.state
        self.state = ConnectionState.CONNECTING
        if self._mt5 is not None:
            _mt5_mod = self._mt5
        else:
            try:
                import MetaTrader5 as _mt5_mod
            except ImportError:
                print("[LiveMT5Bridge] MetaTrader5 package not installed. Falling back to mock.", file=sys.stderr)
                self.live_mode = False
                self.state = ConnectionState.CONNECTED
                return self.state
            self._mt5 = _mt5_mod
        kwargs = {}
        for key in ("login","password","server","path","timeout","portable"):
            val = getattr(self.config, key, None)
            if val is not None:
                kwargs[key] = val
        try:
            ok = self._mt5.initialize(**kwargs)
        except Exception as exc:
            print(f"[LiveMT5Bridge] initialize() raised: {exc}", file=sys.stderr)
            self.state = ConnectionState.ERROR
            return self.state
        if ok:
            self.state = ConnectionState.CONNECTED
        else:
            print(f"[LiveMT5Bridge] initialize() returned False", file=sys.stderr)
            self.state = ConnectionState.ERROR
        return self.state

    def shutdown(self):
        if self._mt5 is not None and self.state == ConnectionState.CONNECTED:
            try:
                self._mt5.shutdown()
            except Exception as exc:
                print(f"[LiveMT5Bridge] shutdown() raised: {exc}", file=sys.stderr)
        self.state = ConnectionState.DISCONNECTED

    def get_symbol_info(self, symbol: str):
        sym = symbol.upper()
        if self._mt5 is not None and self.state == ConnectionState.CONNECTED:
            try:
                raw = self._mt5.symbol_info(sym)
                if raw is None:
                    return None
                return SymbolInfo(
                    symbol=raw.name if hasattr(raw,"name") else sym,
                    bid=float(getattr(raw,"bid",0.0)),
                    ask=float(getattr(raw,"ask",0.0)),
                    spread=int(getattr(raw,"spread",0)),
                    digits=int(getattr(raw,"digits",5)),
                    contract_size=float(getattr(raw,"trade_contract_size",100000)),
                    lot_step=float(getattr(raw,"volume_step",0.01)),
                    point=float(getattr(raw,"point",0.00001)),
                    trade_mode=str(getattr(raw,"trade_mode","full")),
                    description=str(getattr(raw,"description","")))
            except Exception as exc:
                print(f"[LiveMT5Bridge] symbol_info raised: {exc}", file=sys.stderr)
                return None
        snap = _MOCK_SYMBOLS.get(sym)
        if snap is None:
            return None
        return SymbolInfo(
            symbol=sym,
            bid=float(snap["bid"]),
            ask=float(snap["ask"]),
            spread=abs(int(round((snap["ask"]-snap["bid"])/snap["point"]))),
            digits=int(snap["digits"]),
            contract_size=float(snap["contract_size"]),
            lot_step=float(snap["lot_step"]),
            point=float(snap["point"]))
