#pragma once

#include "engine/OrderBook.h"
#include "models/Order.h"
#include "models/Trade.h"
#include "compat/optional.h"
#include <vector>
#include <mutex>
#include <string>

class MatchingEngine
{
public:
  struct ProcessResult
  {
    std::vector<Trade> trades;
    compat::optional<Order> remainingOrder;
    int remainingQuantity;
    std::string fillStatus;
  };

private:
  OrderBook orderBook;
  mutable std::mutex engineMutex;
  double lastTradedPrice;

public:
  MatchingEngine() : lastTradedPrice(0.0) {}

  // Process one order and return trades plus remaining order if not filled
  ProcessResult processOrder(const Order &order);

  // Return the JSON serialized order book
  std::string getOrderBook() const;

  // Get the last traded price
  double getLastTradedPrice() const;
};