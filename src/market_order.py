"""
Market Order Tool - place market orders with optional SL/TP.
"""
from dataclasses import dataclass
from typing import Optional
import uuid

@dataclass
class Position:
    ticket: str
    symbol: str
    volume: float
    price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    type: str = "buy"

def place_market_order(symbol, volume, order_type="buy", sl=None, tp=None, comment=""):
    symbol = symbol.upper().strip()
    if volume <= 0:
        return {"error": "Volume must be positive", "status": "rejected"}
    if order_type not in ("buy", "sell"):
        return {"error": "Invalid order type", "status": "rejected"}
    mock_price = 1.1000 if "USD" in symbol else 150.00
    return {
        "ticket": str(uuid.uuid4())[:8], "symbol": symbol,
        "volume": volume, "type": order_type, "price": mock_price,
        "status": "filled", "comment": comment,
        "sl": sl, "tp": tp,
    }
