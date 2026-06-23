# NanoTrade API Documentation

This document outlines the API endpoints available for the NanoTrade frontend integration. The backend is built using FastAPI and integrates with Supabase for authentication.

## 🚀 Base URLs
- **Local API:** `http://localhost:8000`
- **Public Tunnel:** `https://sheriff-barbie-engines-beverage.trycloudflare.com` *(Update this with your current active tunnel URL)*

---

## 🔒 Authentication (Supabase)
All protected endpoints require a Supabase JWT token passed in the Authorization header.
```http
Authorization: Bearer <SUPABASE_JWT_TOKEN>
```
*Note: The frontend should use the official `@supabase/supabase-js` client to handle user login/registration. Once logged in, extract the session token (`session.access_token`) and pass it to the NanoTrade backend.*

---

## 🟢 1. Health & Base Endpoints

### `GET /health`
Checks if the backend is alive and running.
- **Auth Required:** No
- **Response:**
  ```json
  {
      "status": "ok",
      "service": "NanoTrade"
  }
  ```

---

## 💼 2. Portfolio Management

### `GET /portfolio`
Fetches the logged-in user's portfolio balance and current holdings.
- **Auth Required:** Yes
- **Response:**
  ```json
  {
      "user_id": "841ebbb6-6bab-46f2-b71c-c23d0315a3d8",
      "balance": 10000000.0,
      "holdings": []
  }
  ```

---

## 📈 3. Order Management

### `POST /orders`
Places a new order (BUY/SELL) into the matching engine.
- **Auth Required:** Yes
- **Payload:**
  ```json
  {
      "symbol": "BTC_USDT",
      "side": "BUY",  // or "SELL"
      "type": "LIMIT", // or "MARKET"
      "quantity": 0.01,
      "price": 60000.0
  }
  ```
- **Response:**
  ```json
  {
      "order_id": "0c295e96-f2d1-4f46-b585-643a7faa04bf",
      "status": "QUEUED",
      "message": "Order queued for matching."
  }
  ```

### `GET /orders/history`
Fetches the user's past and pending orders.
- **Auth Required:** Yes
- **Response:** Array of user's orders.

---

## 📊 4. Market Data

### `GET /market/orderbook`
Fetches the current state of the order book for a symbol.
- **Auth Required:** No
- **Query Params:** `?symbol=BTC_USDT`

### `GET /market/price`
Fetches the current market price for a symbol.
- **Auth Required:** No
- **Query Params:** `?symbol=BTC_USDT`

### `GET /market/trades`
Fetches the recent public trades for a symbol.
- **Auth Required:** No
- **Query Params:** `?symbol=BTC_USDT`

---

## ⚡ 5. Real-Time WebSockets

### `WS /ws/market`
Connect to the WebSocket to receive real-time updates for prices, trades, and order book changes via Redis Pub/Sub.

- **Connection URL:** 
  - Local: `ws://localhost:8000/ws/market`
  - Public: `wss://sheriff-barbie-engines-beverage.trycloudflare.com/ws/market`
- **Auth Required:** You can connect anonymously to receive public market data. If you implement private order updates, you can pass the JWT token during the initial handshake.
- **Behavior:** The backend automatically broadcasts Redis events down to connected clients.
