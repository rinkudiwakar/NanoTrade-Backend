#include "engine/MatchingEngine.h"
#include <algorithm>
#include <chrono>
#include <random>
#include <sstream>
#include <iomanip>

static std::string generateUuid()
{
  static std::random_device rd;
  static std::mt19937 gen(rd());
  static std::uniform_int_distribution<> dis(0, 15);
  static std::uniform_int_distribution<> dis2(8, 11);

  std::stringstream ss;
  ss << std::hex;
  for (int i = 0; i < 8; i++) ss << dis(gen);
  ss << "-";
  for (int i = 0; i < 4; i++) ss << dis(gen);
  ss << "-4";
  for (int i = 0; i < 3; i++) ss << dis(gen);
  ss << "-";
  ss << dis2(gen);
  for (int i = 0; i < 3; i++) ss << dis(gen);
  ss << "-";
  for (int i = 0; i < 12; i++) ss << dis(gen);
  return ss.str();
}

static int64_t currentTimestampMs()
{
  return std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::system_clock::now().time_since_epoch()
  ).count();
}

MatchingEngine::ProcessResult MatchingEngine::processOrder(const Order &order)
{
  std::lock_guard<std::mutex> lock(engineMutex);
  ProcessResult result;
  Order remainingOrder = order;

  if (remainingOrder.type == OrderType::BUY)
  {
    while (orderBook.hasAsks() && remainingOrder.quantity > 0)
    {
      auto bestAskOpt = orderBook.getBestAsk();
      if (!bestAskOpt)
        break;

      Order bestAsk = *bestAskOpt;
      if (bestAsk.price > remainingOrder.price)
        break;

      int tradedQty = std::min(remainingOrder.quantity, bestAsk.quantity);
      int64_t tradeTimestamp = currentTimestampMs();
      lastTradedPrice = bestAsk.price;

      result.trades.emplace_back(
          generateUuid(),
          remainingOrder.order_id,
          bestAsk.order_id,
          bestAsk.price,
          tradedQty,
          tradeTimestamp,
          remainingOrder.user_id,
          bestAsk.user_id);

      remainingOrder.quantity -= tradedQty;
      int updatedAskQty = bestAsk.quantity - tradedQty;

      if (updatedAskQty <= 0)
      {
        orderBook.removeBestAsk();
      }
      else
      {
        orderBook.updateBestAsk(updatedAskQty);
      }
    }

    if (remainingOrder.quantity > 0)
    {
      orderBook.addBid(remainingOrder);
      result.remainingOrder = remainingOrder;
    }
  }
  else
  {
    while (orderBook.hasBids() && remainingOrder.quantity > 0)
    {
      auto bestBidOpt = orderBook.getBestBid();
      if (!bestBidOpt)
        break;

      Order bestBid = *bestBidOpt;
      if (bestBid.price < remainingOrder.price)
        break;

      int tradedQty = std::min(remainingOrder.quantity, bestBid.quantity);
      int64_t tradeTimestamp = currentTimestampMs();
      lastTradedPrice = bestBid.price;

      result.trades.emplace_back(
          generateUuid(),
          bestBid.order_id,
          remainingOrder.order_id,
          bestBid.price,
          tradedQty,
          tradeTimestamp,
          bestBid.user_id,
          remainingOrder.user_id);

      remainingOrder.quantity -= tradedQty;
      int updatedBidQty = bestBid.quantity - tradedQty;

      if (updatedBidQty <= 0)
      {
        orderBook.removeBestBid();
      }
      else
      {
        orderBook.updateBestBid(updatedBidQty);
      }
    }

    if (remainingOrder.quantity > 0)
    {
      orderBook.addAsk(remainingOrder);
      result.remainingOrder = remainingOrder;
    }
  }

  // Populate metadata fields
  result.remainingQuantity = remainingOrder.quantity;
  if (remainingOrder.quantity == 0)
  {
    result.fillStatus = "FILLED";
  }
  else if (remainingOrder.quantity == order.quantity)
  {
    result.fillStatus = "NEW";
  }
  else
  {
    result.fillStatus = "PARTIALLY_FILLED";
  }

  return result;
}

std::string MatchingEngine::getOrderBook() const
{
  std::lock_guard<std::mutex> lock(engineMutex);
  return orderBook.toJson().dump();
}

double MatchingEngine::getLastTradedPrice() const
{
  std::lock_guard<std::mutex> lock(engineMutex);
  return lastTradedPrice;
}


