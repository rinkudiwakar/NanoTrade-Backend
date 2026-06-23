#include "engine/MatchingEngine.h"
#include "models/Order.h"
#include "models/Trade.h"
#include <nlohmann/json.hpp>
#include <iostream>
#include <vector>
#include <ctime>

using namespace std;

int main()
{
  MatchingEngine engine;

  // Prepare a sequence of orders to exercise matching and partial fills
  vector<Order> orders;
  orders.emplace_back("order_1", OrderType::BUY, 100.0, 10, static_cast<int64_t>(time(nullptr)));  // buy 10 @100
  orders.emplace_back("order_2", OrderType::SELL, 99.0, 5, static_cast<int64_t>(time(nullptr)));   // sell 5 @99 -> matches 5
  orders.emplace_back("order_3", OrderType::SELL, 100.0, 10, static_cast<int64_t>(time(nullptr))); // sell 10 @100 -> matches remaining 5, leaves 5
  orders.emplace_back("order_4", OrderType::BUY, 101.0, 3, static_cast<int64_t>(time(nullptr)));   // buy 3 @101 -> matches with best ask (remaining 5 at 100)


  nlohmann::json output = nlohmann::json::object();
  output["trades"] = nlohmann::json::array();
  output["remaining_orders"] = nlohmann::json::array();

  for (const auto &o : orders)
  {
    auto res = engine.processOrder(o);
    for (const Trade &t : res.trades)
    {
      output["trades"].push_back(t);
    }
    if (res.remainingOrder)
    {
      output["remaining_orders"].push_back(*res.remainingOrder);
    }
  }

  cout << output.dump(2) << endl;
  return 0;
}
