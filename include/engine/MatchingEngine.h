#pragma once

#include "engine/OrderBook.h"
#include "models/Order.h"

class MatchingEngine
{
private:
  OrderBook orderBook;

  void matchOrders();

public:
  void addOrder(const Order &order);
};