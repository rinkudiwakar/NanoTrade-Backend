#include "models/Trade.h"
#include <iostream>

Trade::Trade(int buyOrderId,
             int sellOrderId,
             double price,
             int quantity,
             int64_t timestamp)
    : buyOrderId(buyOrderId),
      sellOrderId(sellOrderId),
      price(price),
      quantity(quantity),
      timestamp(timestamp) {}

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