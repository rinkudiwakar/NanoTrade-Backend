# NanoTrade – Technical Requirement Document (Updated with Supabase)

## 1. System Overview

NanoTrade is a real-time crypto paper trading platform with:

* C++ Matching Engine (core execution)
* FastAPI backend (business logic)
* Supabase (Auth + Database + Storage)
* Redis (real-time pub/sub)
* Celery (background jobs)

---

## 2. Architecture

### 2.1 High-Level Flow

User → Frontend → Supabase Auth → FastAPI → C++ Engine → Supabase DB → Redis → WebSocket → Frontend

---

## 3. Core Components

---

### 3.1 Supabase (Critical Layer)

Supabase replaces:

* ❌ Custom auth system
* ❌ Local PostgreSQL setup

---

### Responsibilities:

#### ✅ Authentication

* Email/password login
* JWT tokens issued by Supabase
* FastAPI verifies token

---

#### ✅ Database (PostgreSQL)

Tables:

* users (managed by Supabase auth)
* profiles (custom user data)
* orders
* trades
* portfolios

---

#### ✅ Storage

Used for:

* Strategy files
* Logs (optional)
* Backtesting data

---

---

### 3.2 FastAPI Backend

Responsibilities:

* Verify Supabase JWT
* Route orders to engine
* Manage portfolio logic
* Store trades/orders in Supabase
* Publish updates to Redis

---

### 3.3 C++ Matching Engine

Responsibilities:

* Order matching
* Trade generation
* Order book maintenance

---

### 3.4 Redis

Responsibilities:

* Pub/Sub for:

  * trades
  * orderbook updates
* WebSocket broadcast layer

---

### 3.5 Celery Workers

Responsibilities:

* Market simulator
* Strategy execution
* Scheduled tasks

---

## 4. Authentication Flow

1. User logs in via Supabase (frontend)
2. Supabase returns JWT
3. Frontend sends JWT to FastAPI
4. FastAPI verifies token using Supabase public key
5. User authenticated

---

## 5. Data Flow

### 5.1 Order Execution

Frontend → FastAPI → Engine → Trades → Supabase DB → Redis → WebSocket → Frontend

---

### 5.2 Simulator

Celery → Generate order → Engine → Store → Broadcast

---

## 6. Database Schema (Supabase)

### profiles

* id (UUID, matches auth.users.id)
* balance
* created_at

---

### orders

* id
* user_id
* side
* price
* quantity
* status
* created_at

---

### trades

* id
* buyer_id
* seller_id
* price
* quantity
* timestamp

---

### portfolios

* user_id
* asset (BTC)
* quantity
* avg_price

---

## 7. Security

* Supabase JWT validation in FastAPI
* Row-level security (RLS) in Supabase
* API-level validation

---

## 8. Scaling

* Supabase handles DB scaling
* Redis handles real-time
* Celery handles async load

---

## 9. Deployment

* FastAPI (Docker)
* Redis (Docker)
* Celery worker
* Supabase (managed cloud)

---

## 10. Future Extensions

* Multi-asset trading
* Strategy marketplace
* AI-based traders


# FINAL ARCHITECTURE

Frontend
   ↓
Supabase Auth
   ↓
FastAPI (JWT verify)
   ↓
C++ Engine
   ↓
Supabase DB
   ↓
Redis Pub/Sub
   ↓
WebSocket
   ↓
Frontend


# make sure

Binance price → reference
our engine → actual price in frontend