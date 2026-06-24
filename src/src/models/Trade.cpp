#include "models/Trade.h"
#include <iostream>

Trade::Trade(std::string trade_id,
             std::string buyOrderId,
             std::string sellOrderId,
             double price,
             int quantity,
             int64_t timestamp,
             std::string buyer_id,
             std::string seller_id)
    : trade_id(trade_id),
      buyOrderId(buyOrderId),
      sellOrderId(sellOrderId),
      price(price),
      quantity(quantity),
      timestamp(timestamp),
      buyer_id(buyer_id),
      seller_id(seller_id) {}

void Trade::print() const
{
  std::cout << "Trade Executed | "
            << "BuyID: " << buyOrderId
            << ", SellID: " << sellOrderId
            << ", Price: " << price
            << ", Qty: " << quantity
            << ", Time: " << timestamp
            << std::endl;
}