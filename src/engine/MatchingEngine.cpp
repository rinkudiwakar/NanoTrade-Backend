#include "engine/MatchingEngine.h"
#include "utils/Logger.h"
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

// ─────────────────────────────────────────────────────────────────
// processOrder — core matching logic with full step logging
// ─────────────────────────────────────────────────────────────────
MatchingEngine::ProcessResult MatchingEngine::processOrder(const Order& order)
{
  std::lock_guard<std::mutex> lock(engineMutex);
  ProcessResult result;
  Order remainingOrder = order;

  LOG_INFO("MatchingEngine", "processOrder START | id=" + order.order_id
      + " side=" + order.typeToString()
      + " price=" + std::to_string(order.price)
      + " qty=" + std::to_string(order.quantity)
      + " user=" + order.user_id);

  if (remainingOrder.type == OrderType::BUY)
  {
    LOG_DEBUG("MatchingEngine", "Processing BUY order — scanning ask side");

    while (orderBook.hasAsks() && remainingOrder.quantity > 0)
    {
      auto bestAskOpt = orderBook.getBestAsk();
      if (!bestAskOpt)
      {
        LOG_DEBUG("MatchingEngine", "No best ask found, stopping match loop");
        break;
      }

      Order bestAsk = *bestAskOpt;

      if (bestAsk.price > remainingOrder.price)
      {
        LOG_DEBUG("MatchingEngine", "Best ask price " + std::to_string(bestAsk.price)
            + " > bid price " + std::to_string(remainingOrder.price) + " — no match");
        break;
      }

      int tradedQty       = std::min(remainingOrder.quantity, bestAsk.quantity);
      int64_t tradeTs     = currentTimestampMs();
      lastTradedPrice     = bestAsk.price;
      std::string tradeId = generateUuid();

      LOG_INFO("MatchingEngine", "TRADE MATCHED | trade_id=" + tradeId
          + " price=" + std::to_string(bestAsk.price)
          + " qty=" + std::to_string(tradedQty)
          + " buyer=" + remainingOrder.user_id
          + " seller=" + bestAsk.user_id);

      result.trades.emplace_back(
          tradeId,
          remainingOrder.order_id,
          bestAsk.order_id,
          bestAsk.price,
          tradedQty,
          tradeTs,
          remainingOrder.user_id,
          bestAsk.user_id);

      remainingOrder.quantity -= tradedQty;
      int updatedAskQty = bestAsk.quantity - tradedQty;

      if (updatedAskQty <= 0)
      {
        LOG_DEBUG("MatchingEngine", "Ask order fully consumed, removing from book");
        orderBook.removeBestAsk();
      }
      else
      {
        LOG_DEBUG("MatchingEngine", "Ask order partially consumed, remaining qty=" + std::to_string(updatedAskQty));
        orderBook.updateBestAsk(updatedAskQty);
      }
    }

    if (remainingOrder.quantity > 0)
    {
      LOG_DEBUG("MatchingEngine", "BUY order partially/unfilled — adding to bid book, qty=" + std::to_string(remainingOrder.quantity));
      orderBook.addBid(remainingOrder);
      result.remainingOrder = remainingOrder;
    }
  }
  else
  {
    LOG_DEBUG("MatchingEngine", "Processing SELL order — scanning bid side");

    while (orderBook.hasBids() && remainingOrder.quantity > 0)
    {
      auto bestBidOpt = orderBook.getBestBid();
      if (!bestBidOpt)
      {
        LOG_DEBUG("MatchingEngine", "No best bid found, stopping match loop");
        break;
      }

      Order bestBid = *bestBidOpt;

      if (bestBid.price < remainingOrder.price)
      {
        LOG_DEBUG("MatchingEngine", "Best bid price " + std::to_string(bestBid.price)
            + " < ask price " + std::to_string(remainingOrder.price) + " — no match");
        break;
      }

      int tradedQty       = std::min(remainingOrder.quantity, bestBid.quantity);
      int64_t tradeTs     = currentTimestampMs();
      lastTradedPrice     = bestBid.price;
      std::string tradeId = generateUuid();

      LOG_INFO("MatchingEngine", "TRADE MATCHED | trade_id=" + tradeId
          + " price=" + std::to_string(bestBid.price)
          + " qty=" + std::to_string(tradedQty)
          + " buyer=" + bestBid.user_id
          + " seller=" + remainingOrder.user_id);

      result.trades.emplace_back(
          tradeId,
          bestBid.order_id,
          remainingOrder.order_id,
          bestBid.price,
          tradedQty,
          tradeTs,
          bestBid.user_id,
          remainingOrder.user_id);

      remainingOrder.quantity -= tradedQty;
      int updatedBidQty = bestBid.quantity - tradedQty;

      if (updatedBidQty <= 0)
      {
        LOG_DEBUG("MatchingEngine", "Bid order fully consumed, removing from book");
        orderBook.removeBestBid();
      }
      else
      {
        LOG_DEBUG("MatchingEngine", "Bid order partially consumed, remaining qty=" + std::to_string(updatedBidQty));
        orderBook.updateBestBid(updatedBidQty);
      }
    }

    if (remainingOrder.quantity > 0)
    {
      LOG_DEBUG("MatchingEngine", "SELL order partially/unfilled — adding to ask book, qty=" + std::to_string(remainingOrder.quantity));
      orderBook.addAsk(remainingOrder);
      result.remainingOrder = remainingOrder;
    }
  }

  // Populate result metadata
  result.remainingQuantity = remainingOrder.quantity;
  if (remainingOrder.quantity == 0)
    result.fillStatus = "FILLED";
  else if (remainingOrder.quantity == order.quantity)
    result.fillStatus = "NEW";
  else
    result.fillStatus = "PARTIALLY_FILLED";

  LOG_INFO("MatchingEngine", "processOrder END | id=" + order.order_id
      + " status=" + result.fillStatus
      + " trades=" + std::to_string(result.trades.size())
      + " remaining_qty=" + std::to_string(result.remainingQuantity)
      + " last_price=" + std::to_string(lastTradedPrice));

  return result;
}

// ─────────────────────────────────────────────────────────────────
// getOrderBook
// ─────────────────────────────────────────────────────────────────
std::string MatchingEngine::getOrderBook() const
{
  std::lock_guard<std::mutex> lock(engineMutex);
  LOG_DEBUG("MatchingEngine", "getOrderBook called");
  return orderBook.toJson().dump();
}

// ─────────────────────────────────────────────────────────────────
// getLastTradedPrice
// ─────────────────────────────────────────────────────────────────
double MatchingEngine::getLastTradedPrice() const
{
  std::lock_guard<std::mutex> lock(engineMutex);
  return lastTradedPrice;
}
