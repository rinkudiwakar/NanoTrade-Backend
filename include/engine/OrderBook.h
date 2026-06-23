#pragma once

#include <map>
#include <queue>
#include <functional>
#include "models/Order.h"

class OrderBook
{
private:
  // BUY: highest price first
  std::map<double, std::queue<Order>, std::greater<>> buyBook;

  // SELL: lowest price first
  std::map<double, std::queue<Order>> sellBook;

public:
  void addOrder(const Order &order);

  std::map<double, std::queue<Order>, std::greater<>> &getBuyBook();
  std::map<double, std::queue<Order>> &getSellBook();
};