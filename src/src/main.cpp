#include "engine/MatchingEngine.h"
#include "models/Order.h"
#include "models/Trade.h"
#include <nlohmann/json.hpp>
#include "utils/Time.h"
#include <iostream>
#include <stdexcept>
#include <string>
#include <ctime>

int main(int argc, char *argv[])
{
  nlohmann::json response = {
      {"trades", nlohmann::json::array()},
      {"remaining_order", nullptr}};

  if (argc < 2)
  {
    std::cout << response.dump();
    return 1;
  }

  try
  {
    auto input = nlohmann::json::parse(argv[1]);
    Order order = input.get<Order>();

    if (order.isValid())
    {
      MatchingEngine engine;
      auto result = engine.processOrder(order);

      for (const Trade &trade : result.trades)
      {
        response["trades"].push_back(trade);
      }

      if (result.remainingOrder)
      {
        const Order &remaining = *result.remainingOrder;
        response["remaining_order"] = remaining;
      }
    }
    else
    {
      std::cerr << "Invalid order payload: negative or missing required fields\n";
    }
  }
  catch (const std::exception &ex)
  {
    std::cerr << "Order parsing failed: " << ex.what() << '\n';
  }

  std::cout << response.dump();
  return 0;
}