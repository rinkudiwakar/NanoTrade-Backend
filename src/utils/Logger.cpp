#include "utils/Logger.h"
#include <cstdio>

// ─────────────────────────────────────────────────────────────────
// ANSI color codes (stdout only — stripped for file output)
// ─────────────────────────────────────────────────────────────────
#define COLOR_RESET  "\033[0m"
#define COLOR_GREY   "\033[90m"
#define COLOR_CYAN   "\033[36m"
#define COLOR_YELLOW "\033[33m"
#define COLOR_RED    "\033[31m"

// ─────────────────────────────────────────────────────────────────
// Singleton accessor
// ─────────────────────────────────────────────────────────────────
Logger& Logger::instance()
{
  static Logger inst;
  return inst;
}

Logger::Logger()  = default;
Logger::~Logger() = default;

// ─────────────────────────────────────────────────────────────────
// Configuration
// ─────────────────────────────────────────────────────────────────
void Logger::setLevel(LogLevel level)
{
  std::lock_guard<std::mutex> lock(mutex_);
  minLevel_ = level;
}

void Logger::setLogFile(const std::string& path)
{
  std::lock_guard<std::mutex> lock(mutex_);
  fileStream_.open(path, std::ios::app);
}

// ─────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────
std::string Logger::getTimestampMs()
{
  using namespace std::chrono;
  auto now      = system_clock::now();
  auto ms       = duration_cast<milliseconds>(now.time_since_epoch()) % 1000;
  auto time_t   = system_clock::to_time_t(now);

  std::ostringstream ss;
  ss << std::put_time(std::localtime(&time_t), "%H:%M:%S")
     << '.' << std::setfill('0') << std::setw(3) << ms.count();
  return ss.str();
}

std::string Logger::levelToString(LogLevel level)
{
  switch (level)
  {
    case LogLevel::DEBUG:   return "DEBUG";
    case LogLevel::INFO:    return "INFO ";
    case LogLevel::WARNING: return "WARN ";
    case LogLevel::ERROR:   return "ERROR";
  }
  return "?????";
}

std::string Logger::levelToColor(LogLevel level)
{
  switch (level)
  {
    case LogLevel::DEBUG:   return COLOR_GREY;
    case LogLevel::INFO:    return COLOR_CYAN;
    case LogLevel::WARNING: return COLOR_YELLOW;
    case LogLevel::ERROR:   return COLOR_RED;
  }
  return COLOR_RESET;
}

// ─────────────────────────────────────────────────────────────────
// Core log method
// Format: [HH:MM:SS.mmm] [LEVEL] [component] [tid:XXXX] message  (file:line)
// ─────────────────────────────────────────────────────────────────
void Logger::log(LogLevel level,
                 const std::string& component,
                 const std::string& message,
                 const char* file,
                 int         line)
{
  if (level < minLevel_)
    return;

  // Thread ID (short hash for readability)
  std::ostringstream tid_ss;
  tid_ss << std::hex << (std::hash<std::thread::id>{}(std::this_thread::get_id()) & 0xFFFF);
  std::string tid = tid_ss.str();

  // Source file basename (strip full path)
  std::string src;
  if (file)
  {
    std::string full(file);
    auto pos = full.find_last_of("/\\");
    src = (pos != std::string::npos) ? full.substr(pos + 1) : full;
    src += ":" + std::to_string(line);
  }

  // Build the colored console line
  std::string color  = levelToColor(level);
  std::string ts     = getTimestampMs();
  std::string lvl    = levelToString(level);

  std::ostringstream console;
  console << color
          << "[" << ts << "] "
          << "[" << lvl << "] "
          << "[" << component << "] "
          << "[tid:" << tid << "] "
          << message;
  if (!src.empty())
    console << "  (" << src << ")";
  console << COLOR_RESET;

  // Plain line for file (no ANSI)
  std::ostringstream plain;
  plain << "[" << ts << "] "
        << "[" << lvl << "] "
        << "[" << component << "] "
        << "[tid:" << tid << "] "
        << message;
  if (!src.empty())
    plain << "  (" << src << ")";

  std::lock_guard<std::mutex> lock(mutex_);
  std::cout << console.str() << "\n";

  if (fileStream_.is_open())
    fileStream_ << plain.str() << "\n";
}