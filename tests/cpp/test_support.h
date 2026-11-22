#ifndef DOCLANG_TEST_SUPPORT_H_
#define DOCLANG_TEST_SUPPORT_H_

#include <exception>
#include <filesystem>
#include <initializer_list>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace test_support
{
  using test_case = std::pair<const char*, void (*)()>;

  inline void check(bool condition, const char* expression, const char* file, int line)
  {
    if(!condition)
      {
        throw std::runtime_error(std::string(file) + ":" + std::to_string(line) + ": "
                                 + expression);
      }
  }

  template <typename Error, typename Function>
  void check_throws(Function&& function, const char* expression, const char* file, int line)
  {
    try
      {
        std::forward<Function>(function)();
      }
    catch(const Error&)
      {
        return;
      }
    throw std::runtime_error(std::string(file) + ":" + std::to_string(line) + ": expected "
                             + expression + " to throw");
  }

  inline int run(std::initializer_list<test_case> tests)
  {
    int failures = 0;
    for(const auto& [name, function] : tests)
      {
        try
          {
            function();
            std::cout << "PASS " << name << '\n';
          }
        catch(const std::exception& error)
          {
            ++failures;
            std::cerr << "FAIL " << name << ": " << error.what() << '\n';
          }
      }
    return failures == 0 ? 0 : 1;
  }

  inline std::filesystem::path fixture(std::string_view relative)
  {
    return std::filesystem::path(DOCLANG_SOURCE_DIR) / "tests" / "data" / relative;
  }
}

#define CHECK(expression)                                                                          \
  ::test_support::check(static_cast<bool>(expression), #expression, __FILE__, __LINE__)
#define CHECK_THROWS_AS(expression, error_type)                                                    \
  ::test_support::check_throws<error_type>([&] { (void)(expression); }, #expression, __FILE__,     \
                                           __LINE__)

#endif
