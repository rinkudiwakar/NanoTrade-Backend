#include "engine/OrderBook.h"

void OrderBook::addOrder(const Order &order)
{
  if (order.type == OrderType::BUY)
  {
    buyBook[order.price].push(order);
  }
  else
  {
    sellBook[order.price].push(order);
  }
}

std::map<double, std::queue<Order>, std::greater<>> &OrderBook::getBuyBook()
{
  return buyBook;
}

std::map<double, std::queue<Order>> &OrderBook::getSellBook()
{
  return sellBook;
}