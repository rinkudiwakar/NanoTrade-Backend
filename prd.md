# NanoTrade – Crypto Paper Trading Platform (PRD)

## 1. Overview

NanoTrade is a real-time crypto paper trading platform that allows users to practice trading using virtual funds. The system simulates a live market using a hybrid approach:

* Real-time price anchoring (via Binance)
* Synthetic liquidity (simulator bots)
* Custom matching engine (C++)

Users can trade, test strategies, and analyze performance without financial risk.

---

## 2. Goals

* Provide realistic trading experience
* Enable learning and experimentation
* Simulate real market microstructure
* Support both manual and automated trading

---

## 3. Core Features

### 3.1 User System

* User registration & login
* JWT-based authentication
* Initial virtual balance (e.g., 100,000 USDT)

---

### 3.2 Trading System

* Place Buy/Sell orders
* Limit orders (Phase 1)
* Market orders (Phase 2)
* Order matching via C++ engine

---

### 3.3 Market Simulation

* Bot-generated liquidity
* Multiple trader types:

  * Momentum traders
  * Mean reversion traders
  * Whale traders
  * Noise traders

---

### 3.4 Portfolio System

* Balance tracking
* Asset holdings
* Average price calculation
* Real-time PnL

---

### 3.5 Real-Time System

* Live order book
* Live trades feed
* WebSocket updates

---

### 3.6 Strategy Engine (Phase 2)

* Rule-based strategies
* Auto execution
* Backtesting (future)

---

### 3.7 Gamification (Phase 3)

* Leaderboards
* Daily competitions
* Performance ranking

---

## 4. User Flow

1. User registers
2. Receives virtual balance
3. Views market dashboard
4. Places trade
5. Trade matched via engine
6. Portfolio updated
7. Real-time UI reflects changes

---

## 5. Non-Goals (MVP)

* No real money trading
* No regulatory compliance needed
* No advanced derivatives (futures/options)

---

## 6. Success Metrics

* Active users
* Trades executed per session
* Strategy usage
* User retention
