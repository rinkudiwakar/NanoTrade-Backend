#pragma once

#include "models/Order.h"
#include <map>
#include <queue>
#include "compat/optional.h"

class OrderBook
{
private:
  // Buy orders → highest price first
  std::map<double, std::queue<Order>, std::greater<double>> bids;

  // Sell orders → lowest price first
  std::map<double, std::queue<Order>> asks;

public:
  // Add orders
  void addBid(const Order &order);
  void addAsk(const Order &order);

  // Get best orders
  compat::optional<Order> getBestBid() const;
  compat::optional<Order> getBestAsk() const;

  // Remove best order (after fully filled)
  void removeBestBid();
  void removeBestAsk();

  // Update top order after partial fill
  void updateBestBid(int newQuantity);
  void updateBestAsk(int newQuantity);

  // Check if book is empty
  bool hasBids() const;
  bool hasAsks() const;

  // Debug helper
  void print() const;
};