#include "engine/OrderBook.h"
#include <iostream>

void OrderBook::addBid(const Order &order)
{
  bids[order.price].push(order);
}

void OrderBook::addAsk(const Order &order)
{
  asks[order.price].push(order);
}

compat::optional<Order> OrderBook::getBestBid() const
{
  if (bids.empty())
    return compat::nullopt;
  return bids.begin()->second.front();
}

compat::optional<Order> OrderBook::getBestAsk() const
{
  if (asks.empty())
    return compat::nullopt;
  return asks.begin()->second.front();
}

void OrderBook::removeBestBid()
{
  if (bids.empty())
    return;

  auto it = bids.begin();
  it->second.pop();

  if (it->second.empty())
  {
    bids.erase(it);
  }
}

void OrderBook::removeBestAsk()
{
  if (asks.empty())
    return;

  auto it = asks.begin();
  it->second.pop();

  if (it->second.empty())
  {
    asks.erase(it);
  }
}

void OrderBook::updateBestBid(int newQuantity)
{
  if (bids.empty())
    return;

  auto &order = bids.begin()->second.front();
  order.quantity = newQuantity;
}

void OrderBook::updateBestAsk(int newQuantity)
{
  if (asks.empty())
    return;

  auto &order = asks.begin()->second.front();
  order.quantity = newQuantity;
}

bool OrderBook::hasBids() const
{
  return !bids.empty();
}

bool OrderBook::hasAsks() const
{
  return !asks.empty();
}

void OrderBook::print() const
{
  std::cout << "\n--- ORDER BOOK ---\n";

  std::cout << "BIDS:\n";
  for (const auto &entry : bids)
  {
    const auto &price = entry.first;
    const auto &queue = entry.second;
    std::cout << price << " -> " << queue.size() << " orders\n";
  }

  std::cout << "ASKS:\n";
  for (const auto &entry : asks)
  {
    const auto &price = entry.first;
    const auto &queue = entry.second;
    std::cout << price << " -> " << queue.size() << " orders\n";
  }

  std::cout << "-------------------\n";
}

nlohmann::json OrderBook::toJson() const
{
  nlohmann::json result = {
      {"bids", nlohmann::json::array()},
      {"asks", nlohmann::json::array()}};

  for (const auto &entry : bids)
  {
    double price = entry.first;
    int totalQuantity = 0;
    std::queue<Order> q = entry.second;
    while (!q.empty())
    {
      totalQuantity += q.front().quantity;
      q.pop();
    }
    result["bids"].push_back({{"price", price}, {"quantity", totalQuantity}});
  }

  for (const auto &entry : asks)
  {
    double price = entry.first;
    int totalQuantity = 0;
    std::queue<Order> q = entry.second;
    while (!q.empty())
    {
      totalQuantity += q.front().quantity;
      q.pop();
    }
    result["asks"].push_back({{"price", price}, {"quantity", totalQuantity}});
  }

  return result;
}