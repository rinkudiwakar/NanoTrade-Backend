#include <iostream>
#include "engine/MatchingEngine.h"

void MatchingEngine::addOrder(const Order &order)
{
  orderBook.addOrder(order);
  matchOrders();
}

void MatchingEngine::matchOrders()
{
  auto &buyBook = orderBook.getBuyBook();
  auto &sellBook = orderBook.getSellBook();

  while (!buyBook.empty() && !sellBook.empty())
  {
    auto bestBuy = buyBook.begin();
    auto bestSell = sellBook.begin();

    if (bestBuy->first >= bestSell->first)
    {
      Order &buyOrder = bestBuy->second.front();
      Order &sellOrder = bestSell->second.front();

      int tradedQty = std::min(buyOrder.quantity, sellOrder.quantity);

      std::cout << "TRADE: "
                << tradedQty << " @ " << bestSell->first << std::endl;

      buyOrder.quantity -= tradedQty;
      sellOrder.quantity -= tradedQty;

      if (buyOrder.quantity == 0)
        bestBuy->second.pop();

      if (sellOrder.quantity == 0)
        bestSell->second.pop();

      if (bestBuy->second.empty())
        buyBook.erase(bestBuy);

      if (bestSell->second.empty())
        sellBook.erase(bestSell);
    }
    else
    {
      break;
    }
  }
}