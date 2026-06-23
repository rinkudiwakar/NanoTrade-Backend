#pragma once

#include <cstdint>

class Time
{
public:
  // Nanoseconds timestamp (for latency measurement)
  static int64_t now();
};