#ifndef DOCLANG_NATIVE_VERSION_H_
#define DOCLANG_NATIVE_VERSION_H_

#include <charconv>
#include <compare>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>
#include <system_error>

namespace doclang::native
{
  struct doclang_version
  {
    std::uint32_t major = 0;
    std::uint32_t minor = 0;

    static doclang_version parse(std::string_view value);
    std::string to_string() const;

    auto operator<=>(const doclang_version&) const = default;
  };

  inline constexpr doclang_version default_doclang_version{ 0, 7 };

  inline doclang_version doclang_version::parse(std::string_view value)
  {
    const auto separator = value.find('.');
    if(separator == std::string_view::npos or separator == 0 or separator == value.size() - 1
       or value.find('.', separator + 1) != std::string_view::npos)
      {
        throw std::invalid_argument("DocLang version must have MAJOR.MINOR form");
      }

    doclang_version result;
    const auto major_text = value.substr(0, separator);
    const auto minor_text = value.substr(separator + 1);
    const auto major_parse
        = std::from_chars(major_text.data(), major_text.data() + major_text.size(), result.major);
    const auto minor_parse
        = std::from_chars(minor_text.data(), minor_text.data() + minor_text.size(), result.minor);
    if(major_parse.ec != std::errc{} or major_parse.ptr != major_text.data() + major_text.size()
       or minor_parse.ec != std::errc{} or minor_parse.ptr != minor_text.data() + minor_text.size())
      {
        throw std::invalid_argument("DocLang version must have MAJOR.MINOR form");
      }
    return result;
  }

  inline std::string doclang_version::to_string() const
  {
    return std::to_string(major) + "." + std::to_string(minor);
  }
}

#endif
