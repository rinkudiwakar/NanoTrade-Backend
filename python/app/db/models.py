"""
app/db/models.py

Pydantic models representing database rows returned from Supabase.
These are used for response serialization and internal type safety.
They do NOT interact with the database directly — that's Supabase's job.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ---------------------------------------------------------------------------
# Profile (maps to `profiles` table)
# ---------------------------------------------------------------------------


class ProfileModel(BaseModel):
    id: str
    balance: float = Field(..., description="Virtual INR balance")
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Order (maps to `orders` table)
# ---------------------------------------------------------------------------


class OrderModel(BaseModel):
    id: str
    user_id: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    price: float = Field(..., description="Price in INR, 2 decimal precision")
    quantity: float = Field(..., description="Quantity in BTC, 6 decimal precision")
    status: str = Field(..., description="NEW | PARTIALLY_FILLED | FILLED | CANCELLED")
    is_bot: bool = False
    source: str = Field(default="user", description="'user' or 'simulator'")
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Trade (maps to `trades` table)
# ---------------------------------------------------------------------------


class TradeModel(BaseModel):
    id: str
    buyer_id: str
    seller_id: str
    price: float = Field(..., description="Matched price in INR")
    quantity: float = Field(..., description="Traded quantity in BTC")
    is_bot_trade: bool = False
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Portfolio holding (maps to `portfolios` table)
# ---------------------------------------------------------------------------


class PortfolioHoldingModel(BaseModel):
    user_id: str
    asset: str = Field(default="BTC")
    quantity: float = Field(..., description="BTC quantity held")
    avg_price: float = Field(..., description="Weighted average buy price in INR")


# ---------------------------------------------------------------------------
# Composite response models (used by API routes)
# ---------------------------------------------------------------------------


class PortfolioResponse(BaseModel):
    user_id: str
    balance: float = Field(..., description="Available INR balance")
    holdings: list[PortfolioHoldingModel] = []


class OrderbookEntry(BaseModel):
    price: float
    quantity: float


class OrderbookResponse(BaseModel):
    bids: list[OrderbookEntry] = []
    asks: list[OrderbookEntry] = []


class PriceResponse(BaseModel):
    binance_price_usd: Optional[float] = None
    usd_inr_rate: Optional[float] = None
    reference_price_inr: Optional[float] = None
    last_traded_price_inr: Optional[float] = None


class RecentTradeResponse(BaseModel):
    id: str
    price: float
    quantity: float
    created_at: Optional[datetime] = None
