#include "engine/MatchingEngine.h"
#include <algorithm>
#include <ctime>

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
      int64_t tradeTimestamp = static_cast<int64_t>(std::time(nullptr));

      result.trades.emplace_back(
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
      int64_t tradeTimestamp = static_cast<int64_t>(std::time(nullptr));

      result.trades.emplace_back(
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
    result.fillStatus = "PARTIAL";
  }

  return result;
}

std::string MatchingEngine::getOrderBook() const
{
  std::lock_guard<std::mutex> lock(engineMutex);
  return orderBook.toJson().dump();
}

