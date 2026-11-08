#ifndef DOCLANG_NATIVE_SOURCE_H_
#define DOCLANG_NATIVE_SOURCE_H_

#include <stdexcept>
#include <string>
#include <string_view>

#include <doclang/archive.h>

namespace doclang::native
{
  inline constexpr std::string_view SOURCE_MIMETYPE = "source/mimetype";
  inline constexpr std::string_view SOURCE_DOCUMENT = "source/document";

  inline bool valid_source_mimetype(std::string_view value)
  {
    const auto slash = value.find('/');
    if(slash == value.npos or slash == 0 or slash + 1 == value.size())
      {
        return false;
      }
    for(std::size_t i = 0; i < value.size(); ++i)
      {
        const char c = value[i];
        if(i != slash
           and not((c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z') or (c >= '0' and c <= '9')
                   or std::string_view("!#$&^_.+-").find(c) != value.npos))
          {
            return false;
          }
      }
    return true;
  }

  inline std::string source_mimetype(const archive& zip)
  {
    const auto text = zip.text(SOURCE_MIMETYPE);
    if(not text)
      {
        throw std::runtime_error("could not read source/mimetype");
      }
    std::string_view value = *text;
    if(value.ends_with("\r\n"))
      {
        value.remove_suffix(2);
      }
    else if(value.ends_with('\n') or value.ends_with('\r'))
      {
        value.remove_suffix(1);
      }
    if(not valid_source_mimetype(value))
      {
        throw std::invalid_argument("invalid MIME type in source/mimetype");
      }
    return std::string(value);
  }

  inline bool validate_source_parts(const archive& zip, std::string& error)
  {
    if(zip.has(SOURCE_MIMETYPE) != zip.has(SOURCE_DOCUMENT))
      {
        error = "source/mimetype and source/document must be present together";
        return false;
      }
    if(zip.has(SOURCE_MIMETYPE))
      {
        try
          {
            source_mimetype(zip);
          }
        catch(const std::exception& exc)
          {
            error = exc.what();
            return false;
          }
      }
    return true;
  }
}

#endif
