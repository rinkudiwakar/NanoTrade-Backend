# NanoTrade — Real-Time Crypto Paper Trading Platform

> **Backend Repository**  
> This repository contains the backend, matching engine, market simulation, database integration, and real-time infrastructure for NanoTrade.
>
> **Frontend:** [View NanoTrade Frontend Repository →](https://github.com/rinkudiwakar/NanoTrade)

NanoTrade is a **high-performance crypto paper trading platform** that simulates a real exchange environment using a custom-built **C++ matching engine**, real-time price anchoring, and intelligent market simulation.

> Practice trading, test strategies, and understand market behavior — without risking real money.

---

## 🧠 Key Highlights

- ⚡ **C++ Matching Engine** (Low-latency, price-time priority)
- 🔄 **Real-Time Trading System** (WebSocket updates)
- 🤖 **Market Simulator** (Bots + liquidity generation)
- 💰 **Paper Trading with Virtual INR Balance**
- 📊 **Order Book + Trade Execution**
- 🧪 **Strategy-ready architecture**
- 🇮🇳 **INR-based pricing (India-focused)**

---

## 🏗️ Architecture

```text
                    NanoTrade
                        │
             ┌──────────┴──────────┐
             │                     │
        React Frontend         FastAPI Backend
             │                     │
             │              C++ Matching Engine
             │                  (pybind11)
             │                     │
             │              ┌──────┴──────┐
             │              │             │
             │          Supabase        Redis
             │          Auth + DB    Pub/Sub + Realtime
             │                            │
             │                         Celery
             │                    Background Jobs
             │
             └──── WebSocket / REST ─────┘


```
## 💡 How It Works

### 🔹 Price System

* Real-time price fetched from Binance (USD)
* Converted to INR using live FX rate
* Used as a **reference price only**
* Final price is determined by the **matching engine**

---

### 🔹 Trading Flow

1. User places order (BUY/SELL)
2. Order sent to C++ matching engine
3. Engine matches against order book
4. Trades generated
5. Portfolio updated
6. Updates broadcast via WebSocket

---

### 🔹 Market Simulation

* Synthetic traders generate liquidity
* Orders placed around reference price
* Includes:

  * Random traders
  * Whale behavior
  * Price clustering

---

## 🧰 Tech Stack

| Layer      | Tech                  |
| ---------- | --------------------- |
| Engine     | C++                   |
| Backend    | FastAPI (Python)      |
| Database   | Supabase (PostgreSQL) |
| Realtime   | Redis + WebSocket     |
| Workers    | Celery                |
| Price Feed | Binance WebSocket     |

---

## 📦 Features

* ✅ Limit order trading
* ✅ Real-time order book
* ✅ Trade execution engine
* ✅ Portfolio tracking
* ✅ PnL calculation
* ✅ Multi-user support
* 🔜 Strategy engine
* 🔜 Leaderboard & gamification

---

## 🗄️ Database Design

* `profiles` → user balance
* `orders` → placed orders
* `trades` → executed trades
* `portfolios` → asset holdings

---

## 🔐 Authentication

* Powered by Supabase Auth
* JWT-based authentication
* Row-Level Security (RLS) enabled

---

## ⚙️ Setup Instructions

### 1. Clone Repository
## For Backend

```bash
git clone https://github.com/rinkudiwakar/NanoTrade-Backend.git
cd nanotrade-backend
```
## For Frontend

```bash
git clone https://github.com/rinkudiwakar/NanoTrade.git
cd nanotrade
```

---

### 2. Configure Environment

Copy the example environment file and fill in your Supabase credentials:

```bash
cp .env.example .env
```
*(Update `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_JWT_SECRET` in `.env`)*

---

### 3. Run with Docker (Recommended)

NanoTrade is fully containerized. You can launch the entire stack (API, Engine, Redis, Celery) with one command:

```bash
docker-compose up --build
```
*The API will be available at `http://localhost:8000`*

---

## 🧪 Testing

* API testing via Postman / curl (See `API_DOCS.md`)
* Run automated backend integration tests:
  ```bash
  python test_public_api.py
  ```
* Simulator testing via background Celery tasks


---

## 🚀 Future Roadmap

* 📈 Strategy execution engine
* 📊 Advanced analytics (PnL charts)
* 🧠 AI-based trading agents
* 🎮 Leaderboard & competitions
* 🌐 Multi-asset support (ETH, SOL, etc.)

---

## ⚠️ Important Notes

* Binance price is used only as a reference
* Final trading price is determined by the matching engine
* All values are shown in INR

---

## 🤝 Contribution

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## 📜 License

MIT License

---

## 💡 Inspiration

Built to simulate real-world trading systems and explore market microstructure, system design, and real-time backend engineering.
