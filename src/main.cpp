#include "engine/MatchingEngine.h"
#include "models/Order.h"

int main()
{
  MatchingEngine engine;

  engine.addOrder(Order(1, OrderType::BUY, 100.0, 10, 1));
  engine.addOrder(Order(2, OrderType::SELL, 99.0, 5, 2));
  engine.addOrder(Order(3, OrderType::SELL, 100.0, 10, 3));

  return 0;
}