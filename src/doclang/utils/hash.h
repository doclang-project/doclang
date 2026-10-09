#ifndef DOCLANG_NATIVE_HASH_H_
#define DOCLANG_NATIVE_HASH_H_

#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

namespace doclang::native
{
  inline std::uint64_t mix_hash(std::uint64_t value)
  {
    value ^= value >> 33;
    value *= 0xff51afd7ed558ccdULL;
    value ^= value >> 33;
    value *= 0xc4ceb9fe1a85ec53ULL;
    value ^= value >> 33;
    return value;
  }

  inline std::uint64_t combine_hash(std::uint64_t hash, std::uint64_t value)
  {
    return hash ^ (value + 0x9e3779b9ULL + (hash << 6) + (hash >> 2));
  }

  // Match docling-nlp: hash UTF-16 code units from the valid UTF-8 prefix.
  inline std::uint64_t reproducible_hash(std::string_view text)
  {
    std::vector<std::uint16_t> units;
    units.reserve(text.size());
    for(std::size_t i = 0; i < text.size();)
      {
        const auto first = static_cast<unsigned char>(text[i]);
        std::uint32_t codepoint = 0;
        std::size_t width = 0;
        if(first < 0x80)
          {
            codepoint = first;
            width = 1;
          }
        else if(first >= 0xc2 && first <= 0xdf)
          {
            codepoint = first & 0x1f;
            width = 2;
          }
        else if(first >= 0xe0 && first <= 0xef)
          {
            codepoint = first & 0x0f;
            width = 3;
          }
        else if(first >= 0xf0 && first <= 0xf4)
          {
            codepoint = first & 0x07;
            width = 4;
          }
        else
          {
            break;
          }

        if(i + width > text.size())
          {
            break;
          }
        bool valid = true;
        for(std::size_t j = 1; j < width; ++j)
          {
            const auto next = static_cast<unsigned char>(text[i + j]);
            if((next & 0xc0) != 0x80)
              {
                valid = false;
                break;
              }
            codepoint = (codepoint << 6) | (next & 0x3f);
          }
        if(!valid || (width == 3 && codepoint < 0x800) || (width == 4 && codepoint < 0x10000)
           || (codepoint >= 0xd800 && codepoint <= 0xdfff) || codepoint > 0x10ffff)
          {
            break;
          }
        if(codepoint <= 0xffff)
          {
            units.push_back(static_cast<std::uint16_t>(codepoint));
          }
        else
          {
            codepoint -= 0x10000;
            units.push_back(static_cast<std::uint16_t>(0xd800 + (codepoint >> 10)));
            units.push_back(static_cast<std::uint16_t>(0xdc00 + (codepoint & 0x3ff)));
          }
        i += width;
      }

    auto hash = mix_hash(units.size());
    for(const auto unit : units)
      {
        hash = combine_hash(hash, unit);
      }
    return hash;
  }
}

#endif
