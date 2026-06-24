"""
app/services/strategy_service.py

Strategy Engine Service (Phase 2 — PRD Section 3.6).

Provides rule-based automated trading strategies that users can
activate to execute orders on their behalf.

Architecture rules:
- Strategy engine runs via Celery (background worker), NOT in API routes.
- Strategies submit orders through the /orders API (not directly to engine).
- All strategies are per-user and must pass fund validation.
- No direct DB access — uses portfolio_service for reads.

Current strategies:
    1. SimpleMovingAverage (SMA) crossover
    2. MeanReversion (RSI-style threshold)
    3. MomentumFollow

Phase 2 NOTE: Strategy execution (run_strategy_for_user) is designed to be
called from a Celery periodic task, not directly from API routes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

# ---------------------------------------------------------------------------
# Strategy Types & Config
# ---------------------------------------------------------------------------


class StrategyType(str, Enum):
    SIMPLE_MA = "simple_ma"  # Simple moving average crossover
    MEAN_REVERSION = "mean_reversion"  # Buy low / sell high around reference
    MOMENTUM = "momentum"  # Follow the trend


@dataclass
class StrategyConfig:
    """
    Configuration for a user's active strategy.
    Stored/fetched from Supabase (strategy config table — future).
    """

    strategy_type: StrategyType
    user_id: str
    asset: str = "BTC"

    # Common parameters
    order_quantity: float = 0.01  # BTC per signal, 6 decimal max
    max_open_orders: int = 3  # Safety cap on open simultaneous orders

    # SMA-specific
    short_window: int = 5  # Number of price ticks for short MA
    long_window: int = 20  # Number of price ticks for long MA

    # Mean reversion-specific
    deviation_pct: float = 0.005  # Buy if price is 0.5% below reference

    # Momentum-specific
    momentum_threshold: float = 0.003  # 0.3% move triggers momentum trade


@dataclass
class StrategySignal:
    """Result from strategy evaluation — what action to take."""

    should_trade: bool
    side: Optional[str] = None  # "BUY" or "SELL"
    price: Optional[float] = None  # Limit price in INR
    quantity: Optional[float] = None  # BTC quantity
    reason: str = ""


# ---------------------------------------------------------------------------
# Price history buffer (in-memory, per-worker)
# In production this would be backed by Redis or a time-series store.
# ---------------------------------------------------------------------------

_price_history: list[float] = []
_MAX_HISTORY = 100  # Keep last 100 ticks


def record_price(price: float) -> None:
    """
    Append a new price to the in-memory history buffer.
    Called by the Binance feed task every time a new reference price arrives.
    """
    global _price_history
    _price_history.append(price)
    if len(_price_history) > _MAX_HISTORY:
        _price_history = _price_history[-_MAX_HISTORY:]


def get_price_history() -> list[float]:
    """Return a copy of the current price history."""
    return list(_price_history)


# ---------------------------------------------------------------------------
# Strategy Evaluators
# ---------------------------------------------------------------------------


def _evaluate_simple_ma(config: StrategyConfig, prices: list[float]) -> StrategySignal:
    """
    Simple Moving Average crossover strategy.
    BUY when short MA crosses above long MA.
    SELL when short MA crosses below long MA.
    """
    if len(prices) < config.long_window:
        return StrategySignal(
            should_trade=False, reason="Not enough price history for SMA"
        )

    short_ma = sum(prices[-config.short_window :]) / config.short_window
    long_ma = sum(prices[-config.long_window :]) / config.long_window

    # Previous crossover state (one tick ago)
    prev_prices = prices[:-1]
    if len(prev_prices) < config.long_window:
        return StrategySignal(
            should_trade=False, reason="Not enough history for previous tick"
        )

    prev_short = sum(prev_prices[-config.short_window :]) / config.short_window
    prev_long = sum(prev_prices[-config.long_window :]) / config.long_window

    current_price = prices[-1]

    # Bullish crossover: short MA crossed above long MA
    if prev_short <= prev_long and short_ma > long_ma:
        return StrategySignal(
            should_trade=True,
            side="BUY",
            price=round(current_price * 1.001, 2),  # Slightly above to fill
            quantity=round(config.order_quantity, 6),
            reason=f"SMA bullish crossover: short={short_ma:.0f} > long={long_ma:.0f}",
        )

    # Bearish crossover: short MA crossed below long MA
    if prev_short >= prev_long and short_ma < long_ma:
        return StrategySignal(
            should_trade=True,
            side="SELL",
            price=round(current_price * 0.999, 2),  # Slightly below to fill
            quantity=round(config.order_quantity, 6),
            reason=f"SMA bearish crossover: short={short_ma:.0f} < long={long_ma:.0f}",
        )

    return StrategySignal(should_trade=False, reason="No SMA crossover signal")


def _evaluate_mean_reversion(
    config: StrategyConfig, current_price: float, reference_price: float
) -> StrategySignal:
    """
    Mean Reversion strategy.
    BUY when current engine price is significantly BELOW reference (Binance INR).
    SELL when current engine price is significantly ABOVE reference.
    """
    if reference_price <= 0 or current_price <= 0:
        return StrategySignal(should_trade=False, reason="Invalid price data")

    deviation = (current_price - reference_price) / reference_price

    # Price is well below reference → expect reversion up → BUY
    if deviation < -config.deviation_pct:
        return StrategySignal(
            should_trade=True,
            side="BUY",
            price=round(current_price * 1.0005, 2),
            quantity=round(config.order_quantity, 6),
            reason=f"Mean reversion BUY: deviation={deviation:.4%}",
        )

    # Price is well above reference → expect reversion down → SELL
    if deviation > config.deviation_pct:
        return StrategySignal(
            should_trade=True,
            side="SELL",
            price=round(current_price * 0.9995, 2),
            quantity=round(config.order_quantity, 6),
            reason=f"Mean reversion SELL: deviation={deviation:.4%}",
        )

    return StrategySignal(
        should_trade=False, reason=f"Within reversion band: deviation={deviation:.4%}"
    )


def _evaluate_momentum(config: StrategyConfig, prices: list[float]) -> StrategySignal:
    """
    Momentum strategy.
    BUY if recent price movement exceeds positive threshold.
    SELL if recent price movement exceeds negative threshold.
    Looks at the last 2 ticks.
    """
    if len(prices) < 2:
        return StrategySignal(
            should_trade=False, reason="Not enough price history for momentum"
        )

    current = prices[-1]
    prev = prices[-2]
    change_pct = (current - prev) / prev if prev > 0 else 0

    if change_pct >= config.momentum_threshold:
        return StrategySignal(
            should_trade=True,
            side="BUY",
            price=round(current * 1.001, 2),
            quantity=round(config.order_quantity, 6),
            reason=f"Momentum BUY: +{change_pct:.3%}",
        )

    if change_pct <= -config.momentum_threshold:
        return StrategySignal(
            should_trade=True,
            side="SELL",
            price=round(current * 0.999, 2),
            quantity=round(config.order_quantity, 6),
            reason=f"Momentum SELL: {change_pct:.3%}",
        )

    return StrategySignal(
        should_trade=False, reason=f"Momentum below threshold: {change_pct:.3%}"
    )


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------


def evaluate_strategy(
    config: StrategyConfig,
    current_price: float,
    reference_price: float,
) -> StrategySignal:
    """
    Evaluate a strategy for a user and return a trade signal.

    Args:
        config: The user's strategy configuration.
        current_price: Latest engine-traded price in INR.
        reference_price: Current Binance INR reference price.

    Returns:
        StrategySignal indicating whether and how to trade.
    """
    prices = get_price_history()

    if config.strategy_type == StrategyType.SIMPLE_MA:
        return _evaluate_simple_ma(config, prices)

    elif config.strategy_type == StrategyType.MEAN_REVERSION:
        return _evaluate_mean_reversion(config, current_price, reference_price)

    elif config.strategy_type == StrategyType.MOMENTUM:
        return _evaluate_momentum(config, prices)

    return StrategySignal(
        should_trade=False, reason=f"Unknown strategy: {config.strategy_type}"
    )
