#pragma once

#include <string>

enum class LogLevel
{
  INFO,
  WARNING,
  ERROR
};

class Logger
{
public:
  static void log(LogLevel level, const std::string &message);

private:
  static std::string getTimestamp();
  static std::string levelToString(LogLevel level);
};