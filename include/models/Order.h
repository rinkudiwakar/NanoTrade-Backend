#pragma once

#include <cstdint>
#include <ctime>
#include <nlohmann/json.hpp>
#include <stdexcept>
#include <string>

enum class OrderType
{
  BUY,
  SELL
};

static inline OrderType parseOrderType(const nlohmann::json &value)
{
  if (value.is_string())
  {
    std::string typeString = value.get<std::string>();
    if (typeString == "BUY")
      return OrderType::BUY;
    if (typeString == "SELL")
      return OrderType::SELL;
  }
  else if (value.is_number_integer())
  {
    int typeInt = value.get<int>();
    if (typeInt == 0)
      return OrderType::BUY;
    if (typeInt == 1)
      return OrderType::SELL;
  }

  throw std::invalid_argument("Invalid order type");
}

struct Order
{
  int order_id;
  OrderType type;
  double price;
  int quantity;
  int64_t timestamp;
  std::string user_id;
  bool is_user;

  Order() = default;
  Order(int order_id, OrderType type, double price, int quantity, int64_t timestamp, std::string user_id = "", bool is_user = false)
      : order_id(order_id), type(type), price(price), quantity(quantity), timestamp(timestamp), user_id(user_id), is_user(is_user) {}

  bool isBuy() const { return type == OrderType::BUY; }
  bool isSell() const { return type == OrderType::SELL; }

  std::string typeToString() const
  {
    return (type == OrderType::BUY) ? "BUY" : "SELL";
  }

  bool isValid() const
  {
    return order_id > 0 && price > 0.0 && quantity > 0 && timestamp >= 0;
  }
};

inline void to_json(nlohmann::json &j, const Order &order)
{
  j = nlohmann::json{
      {"order_id", order.order_id},
      {"type", order.typeToString()},
      {"price", order.price},
      {"quantity", order.quantity},
      {"timestamp", order.timestamp},
      {"user_id", order.user_id},
      {"is_user", order.is_user}};
}

inline void from_json(const nlohmann::json &j, Order &order)
{
  order.order_id = j.at("order_id").get<int>();
  order.type = parseOrderType(j.at("type"));
  order.price = j.at("price").get<double>();
  order.quantity = j.at("quantity").get<int>();
  order.timestamp = j.value("timestamp", static_cast<int64_t>(std::time(nullptr)));
  order.user_id = j.value("user_id", "");
  order.is_user = j.value("is_user", false);
}

