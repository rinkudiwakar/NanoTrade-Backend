#pragma once

#include <cstdint>

enum class OrderType
{
  BUY,
  SELL
};

struct Order
{
  int order_id;
  OrderType type;
  double price;
  int quantity;
  int64_t timestamp;

  Order(int id, OrderType t, double p, int q, int64_t ts)
      : order_id(id), type(t), price(p), quantity(q), timestamp(ts) {}
};