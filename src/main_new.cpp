#include "engine/MatchingEngine.h"
#include "models/Order.h"
#include "models/Trade.h"
#include "utils/Time.h"
#include <ctime>
#include <iostream>
#include <nlohmann/json.hpp>
#include <sstream>
#include <stdexcept>
#include <string>

int main_cli(int argc, char *argv[]) {
  nlohmann::json response = {{"trades", nlohmann::json::array()},
                             {"remaining_orders", nlohmann::json::array()}};

  std::string raw;
  if (argc < 2) {
    // read from stdin
    std::ostringstream ss;
    ss << std::cin.rdbuf();
    raw = ss.str();
    if (raw.empty()) {
      std::cout << response.dump();
      return 1;
    }
  } else {
    raw = argv[1];
  }

  try {
    auto input = nlohmann::json::parse(raw);

    MatchingEngine engine;

    if (input.is_array()) {
      for (const auto &elem : input) {
        Order order = elem.get<Order>();
        if (!order.isValid()) {
          std::cerr << "Invalid order payload in array\n";
          continue;
        }

        auto result = engine.processOrder(order);
        for (const Trade &trade : result.trades)
          response["trades"].push_back(trade);
        if (result.remainingOrder)
          response["remaining_orders"].push_back(*result.remainingOrder);
      }
    } else if (input.is_object()) {
      Order order = input.get<Order>();
      if (!order.isValid()) {
        std::cerr << "Invalid order payload\n";
      } else {
        auto result = engine.processOrder(order);
        for (const Trade &trade : result.trades)
          response["trades"].push_back(trade);
        if (result.remainingOrder)
          response["remaining_orders"].push_back(*result.remainingOrder);
      }
    } else {
      std::cerr << "Unsupported JSON input: must be object or array\n";
    }
  } catch (const std::exception &ex) {
    std::cerr << "Order parsing failed: " << ex.what() << '\n';
  }

  std::cout << response.dump();
  return 0;
}

// Keep original main for compatibility but delegate to new CLI
int main(int argc, char *argv[]) {
  return main_cli(argc, argv);
}
