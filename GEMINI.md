# Gemini.md — NanoTrade System Instructions

## 1. Project Overview

NanoTrade is a real-time crypto paper trading platform built with:

* C++ Matching Engine (core execution)
* Python FastAPI (backend logic)
* Supabase (Auth + Database + Storage)
* Redis (real-time pub/sub)
* Celery (background workers)
* Binance (public WebSocket for price reference)

The system simulates a live crypto exchange with synthetic liquidity and real-time user trading.

---

## 2. Core Architecture Rules (MANDATORY)

### Rule 1: Engine is Source of Truth

* All trades and price discovery MUST come from the C++ matching engine
* Binance data is ONLY a reference (anchor), NOT the final price

---

### Rule 2: No Direct DB Access from Engine

* C++ engine MUST NOT interact with database
* All persistence handled via FastAPI layer

---

### Rule 3: Supabase Handles Auth

* DO NOT implement custom authentication
* Use Supabase JWT
* FastAPI only verifies tokens

---

### Rule 4: Redis for Real-Time

* DO NOT use Supabase realtime for trading updates
* Use Redis Pub/Sub + WebSocket

---

### Rule 5: Separation of Concerns

| Layer    | Responsibility      |
| -------- | ------------------- |
| C++      | Matching, OrderBook |
| FastAPI  | Business Logic      |
| Supabase | Auth + Storage      |
| Redis    | Realtime            |
| Celery   | Async jobs          |

---

## 3. Current Codebase Understanding

Existing Structure:

* include/ → C++ headers
* src/ → C++ implementation
* bindings.cpp → Python binding
* python/fastapi_server.py → initial API

---

### Important Notes:

* Engine already exists and should NOT be rewritten
* Modify only to add metadata + return results
* Maintain performance and structure

---

## 4. Required C++ Changes (MANDATORY)

### 4.1 Order Struct MUST include:

* user_id
* is_user
* timestamp

---

### 4.2 Trade Struct MUST include:

* buyer_id
* seller_id

---

### 4.3 Engine MUST return:

* trades (vector)
* remaining quantity
* fill status

---

### 4.4 Thread Safety

* Use mutex for processOrder

---

### 4.5 Provide API:

* processOrder()
* getOrderBook()

---

## 5. Backend Responsibilities

### FastAPI MUST:

* Verify Supabase JWT
* Accept user orders
* Call C++ engine
* Store results in Supabase
* Publish events via Redis
* Serve WebSocket updates

---

### Celery MUST:

* Run simulator loop
* Run strategy engine

---

## 6. Market Data (IMPORTANT)

### Binance Usage:

* Use public WebSocket ONLY
* No API key required

Endpoint:
wss://stream.binance.com:9443/ws/btcusdt@trade

---

### Rules:

* Binance price = reference price
* Engine price = actual price shown

---

## 7. Simulator Rules

* Generates synthetic orders
* Must NOT directly change price
* Must feed orders into engine

---

## 8. Database Design (Supabase)

Tables:

* profiles
* orders
* trades
* portfolios

---

## 9. Common Mistakes to AVOID

### ❌ Mistake 1:

Using Binance price as actual trading price
→ WRONG: breaks simulation

---

### ❌ Mistake 2:

Skipping engine and directly updating DB
→ WRONG: breaks system integrity

---

### ❌ Mistake 3:

Using Supabase realtime for trading
→ WRONG: high latency

---

### ❌ Mistake 4:

Mixing simulator logic inside API routes
→ WRONG: must be in Celery

---

## 10. Known Faults (From Previous Iterations)

### Fault 1:

Initially treated API price as main price
→ FIXED: now only reference price

---

### Fault 2:

Missing ownership in trades (no buyer/seller)
→ FIXED: required in Trade struct

---

### Fault 3:

No separation between engine and DB
→ FIXED: FastAPI layer introduced

---

### Fault 4:

No background system for simulator
→ FIXED: Celery added

---

## 11. User-Suggested Changes (MANDATORY TO FOLLOW)

* Use Supabase instead of local PostgreSQL
* Use Supabase Auth instead of custom auth
* Use Redis for real-time updates
* Use Binance WebSocket (no API key)
* Build backend FIRST, then frontend
* Maintain existing C++ structure

---

## 12. Frontend Expectations (IMPORTANT FOR BACKEND DESIGN)

Frontend will:

* Use Supabase for login
* Call FastAPI with JWT
* Connect to WebSocket for real-time updates

Required APIs:

* POST /orders
* GET /portfolio
* GET /market/orderbook

WebSocket:

* /ws/market

---

## 13. Development Order (STRICT)

1. Engine update (C++)
2. FastAPI structure
3. Supabase integration
4. Order API
5. Portfolio logic
6. Redis + WebSocket
7. Celery simulator
8. Strategy engine

---

## 14. Coding Standards

* Keep engine optimized (no unnecessary abstraction)
* Use async in FastAPI
* Maintain modular structure
* Avoid tight coupling

---

## 15. Final Goal

System should behave like:

* Real exchange simulation
* Real-time updates
* Multi-user trading
* Strategy testing environment

---

## 16. Instruction for Future Iterations

* If any design change occurs, update this file
* Always document faults and fixes
* Never bypass architecture rules


## 17. PRICE SYSTEM DESIGN (CRITICAL – MUST FOLLOW)

### 17.1 Binance Price Usage Rule

* Binance price MUST NOT be used as the actual trading price.
* It is ONLY used as a reference (anchor) for simulation.

---

### 17.2 Price Flow

Correct flow:

Binance (USD) → Currency Conversion → Reference Price (INR) → Simulator → Engine → Final Market Price

---

### 17.3 Currency Conversion (MANDATORY)

Requirement:

* Convert USD → INR in real-time
* Use reliable exchange rate source (API or cached rate)

---

### 17.4 Implementation Requirement

Backend must maintain:

* current_usd_price (from Binance)
* usd_inr_rate (from FX source)
* reference_price_inr = usd_price × usd_inr_rate

---

### 17.5 Update Frequency

* Binance price: real-time (WebSocket)
* USD-INR rate: every 5–10 seconds (NOT per tick)

---

### 17.6 Simulator Rule

* Simulator MUST generate orders around reference_price_inr
* Must maintain spread:

  BUY < reference_price < SELL

---

### 17.7 Engine Rule

* Engine determines final price via trades
* Engine price may deviate from reference price (allowed)

---

### 17.8 Frontend Rule

* All prices displayed MUST be in INR
* NEVER show USD to end user

---

### 17.9 Precision Rules

* Price: 2 decimal places (₹)
* Quantity: up to 6 decimals (BTC)

---

### 17.10 Fault Prevention

DO NOT:

* Use Binance price directly in UI
* Convert currency inside frontend
* Fetch exchange rate per request

---

### 17.11 Caching Strategy

* Store USD-INR rate in Redis
* Update periodically via Celery task

---

### 17.12 Example

If:

BTC = 67,000 USD
USD-INR = 83

Then:

Reference Price = ₹55,61,000

Simulator generates orders around this value.
