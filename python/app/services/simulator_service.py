"""
app/services/simulator_service.py

Market Simulator Service.
Extracted from workers/tasks.py to provide a clean, testable, reusable
module for all simulator-related logic.

Architecture rules:
- Simulator MUST NOT write directly to DB — it submits orders to the engine via FastAPI.
- Simulator generates orders around the Binance reference price (INR).
- BUY orders < reference price, SELL orders > reference price (spread maintained).
- All prices in INR, all quantities in BTC (6 decimal precision).
"""

import random
from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# Trader Personality Types  (PRD Section 3.3)
# ---------------------------------------------------------------------------


@dataclass
class SimulatorOrder:
    """Represents a single order to be submitted by the simulator."""

    side: str  # "BUY" or "SELL"
    price: float  # INR, 2 decimal precision
    quantity: float  # BTC, 6 decimal precision


def _noise_order(reference_price: float) -> List[SimulatorOrder]:
    """
    Noise trader: random direction, small spread, small quantity.
    Represents retail participants with no specific strategy.
    """
    spread = random.uniform(0.0002, 0.002)  # 0.02% – 0.2%
    side = random.choice(["BUY", "SELL"])
    quantity = round(random.uniform(0.001, 0.02), 6)

    if side == "BUY":
        price = round(reference_price * (1 - spread), 2)
    else:
        price = round(reference_price * (1 + spread), 2)

    return [SimulatorOrder(side=side, price=price, quantity=quantity)]


def _momentum_order(reference_price: float) -> List[SimulatorOrder]:
    """
    Momentum trader: chases recent direction with slightly tighter spread
    and larger size. 50/50 split between buy-side and sell-side momentum.
    """
    spread = random.uniform(0.0001, 0.001)
    side = random.choice(["BUY", "SELL"])
    quantity = round(random.uniform(0.01, 0.1), 6)

    if side == "BUY":
        price = round(reference_price * (1 - spread), 2)
    else:
        price = round(reference_price * (1 + spread), 2)

    return [SimulatorOrder(side=side, price=price, quantity=quantity)]


def _mean_reversion_order(reference_price: float) -> List[SimulatorOrder]:
    """
    Mean reversion trader: places orders slightly inside the spread,
    betting price will snap back to reference.
    """
    spread = random.uniform(0.0005, 0.003)
    side = random.choice(["BUY", "SELL"])
    quantity = round(random.uniform(0.005, 0.05), 6)

    # Mean reversion places orders closer to reference than momentum traders
    if side == "BUY":
        price = round(reference_price * (1 - spread * 0.5), 2)
    else:
        price = round(reference_price * (1 + spread * 0.5), 2)

    return [SimulatorOrder(side=side, price=price, quantity=quantity)]


def _whale_order(reference_price: float) -> List[SimulatorOrder]:
    """
    Whale trader: large size, larger spread impact. Rare — 5% probability.
    Can cause significant price movement within the engine.
    """
    spread = random.uniform(0.005, 0.015)  # 0.5% – 1.5%
    side = random.choice(["BUY", "SELL"])
    quantity = round(random.uniform(1.5, 5.0), 6)

    if side == "BUY":
        price = round(reference_price * (1 - spread), 2)
    else:
        price = round(reference_price * (1 + spread), 2)

    return [SimulatorOrder(side=side, price=price, quantity=quantity)]


def _cluster_orders(reference_price: float) -> List[SimulatorOrder]:
    """
    Cluster: 2–4 orders placed in layers at slightly different price levels,
    representing market-making or iceberg-style activity.
    """
    cluster_size = random.randint(2, 4)
    side = random.choice(["BUY", "SELL"])
    base_spread = random.uniform(0.0002, 0.003)
    base_quantity = round(random.uniform(0.005, 0.05), 6)
    orders = []

    for i in range(cluster_size):
        layer_spread = base_spread + (i * 0.0005)
        qty_var = round(base_quantity / cluster_size * random.uniform(0.8, 1.2), 6)

        if side == "BUY":
            price = round(reference_price * (1 - layer_spread), 2)
        else:
            price = round(reference_price * (1 + layer_spread), 2)

        orders.append(SimulatorOrder(side=side, price=price, quantity=qty_var))

    return orders


# ---------------------------------------------------------------------------
# Main entry point: generate_simulator_orders()
# ---------------------------------------------------------------------------


def generate_simulator_orders(reference_price: float) -> List[SimulatorOrder]:
    """
    Generates one batch of synthetic orders for the current tick.

    Trader type probabilities:
    - Noise trader:         40%
    - Momentum trader:      25%
    - Mean reversion:       15%
    - Cluster:              15%
    - Whale:                5%

    Args:
        reference_price: Current BTC reference price in INR (from Redis).

    Returns:
        A list of SimulatorOrder objects to submit to the engine.
    """
    if reference_price <= 0:
        raise ValueError(f"Invalid reference price: {reference_price}")

    roll = random.random()

    if roll < 0.40:
        return _noise_order(reference_price)
    elif roll < 0.65:
        return _momentum_order(reference_price)
    elif roll < 0.80:
        return _mean_reversion_order(reference_price)
    elif roll < 0.95:
        return _cluster_orders(reference_price)
    else:
        return _whale_order(reference_price)
