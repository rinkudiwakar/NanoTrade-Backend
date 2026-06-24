#pragma once
#include <atomic>
#include <cstddef>
#include <optional>
#include <vector>

// Single-producer single-consumer ring buffer
template <typename T> class SPSCQueue {
public:
  explicit SPSCQueue(size_t capacity_power_of_two)
      : capacity(1u << capacity_power_of_two), mask(capacity - 1), buffer(capacity) {}

  bool push(const T &item) {
    auto head = head_.load(std::memory_order_relaxed);
    auto next = (head + 1) & mask;
    if (next == tail_.load(std::memory_order_acquire))
      return false; // full
    buffer[head] = item;
    head_.store(next, std::memory_order_release);
    return true;
  }

  std::optional<T> pop() {
    auto tail = tail_.load(std::memory_order_relaxed);
    if (tail == head_.load(std::memory_order_acquire))
      return std::nullopt; // empty
    T item = buffer[tail];
    tail_.store((tail + 1) & mask, std::memory_order_release);
    return item;
  }

private:
  const size_t capacity;
  const size_t mask;
  std::vector<T> buffer;
  std::atomic<size_t> head_{0};
  std::atomic<size_t> tail_{0};
};
