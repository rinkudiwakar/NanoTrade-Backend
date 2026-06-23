#pragma once
#include <chrono>
#include <iostream>
#include <string>

class ScopedTimer {
public:
  ScopedTimer(const std::string &name)
      : name(name), start(std::chrono::high_resolution_clock::now()) {}
  ~ScopedTimer() {
    using namespace std::chrono;
    auto end = high_resolution_clock::now();
    auto ms = duration_cast<microseconds>(end - start).count();
    std::cerr << "[PROFILE] " << name << " " << ms << "us\n";
  }

private:
  std::string name;
  std::chrono::high_resolution_clock::time_point start;
};
