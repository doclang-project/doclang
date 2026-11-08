#include <doclang/dclg_document.h>
#include <doclang/dclg_node/dclg_text.h>
#include <doclang/view.h>

#include "test_support.h"

#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

using namespace doclang::native;

namespace
{
  void parsing_and_recovery()
  {
    dclg_document document;
    CHECK(!document.valid());
    CHECK(!document.read("<text>wrong root</text>"));
    CHECK(document.get_last_error().find("root") != std::string::npos);
    CHECK(!document.read("<doclang><text>"));
    CHECK(document.get_last_error().find("parse") != std::string::npos);
    const std::string xml = "<doclang version=\"0.7\"><text>Recovered</text></doclang>";
    CHECK(document.read(xml));
    CHECK(document.valid());
    CHECK(document.raw() == xml);
    CHECK(document.version().has_value());
    CHECK(document.version()->to_string() == "0.7");
    CHECK(document.at("/doclang[1]/text[1]") == "Recovered");
  }

  void lookup_and_iteration()
  {
    dclg_document document;
    CHECK(document.read("<doclang><text>One</text><table><fcel/>A<lcel/>B</table>"
                        "<picture><caption>Figure</caption><src uri=\"a.png\"/></picture>"
                        "<text>Two</text></doclang>"));
    CHECK(document.at("/doclang[1]/table[1]", "text") == "A\nB");
    CHECK(document.at("/doclang[1]/picture[1]", "text") == "Figure");
    CHECK(document.at("/doclang[1]/missing[1]").empty());
    CHECK(document.get_last_error().find("not found") != std::string::npos);
    std::vector<std::string> names;
    document.iterate_elements([&](pugi::xml_node node) { names.emplace_back(node.name()); });
    CHECK((names == std::vector<std::string>{ "text", "table", "picture", "text" }));
    std::size_t text_count = 0;
    document.iterate_elements("text", [&](pugi::xml_node) { ++text_count; });
    CHECK(text_count == 2);
  }

  void editing_and_failed_edits()
  {
    auto document = dclg_document::create_empty();
    const auto original_generation = document.generation();
    dclg_text source("First & second");
    CHECK(document.append_child("/doclang[1]", source) == "/doclang[1]/text[1]");
    CHECK(document.prepend_child("/doclang[1]", dclg_text("Zero")) == "/doclang[1]/text[1]");
    CHECK(document.insert_after("/doclang[1]/text[2]", dclg_text("Third"))
          == "/doclang[1]/text[3]");
    CHECK(document.insert_before("/doclang[1]/text[3]", dclg_text("Middle"))
          == "/doclang[1]/text[3]");
    CHECK(document.at("/doclang[1]/text[2]") == "First & second");
    CHECK(document.at("/doclang[1]/text[3]") == "Middle");
    document.erase("/doclang[1]/text[2]");
    CHECK(document.at("/doclang[1]/text[2]") == "Middle");
    CHECK(document.generation() == original_generation + 5);
    CHECK(source.to_xml().find("First &amp; second") != std::string::npos);

    const auto before = document.raw();
    const auto generation = document.generation();
    CHECK_THROWS_AS(document.insert_before("/doclang[1]", dclg_text("bad")), std::invalid_argument);
    CHECK_THROWS_AS(document.erase("/doclang[1]"), std::invalid_argument);
    CHECK_THROWS_AS(document.append_child("/doclang[1]/missing[1]", dclg_text("bad")),
                    std::out_of_range);
    CHECK(document.raw() == before);
    CHECK(document.generation() == generation);
  }

  void views_and_lifetime()
  {
    auto document = std::make_shared<dclg_document>();
    CHECK(document->read("<doclang><heading level=\"2\">Title</heading>"
                         "<text><location value=\"1\"/><location value=\"2\"/>Body</text>"
                         "<table><fcel/>Cell</table></doclang>"));
    document_view view(document);
    CHECK(view.valid());
    CHECK(view.body_elements().size() == 3);
    CHECK(view.text_like_elements().size() == 2);
    CHECK(view.table_elements().size() == 1);
    CHECK(view.elements_by_name("heading")[0].heading_level() == 2);
    CHECK((view.elements_by_name("text")[0].location() == std::vector<float>{ 1.0f, 2.0f }));
    document.reset();
    CHECK(view.valid());
    CHECK(view.body_elements().size() == 3);
  }
}

int main()
{
  return test_support::run({ { "parsing and recovery", parsing_and_recovery },
                             { "lookup and iteration", lookup_and_iteration },
                             { "editing and failed edits", editing_and_failed_edits },
                             { "views and lifetime", views_and_lifetime } });
}
