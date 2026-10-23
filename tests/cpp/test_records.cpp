#include <doclang/annotations.h>
#include <doclang/records.h>
#include <doclang/utils/hash.h>
#include <doclang/version.h>
#include <doclang/vocabulary.h>

#include "test_support.h"

#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

using namespace doclang::native;

namespace
{
  void typed_records_and_csv()
  {
    const base_property property("language", "/doclang[1]/text[1]", "en", 0.75f);
    CHECK(std::get<1>(property.values()) == "/doclang[1]/text[1]");
    CHECK(property.to_row()[2] == "en");
    std::vector<base_property> properties;
    std::string error;
    CHECK(load_properties_csv(to_properties_csv({ property }), properties, error));
    CHECK(properties.size() == 1);
    CHECK(properties[0].get_conf() == 0.75f);

    const base_instance instance("term", "", "/doclang[1]/text[1]", 1.0f, 42, 7, 0, 4, "FeSe",
                                 "FeSe");
    std::vector<base_instance> instances;
    CHECK(load_instances_csv(to_instances_csv({ instance }), instances, error));
    CHECK(instances.size() == 1);
    CHECK(instances[0].get_xpath() == "/doclang[1]/text[1]");
    CHECK(instances[0].get_char_j() == 4);

    const base_entity entity("term", "", "FeSe", 42, 2);
    std::vector<base_entity> entities;
    CHECK(load_entities_csv(to_entities_csv({ entity }), entities, error));
    CHECK(entities.size() == 1);
    CHECK(entities[0].get_count() == 2);

    const base_relation relation("contains", 0.8f, 42, 7);
    std::vector<base_relation> relations;
    CHECK(load_relations_csv(to_relations_csv({ relation }), relations, error));
    CHECK(relations.size() == 1);
    CHECK(relations[0].get_hash_j() == 7);
  }

  void malformed_csv()
  {
    std::vector<base_property> properties;
    std::string error;
    CHECK(!load_properties_csv("type,xpath,label,old_conf\n", properties, error));
    CHECK(error.find("header") != std::string::npos);
    error.clear();
    CHECK(!load_properties_csv("type,xpath,label,confidence\na,b,c\n", properties, error));
    CHECK(error.find("width") != std::string::npos);
    CHECK_THROWS_AS(
        load_properties_csv("type,xpath,label,confidence\na,b,c,NaN\n", properties, error),
        std::invalid_argument);
  }

  void vocabulary_hash_and_version()
  {
    CHECK(reproducible_hash("FeSe") == reproducible_hash("FeSe"));
    CHECK(reproducible_hash("FeSe") != reproducible_hash("FeS"));
    CHECK(to_string(element_tag::table) == "table");
    CHECK(to_string(attribute_name::class_) == "class");
    CHECK(to_string(otsl_token::fc) == "fcel");
    CHECK(element_tag_from_string("picture") == element_tag::picture);
    CHECK(!element_tag_from_string("unknown").has_value());
    CHECK(doclang_version::parse("0.10") > doclang_version::parse("0.9"));
    CHECK(doclang_version::parse("1.0").to_string() == "1.0");
    CHECK_THROWS_AS(doclang_version::parse("1.0.0"), std::invalid_argument);
  }
}

int main()
{
  return test_support::run({ { "typed records and CSV", typed_records_and_csv },
                             { "malformed CSV", malformed_csv },
                             { "vocabulary, hash, version", vocabulary_hash_and_version } });
}
