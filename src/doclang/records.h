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

#include <doclang/utils/hash.h>

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
    inline static const std::vector<std::string> HEADERS
        = { "type", "xpath", "label", "confidence" };

    base_property();
    base_property(std::string type, std::string xpath, std::string label, float confidence);

    /* reading */
    const tuple_type& values() const;
    const std::string& get_type() const;
    const std::string& get_xpath() const;
    const std::string& get_label() const;
    float get_conf() const;
    std::vector<std::string> to_row() const;

  private:

    /* state */
    tuple_type values_;
  };

  inline base_property::base_property() = default;

  inline base_property::base_property(std::string type, std::string xpath, std::string label, float confidence)
      : values_(std::move(type), std::move(xpath), std::move(label), confidence)
  {
  }
  inline const base_property::tuple_type& base_property::values() const
  {
    return values_;
  }
  inline const std::string& base_property::get_type() const
  {
    return std::get<0>(values_);
  }
  inline const std::string& base_property::get_xpath() const
  {
    return std::get<1>(values_);
  }
  inline const std::string& base_property::get_label() const
  {
    return std::get<2>(values_);
  }
  inline float base_property::get_conf() const
  {
    return std::get<3>(values_);
  }
  inline std::vector<std::string> base_property::to_row() const
  {
    return { get_type(), get_xpath(), get_label(), decimal(get_conf()) };
  }

  class base_instance : public base_types
  {
  public:

    using tuple_type = std::tuple<std::string, std::string, std::string, float, hash_type,
                                  hash_type, ind_type, ind_type, std::string, std::string>;
    inline static const std::vector<std::string> HEADERS
        = { "type",  "subtype", "xpath",  "conf", "ehash",
            "ihash", "char_i",  "char_j", "name", "original" };

    base_instance();
    base_instance(std::string type, std::string subtype, std::string xpath, float confidence,
                  hash_type ehash, hash_type ihash, ind_type char_i, ind_type char_j,
                  std::string name, std::string original);

    /* reading */
    const tuple_type& values() const;
    const std::string& get_type() const;
    const std::string& get_subtype() const;
    const std::string& get_xpath() const;
    float get_conf() const;
    hash_type get_ehash() const;
    hash_type get_ihash() const;
    ind_type get_char_i() const;
    ind_type get_char_j() const;
    const std::string& get_name() const;
    const std::string& get_original() const;
    std::vector<std::string> to_row() const;

  private:

    /* state */
    tuple_type values_;
  };

  inline base_instance::base_instance() = default;

  inline base_instance::base_instance(std::string type, std::string subtype, std::string xpath, float confidence,
                hash_type ehash, hash_type ihash, ind_type char_i, ind_type char_j,
                std::string name, std::string original)
      : values_(std::move(type), std::move(subtype), std::move(xpath), confidence, ehash, ihash,
                char_i, char_j, std::move(name), std::move(original))
  {
  }
  inline const base_instance::tuple_type& base_instance::values() const
  {
    return values_;
  }
  inline const std::string& base_instance::get_type() const
  {
    return std::get<0>(values_);
  }
  inline const std::string& base_instance::get_subtype() const
  {
    return std::get<1>(values_);
  }
  inline const std::string& base_instance::get_xpath() const
  {
    return std::get<2>(values_);
  }
  inline float base_instance::get_conf() const
  {
    return std::get<3>(values_);
  }
  inline base_instance::hash_type base_instance::get_ehash() const
  {
    return std::get<4>(values_);
  }
  inline base_instance::hash_type base_instance::get_ihash() const
  {
    return std::get<5>(values_);
  }
  inline base_instance::ind_type base_instance::get_char_i() const
  {
    return std::get<6>(values_);
  }
  inline base_instance::ind_type base_instance::get_char_j() const
  {
    return std::get<7>(values_);
  }
  inline const std::string& base_instance::get_name() const
  {
    return std::get<8>(values_);
  }
  inline const std::string& base_instance::get_original() const
  {
    return std::get<9>(values_);
  }
  inline std::vector<std::string> base_instance::to_row() const
  {
    return { get_type(),
             get_subtype(),
             get_xpath(),
             decimal(get_conf()),
             std::to_string(get_ehash()),
             std::to_string(get_ihash()),
             std::to_string(get_char_i()),
             std::to_string(get_char_j()),
             get_name(),
             get_original() };
  }

  class base_entity : public base_types
  {
  public:

    using tuple_type = std::tuple<std::string, std::string, std::string, hash_type, cnt_type>;
    inline static const std::vector<std::string> HEADERS
        = { "type", "subtype", "name", "ehash", "count" };

    base_entity();
    base_entity(std::string type, std::string subtype, std::string name, hash_type ehash,
                cnt_type count);

    /* reading */
    const tuple_type& values() const;
    const std::string& get_type() const;
    const std::string& get_subtype() const;
    const std::string& get_name() const;
    hash_type get_ehash() const;
    cnt_type get_count() const;
    std::vector<std::string> to_row() const;

  private:

    /* state */
    tuple_type values_;
  };

  inline base_entity::base_entity() = default;

  inline base_entity::base_entity(std::string type, std::string subtype, std::string name, hash_type ehash,
              cnt_type count)
      : values_(std::move(type), std::move(subtype), std::move(name), ehash, count)
  {
  }
  inline const base_entity::tuple_type& base_entity::values() const
  {
    return values_;
  }
  inline const std::string& base_entity::get_type() const
  {
    return std::get<0>(values_);
  }
  inline const std::string& base_entity::get_subtype() const
  {
    return std::get<1>(values_);
  }
  inline const std::string& base_entity::get_name() const
  {
    return std::get<2>(values_);
  }
  inline base_entity::hash_type base_entity::get_ehash() const
  {
    return std::get<3>(values_);
  }
  inline base_entity::cnt_type base_entity::get_count() const
  {
    return std::get<4>(values_);
  }
  inline std::vector<std::string> base_entity::to_row() const
  {
    return { get_type(), get_subtype(), get_name(), std::to_string(get_ehash()),
             std::to_string(get_count()) };
  }

  inline std::vector<base_entity>
  compute_entities_from_instances(const std::vector<base_instance>& instances)
  {
    using key_type = std::tuple<std::string, std::string, std::string>;
    std::map<key_type, base_types::cnt_type> counts;
    for(const auto& instance : instances)
      {
        std::vector<std::string> words;
        std::istringstream stream(instance.get_name());
        for(std::string word; stream >> word;)
          {
            words.push_back(word);
          }
        for(std::size_t i = 0; i < words.size(); ++i)
          {
            std::string suffix;
            for(std::size_t j = i; j < words.size(); ++j)
              {
                if(j != i)
                  {
                    suffix += ' ';
                  }
                suffix += words[j];
              }
            ++counts[{ instance.get_type(), instance.get_subtype(), suffix }];
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
    inline static const std::vector<std::string> HEADERS = { "name", "conf", "hash_i", "hash_j" };

    base_relation();
    base_relation(std::string name, float confidence, hash_type hash_i, hash_type hash_j);

    /* reading */
    static const std::vector<std::string>& headers();
    const tuple_type& values() const;
    const std::string& get_name() const;
    float get_conf() const;
    hash_type get_hash_i() const;
    hash_type get_hash_j() const;
    std::vector<std::string> to_row() const;

  private:

    /* state */
    tuple_type values_;
  };

  inline base_relation::base_relation() = default;

  inline base_relation::base_relation(std::string name, float confidence, hash_type hash_i, hash_type hash_j)
      : values_(std::move(name), confidence, hash_i, hash_j)
  {
  }
  inline const std::vector<std::string>& base_relation::headers()
  {
    return HEADERS;
  }
  inline const base_relation::tuple_type& base_relation::values() const
  {
    return values_;
  }
  inline const std::string& base_relation::get_name() const
  {
    return std::get<0>(values_);
  }
  inline float base_relation::get_conf() const
  {
    return std::get<1>(values_);
  }
  inline base_relation::hash_type base_relation::get_hash_i() const
  {
    return std::get<2>(values_);
  }
  inline base_relation::hash_type base_relation::get_hash_j() const
  {
    return std::get<3>(values_);
  }
  inline std::vector<std::string> base_relation::to_row() const
  {
    return { get_name(), decimal(get_conf()), std::to_string(get_hash_i()),
             std::to_string(get_hash_j()) };
  }
}

#endif
