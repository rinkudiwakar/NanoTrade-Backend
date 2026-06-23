#pragma once

#include <cstdint>
#include <nlohmann/json.hpp>

class Trade
{
public:
  int buyOrderId;
  int sellOrderId;
  double price;
  int quantity;
  int64_t timestamp;

  // Constructor
  Trade(int buyOrderId,
        int sellOrderId,
        double price,
        int quantity,
        int64_t timestamp);

  // Utility: print trade (for debugging)
  void print() const;
};

inline void to_json(nlohmann::json &j, const Trade &trade)
{
  j = nlohmann::json{
      {"buyOrderId", trade.buyOrderId},
      {"sellOrderId", trade.sellOrderId},
      {"price", trade.price},
      {"quantity", trade.quantity},
      {"timestamp", trade.timestamp}};
}
