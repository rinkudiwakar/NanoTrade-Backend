#pragma once

#include <string>
#include <fstream>
#include <mutex>
#include <sstream>
#include <thread>
#include <chrono>
#include <iomanip>
#include <iostream>

// ─────────────────────────────────────────────────────────────────
// Log levels
// ─────────────────────────────────────────────────────────────────
enum class LogLevel
{
  DEBUG   = 0,
  INFO    = 1,
  WARNING = 2,
  ERROR   = 3
};

// ─────────────────────────────────────────────────────────────────
// Logger — thread-safe, singleton, writes to stdout + optional file
// ─────────────────────────────────────────────────────────────────
class Logger
{
public:
  // Access the global singleton
  static Logger& instance();

  // Configure minimum level and optional log file path
  void setLevel(LogLevel level);
  void setLogFile(const std::string& path);

  // Core log method
  void log(LogLevel level,
           const std::string& component,
           const std::string& message,
           const char* file   = nullptr,
           int         line   = 0);

  // Prevent copy/move
  Logger(const Logger&)            = delete;
  Logger& operator=(const Logger&) = delete;

private:
  Logger();
  ~Logger();

  static std::string levelToString(LogLevel level);
  static std::string levelToColor(LogLevel level);
  static std::string getTimestampMs();

  LogLevel       minLevel_  = LogLevel::DEBUG;
  std::ofstream  fileStream_;
  std::mutex     mutex_;
};

// ─────────────────────────────────────────────────────────────────
// Convenience macros — auto-inject file & line info
// ─────────────────────────────────────────────────────────────────
#define LOG_DEBUG(component, msg) \
    Logger::instance().log(LogLevel::DEBUG,   (component), (msg), __FILE__, __LINE__)

#define LOG_INFO(component, msg) \
    Logger::instance().log(LogLevel::INFO,    (component), (msg), __FILE__, __LINE__)

#define LOG_WARN(component, msg) \
    Logger::instance().log(LogLevel::WARNING, (component), (msg), __FILE__, __LINE__)

#define LOG_ERROR(component, msg) \
    Logger::instance().log(LogLevel::ERROR,   (component), (msg), __FILE__, __LINE__)