#ifndef DOCLANG_NATIVE_RECORDS_H_
#define DOCLANG_NATIVE_RECORDS_H_

#include <cstdint>
#include <iomanip>
#include <limits>
#include <map>
#include <sstream>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include <doclang/hash.h>

namespace doclang::native
{
  struct base_types
  {
    using hash_type = std::uint64_t;
    using cnt_type = std::uint32_t;
    using ind_type = std::uint64_t;
  };

  inline std::string decimal(float value)
  {
    std::ostringstream out;
    out << std::setprecision(std::numeric_limits<float>::max_digits10) << value;
    return out.str();
  }

  class base_property : public base_types
  {
  public:
    using tuple_type = std::tuple<std::string, std::string, std::string, float>;
    inline static const std::vector<std::string> HEADERS =
      {"type", "xpath", "label", "confidence"};

    base_property() = default;
    base_property(std::string type, std::string xpath, std::string label,
                  float confidence):
      values_(std::move(type), std::move(xpath), std::move(label), confidence)
    {}

    const tuple_type& values() const { return values_; }
    const std::string& get_type() const { return std::get<0>(values_); }
    const std::string& get_xpath() const { return std::get<1>(values_); }
    const std::string& get_label() const { return std::get<2>(values_); }
    float get_conf() const { return std::get<3>(values_); }
    std::vector<std::string> to_row() const
    {
      return {get_type(), get_xpath(), get_label(), decimal(get_conf())};
    }

  private:
    tuple_type values_;
  };

  class base_instance : public base_types
  {
  public:
    using tuple_type = std::tuple<std::string, std::string, std::string, float,
                                  hash_type, hash_type, ind_type, ind_type,
                                  std::string, std::string>;
    inline static const std::vector<std::string> HEADERS =
      {"type", "subtype", "xpath", "conf", "ehash", "ihash",
       "char_i", "char_j", "name", "original"};

    base_instance() = default;
    base_instance(std::string type, std::string subtype, std::string xpath,
                  float confidence, hash_type ehash, hash_type ihash,
                  ind_type char_i, ind_type char_j, std::string name,
                  std::string original):
      values_(std::move(type), std::move(subtype), std::move(xpath), confidence,
              ehash, ihash, char_i, char_j, std::move(name),
              std::move(original))
    {}

    const tuple_type& values() const { return values_; }
    const std::string& get_type() const { return std::get<0>(values_); }
    const std::string& get_subtype() const { return std::get<1>(values_); }
    const std::string& get_xpath() const { return std::get<2>(values_); }
    float get_conf() const { return std::get<3>(values_); }
    hash_type get_ehash() const { return std::get<4>(values_); }
    hash_type get_ihash() const { return std::get<5>(values_); }
    ind_type get_char_i() const { return std::get<6>(values_); }
    ind_type get_char_j() const { return std::get<7>(values_); }
    const std::string& get_name() const { return std::get<8>(values_); }
    const std::string& get_original() const { return std::get<9>(values_); }
    std::vector<std::string> to_row() const
    {
      return {get_type(), get_subtype(), get_xpath(), decimal(get_conf()),
              std::to_string(get_ehash()), std::to_string(get_ihash()),
              std::to_string(get_char_i()), std::to_string(get_char_j()),
              get_name(), get_original()};
    }

  private:
    tuple_type values_;
  };

  class base_entity : public base_types
  {
  public:
    using tuple_type = std::tuple<std::string, std::string, std::string,
                                  hash_type, cnt_type>;
    inline static const std::vector<std::string> HEADERS =
      {"type", "subtype", "name", "ehash", "count"};

    base_entity() = default;
    base_entity(std::string type, std::string subtype, std::string name,
                hash_type ehash, cnt_type count):
      values_(std::move(type), std::move(subtype), std::move(name), ehash, count)
    {}

    const tuple_type& values() const { return values_; }
    const std::string& get_type() const { return std::get<0>(values_); }
    const std::string& get_subtype() const { return std::get<1>(values_); }
    const std::string& get_name() const { return std::get<2>(values_); }
    hash_type get_ehash() const { return std::get<3>(values_); }
    cnt_type get_count() const { return std::get<4>(values_); }
    std::vector<std::string> to_row() const
    {
      return {get_type(), get_subtype(), get_name(),
              std::to_string(get_ehash()), std::to_string(get_count())};
    }

  private:
    tuple_type values_;
  };

  inline std::vector<base_entity> compute_entities_from_instances(
    const std::vector<base_instance>& instances)
  {
    using key_type = std::tuple<std::string, std::string, std::string>;
    std::map<key_type, base_types::cnt_type> counts;
    for(const auto& instance : instances)
      {
        std::vector<std::string> words;
        std::istringstream stream(instance.get_name());
        for(std::string word; stream >> word;) words.push_back(word);
        for(std::size_t i = 0; i < words.size(); ++i)
          {
            std::string suffix;
            for(std::size_t j = i; j < words.size(); ++j)
              {
                if(j != i) suffix += ' ';
                suffix += words[j];
              }
            ++counts[{instance.get_type(), instance.get_subtype(), suffix}];
          }
      }

    std::vector<base_entity> result;
    result.reserve(counts.size());
    for(const auto& [key, count] : counts)
      {
        const auto& [type, subtype, name] = key;
        result.emplace_back(type, subtype, name, reproducible_hash(name), count);
      }
    return result;
  }

  class base_relation : public base_types
  {
  public:
    using tuple_type = std::tuple<std::string, float, hash_type, hash_type>;
    inline static const std::vector<std::string> HEADERS =
      {"name", "conf", "hash_i", "hash_j"};

    base_relation() = default;
    base_relation(std::string name, float confidence, hash_type hash_i,
                  hash_type hash_j):
      values_(std::move(name), confidence, hash_i, hash_j)
    {}

    static const std::vector<std::string>& headers() { return HEADERS; }
    const tuple_type& values() const { return values_; }
    const std::string& get_name() const { return std::get<0>(values_); }
    float get_conf() const { return std::get<1>(values_); }
    hash_type get_hash_i() const { return std::get<2>(values_); }
    hash_type get_hash_j() const { return std::get<3>(values_); }
    std::vector<std::string> to_row() const
    {
      return {get_name(), decimal(get_conf()), std::to_string(get_hash_i()),
              std::to_string(get_hash_j())};
    }

  private:
    tuple_type values_;
  };
}

#endif
