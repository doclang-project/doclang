#include <doclang/dclg_node.h>
#include <doclang/vocabulary.h>

#include "test_support.h"

#include <stdexcept>
#include <string>

using namespace doclang::native;

namespace
{
  void creation_and_serialization()
  {
    auto node = dclg_node::element(element_tag::text);
    CHECK(node.name() == "text");
    node.set_attribute(attribute_name::class_, "note");
    node.append_text("A < B & C");
    CHECK(node.to_xml().find("A &lt; B &amp; C") != std::string::npos);
    node.remove_attribute(attribute_name::class_);
    CHECK(node.to_xml().find("class=") == std::string::npos);
    CHECK_THROWS_AS(dclg_node::element("bad name"), std::invalid_argument);
    CHECK_THROWS_AS(dclg_node::element("doclang"), std::invalid_argument);
    CHECK_THROWS_AS(dclg_node::from_xml("<text><broken></text>"), std::invalid_argument);
  }

  void child_and_sibling_edits()
  {
    auto parent = dclg_node::element("group");
    parent.append_child(dclg_node::from_xml("<text>Second</text>"));
    parent.prepend_child(dclg_node::from_xml("<text>First</text>"));
    parent.insert_after("/group[1]/text[1]", dclg_node::from_xml("<text>Middle</text>"));
    CHECK(parent.to_xml().find("First") < parent.to_xml().find("Middle"));
    CHECK(parent.to_xml().find("Middle") < parent.to_xml().find("Second"));
    CHECK_THROWS_AS(parent.insert_before("/group[1]", dclg_node::element("text")),
                    std::invalid_argument);
    CHECK_THROWS_AS(parent.insert_after("/group[1]/missing[1]", dclg_node::element("text")),
                    std::out_of_range);
  }

  void detached_copies()
  {
    auto source = dclg_node::from_xml("<picture><src uri=\"a.png\"/></picture>");
    auto copy = source;
    source.set_attribute("class", "chart");
    CHECK(copy.to_xml().find("class=") == std::string::npos);
    auto parent = dclg_node::element("group");
    parent.append_child(copy);
    copy.append_child(dclg_node::element("caption"));
    CHECK(parent.to_xml().find("caption") == std::string::npos);
  }
}

int main()
{
  return test_support::run({ { "creation and serialization", creation_and_serialization },
                             { "child and sibling edits", child_and_sibling_edits },
                             { "detached copies", detached_copies } });
}
