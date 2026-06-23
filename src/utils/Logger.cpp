#include "utils/Logger.h"
#include <iostream>
#include <chrono>
#include <iomanip>
#include <sstream>

std::string Logger::getTimestamp()
{
  auto now = std::chrono::system_clock::now();
  auto time = std::chrono::system_clock::to_time_t(now);

  std::stringstream ss;
  ss << std::put_time(std::localtime(&time), "%H:%M:%S");

  return ss.str();
}

std::string Logger::levelToString(LogLevel level)
{
  switch (level)
  {
  case LogLevel::INFO:
    return "INFO";
  case LogLevel::WARNING:
    return "WARN";
  case LogLevel::ERROR:
    return "ERROR";
  }
  return "UNKNOWN";
}

void Logger::log(LogLevel level, const std::string &message)
{
  std::cout << "[" << getTimestamp() << "] "
            << "[" << levelToString(level) << "] "
            << message << std::endl;
}