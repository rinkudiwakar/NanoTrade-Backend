#pragma once

#include <cstdint>
#include <string>
#include <nlohmann/json.hpp>

class Trade
{
public:
  int buyOrderId;
  int sellOrderId;
  double price;
  int quantity;
  int64_t timestamp;
  std::string buyer_id;
  std::string seller_id;

  Trade() = default;

  // Constructor
  Trade(int buyOrderId,
        int sellOrderId,
        double price,
        int quantity,
        int64_t timestamp,
        std::string buyer_id = "",
        std::string seller_id = "");

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
      {"timestamp", trade.timestamp},
      {"buyer_id", trade.buyer_id},
      {"seller_id", trade.seller_id}};
}

