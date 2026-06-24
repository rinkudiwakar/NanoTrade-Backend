#include "utils/Time.h"
#include <chrono>

int64_t Time::now()
{
  return std::chrono::duration_cast<std::chrono::nanoseconds>(
             std::chrono::high_resolution_clock::now().time_since_epoch())
      .count();
}