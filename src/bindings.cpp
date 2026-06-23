#include "engine/MatchingEngine.h"
#include "models/Order.h"
#include "models/Trade.h"
#include <pybind11/chrono.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

PYBIND11_MODULE(_nanotrade_ext, m) {
  m.doc() = "NanoTrade matching engine C++ extension";

  // OrderType enum
  py::enum_<OrderType>(m, "OrderType").value("BUY", OrderType::BUY).value("SELL", OrderType::SELL);

  // Order class
  py::class_<Order>(m, "Order")
      .def(py::init<>())
      .def(py::init<int, OrderType, double, int, int64_t, std::string, bool>(),
           py::arg("order_id"), py::arg("type"), py::arg("price"), py::arg("quantity"),
           py::arg("timestamp"), py::arg("user_id") = "", py::arg("is_user") = false)
      .def_readwrite("order_id", &Order::order_id)
      .def_readwrite("type", &Order::type)
      .def_readwrite("price", &Order::price)
      .def_readwrite("quantity", &Order::quantity)
      .def_readwrite("timestamp", &Order::timestamp)
      .def_readwrite("user_id", &Order::user_id)
      .def_readwrite("is_user", &Order::is_user)
      .def("is_buy", &Order::isBuy)
      .def("is_sell", &Order::isSell)
      .def("is_valid", &Order::isValid)
      .def("type_to_string", &Order::typeToString);

  // Trade class
  py::class_<Trade>(m, "Trade")
      .def(py::init<>())
      .def(py::init<int, int, double, int, int64_t, std::string, std::string>(),
           py::arg("buyOrderId"), py::arg("sellOrderId"), py::arg("price"), py::arg("quantity"),
           py::arg("timestamp"), py::arg("buyer_id") = "", py::arg("seller_id") = "")
      .def_readwrite("buy_order_id", &Trade::buyOrderId)
      .def_readwrite("sell_order_id", &Trade::sellOrderId)
      .def_readwrite("price", &Trade::price)
      .def_readwrite("quantity", &Trade::quantity)
      .def_readwrite("timestamp", &Trade::timestamp)
      .def_readwrite("buyer_id", &Trade::buyer_id)
      .def_readwrite("seller_id", &Trade::seller_id);

  // ProcessResult struct
  py::class_<MatchingEngine::ProcessResult>(m, "ProcessResult")
      .def(py::init<>())
      .def_readwrite("trades", &MatchingEngine::ProcessResult::trades)
      .def_readwrite("remaining_order", &MatchingEngine::ProcessResult::remainingOrder)
      .def_readwrite("remaining_quantity", &MatchingEngine::ProcessResult::remainingQuantity)
      .def_readwrite("fill_status", &MatchingEngine::ProcessResult::fillStatus);

  // MatchingEngine class
  py::class_<MatchingEngine>(m, "MatchingEngine")
      .def(py::init<>())
      .def("process_order", &MatchingEngine::processOrder, py::arg("order"))
      .def("get_order_book", &MatchingEngine::getOrderBook);
}

