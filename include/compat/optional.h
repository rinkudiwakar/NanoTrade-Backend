#pragma once

#if defined(__has_include)
#if __has_include(<optional>)
#include <optional>
namespace compat
{
  template <typename T>
  using optional = std::optional<T>;
  using nullopt_t = std::nullopt_t;
  constexpr auto nullopt = std::nullopt;
}
#elif __has_include(<experimental/optional>)
#include <experimental/optional>
namespace compat
{
  template <typename T>
  using optional = std::experimental::optional<T>;
  using nullopt_t = std::experimental::nullopt_t;
  constexpr auto nullopt = std::experimental::nullopt;
}
#else
#error "No <optional> or <experimental/optional> available"
#endif
#else
#include <experimental/optional>
namespace compat
{
  template <typename T>
  using optional = std::experimental::optional<T>;
  using nullopt_t = std::experimental::nullopt_t;
  constexpr auto nullopt = std::experimental::nullopt;
}
#endif
