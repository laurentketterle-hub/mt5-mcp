"""
Symbol Specification Tool - trading constraints from mock specs.
"""
from dataclasses import dataclass

@dataclass
class SymbolSpec:
    symbol: str
    digits: int = 5
    lot_step: float = 0.01
    min_lot: float = 0.01
    max_lot: float = 100.0
    contract_size: float = 100000.0
    margin_required: float = 1000.0
    spread: int = 10

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}

MOCK_SPECS = {
    "EURUSD": SymbolSpec("EURUSD", digits=5, spread=10),
    "GBPUSD": SymbolSpec("GBPUSD", digits=5, spread=15),
    "USDJPY": SymbolSpec("USDJPY", digits=3, spread=10),
    "XAUUSD": SymbolSpec("XAUUSD", digits=2, spread=30),
}

def get_symbol_spec(symbol):
    symbol = symbol.upper().strip()
    spec = MOCK_SPECS.get(symbol, SymbolSpec(symbol))
    d = spec.to_dict()
    d["spread_points"] = d.pop("spread")
    return d
