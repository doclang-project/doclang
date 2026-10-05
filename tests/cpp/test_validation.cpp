#include <doclang/dclg_document.h>
#include <doclang/dclg_node/dclg_field_item.h>
#include <doclang/dclg_node/dclg_text.h>
#include <doclang/validation/rules.h>

#include "test_support.h"

#include <fstream>
#include <iterator>
#include <string>
#include <string_view>
#include <vector>

using namespace doclang::native;

namespace
{
  struct assertion_case
  {
    const char* id;
    const char* valid;
    const char* invalid;
  };

  std::string xml(std::string_view body)
  {
    return "<doclang xmlns=\"https://www.doclang.ai/ns/v0\">" + std::string(body) + "</doclang>";
  }

  bool has_assertion(const std::vector<validation_issue>& issues, std::string_view id)
  {
    for(const auto& issue : issues)
      {
        if(issue.assertion == id)
          {
            CHECK(!issue.location.empty());
            CHECK(!issue.message.empty());
            return true;
          }
      }
    return false;
  }

  void every_schematron_assertion()
  {
    const assertion_case cases[] = {
      { "list-structure", "<list><ldiv/></list>", "<list><text/><ldiv/></list>" },
      { "table-structure", "<table><fcel/></table>", "<table><nl/></table>" },
      { "table-rectangular-grid", "<table><fcel/><lcel/><nl/><fcel/><lcel/><nl/></table>",
        "<table><fcel/><lcel/><nl/><fcel/><nl/></table>" },
      { "element-head-placement", "<text><label/>Body</text>", "<text>Body<label/></text>" },
      { "xref-href-mutual-exclusivity",
        "<text><xref thread_id=\"1\"/></text><text><thread thread_id=\"1\"/></text>",
        "<text><xref thread_id=\"1\"/><href uri=\"https://example.org\"/></text>"
        "<text><thread thread_id=\"1\"/></text>" },
      { "xref-thread-defined",
        "<text><xref thread_id=\"1\"/></text><text><thread thread_id=\"1\"/></text>",
        "<text><xref thread_id=\"1\"/></text>" },
      { "location-value-range",
        "<text><location value=\"0\" resolution=\"10\"/><location value=\"0\"/>"
        "<location value=\"9\" resolution=\"10\"/><location value=\"9\"/></text>",
        "<text><location value=\"10\" resolution=\"10\"/><location value=\"0\"/>"
        "<location value=\"9\" resolution=\"10\"/><location value=\"9\"/></text>" },
      { "location-block-order",
        "<text><location value=\"10\"/><location value=\"10\"/>"
        "<location value=\"50\"/><location value=\"50\"/></text>",
        "<text><location value=\"100\"/><location value=\"10\"/>"
        "<location value=\"50\"/><location value=\"50\"/></text>" },
      { "thread-host-type-consistency",
        "<text><thread thread_id=\"1\"/></text><text><thread thread_id=\"1\"/></text>",
        "<text><thread thread_id=\"1\"/></text><picture><thread thread_id=\"1\"/></picture>" },
      { "list-virtual-text-element-head", "<list><ldiv/><label/>Body</list>",
        "<list><ldiv/>Body<label/></list>" },
      { "table-virtual-text-element-head", "<table><fcel/><label/>Body</table>",
        "<table><fcel/>Body<label/></table>" },
      { "field-heading-region", "<field_region><field_heading/></field_region>",
        "<field_heading/>" },
      { "field-item-region", "<field_region><field_item/></field_region>", "<field_item/>" },
      { "key-field-item", "<field_region><field_item><key/></field_item></field_region>",
        "<key/>" },
      { "value-field-item", "<field_region><field_item><value/></field_item></field_region>",
        "<value/>" },
      { "field-item-own-key", "<field_region><field_item><key/></field_item></field_region>",
        "<field_region><field_item><key/><key/></field_item></field_region>" },
      { "picture-tabular-chart", "<picture class=\"chart\"><tabular/></picture>",
        "<picture><tabular/></picture>" },
      { "picture-src-first", "<picture><src/></picture>", "<picture><text/><src/></picture>" },
      { "picture-tabular-after-src", "<picture class=\"chart\"><src/><tabular/></picture>",
        "<picture class=\"chart\"><src/><text/><tabular/></picture>" },
    };
    CHECK(std::size(cases) == 19);
    for(const auto& item : cases)
      {
        CHECK(!has_assertion(validate_schematron_xml(xml(item.valid)), item.id));
        CHECK(has_assertion(validate_schematron_xml(xml(item.invalid)), item.id));
      }
  }

  void full_and_scoped_validation()
  {
    dclg_document document;
    CHECK(document.read(xml("<text>Body</text>")));
    CHECK(document.is_valid() == std::make_tuple(true, std::string{}));
    CHECK(document.read(xml("<heading level=\"0\">Bad</heading>"
                            "<text><xref thread_id=\"1\"/>Body</text>")));
    CHECK(document.valid());
    auto report = document.validate();
    CHECK(!report.ok());
    CHECK(!report.xsd_errors.empty());
    CHECK(has_assertion(report.schematron_errors, "xref-thread-defined"));
    CHECK(document.validate({ .xsd_only = true }).schematron_errors.empty());
    CHECK(document.validate({ .schematron_only = true }).xsd_errors.empty());

    dclg_text node("Body");
    CHECK(node.validate_local().scope == "local");
    CHECK(std::get<0>(node.is_valid()));
    node.set_attribute("unsupported", "yes");
    CHECK(!node.validate_local().xsd_errors.empty());
    dclg_field_item item;
    auto candidate = dclg_document::create_empty();
    const auto before = candidate.raw();
    CHECK(std::get<0>(item.is_valid()));
    auto contextual = item.validate_in(candidate, insertion_site::append_child("/doclang[1]"));
    CHECK(contextual.scope == "contextual");
    CHECK(!contextual.ok());
    CHECK(candidate.raw() == before);
  }

  void namespace_and_fixture()
  {
    const std::string prefixed = "<dl:doclang xmlns:dl=\"https://www.doclang.ai/ns/v0\">"
                                 "<dl:text>Body<dl:label/></dl:text></dl:doclang>";
    CHECK(has_assertion(validate_schematron_xml(prefixed), "element-head-placement"));
    const std::string no_namespace = "<doclang><text>Body<label/></text></doclang>";
    CHECK(validate_schematron_xml(no_namespace).empty());
    CHECK(has_assertion(validate_schematron_xml(no_namespace, true), "element-head-placement"));

    const auto path = test_support::fixture("valid/ok_comprehensive.dclg.xml");
    std::ifstream stream(path);
    CHECK(stream.good());
    const std::string content(std::istreambuf_iterator<char>{ stream },
                              std::istreambuf_iterator<char>{});
    CHECK(validate_schematron_xml(content).empty());
  }
}

int main()
{
  return test_support::run({ { "every Schematron assertion", every_schematron_assertion },
                             { "full and scoped validation", full_and_scoped_validation },
                             { "namespace and fixture", namespace_and_fixture } });
}
