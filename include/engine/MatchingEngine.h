#pragma once

#include "engine/OrderBook.h"
#include "models/Order.h"
#include "models/Trade.h"
#include "compat/optional.h"
#include <vector>

class MatchingEngine
{
public:
  struct ProcessResult
  {
    std::vector<Trade> trades;
    compat::optional<Order> remainingOrder;
  };

private:
  OrderBook orderBook;

public:
  // Process one order and return trades plus remaining order if not filled
  ProcessResult processOrder(const Order &order);
};