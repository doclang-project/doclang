#include <doclang/annotations.h>
#include <doclang/dclx_document.h>
#include <doclang/dclg_node/dclg_text.h>
#include <doclang/io/reader.h>
#include <doclang/io/writer.h>

#include "test_support.h"

#include <cstddef>
#include <memory>
#include <string>
#include <vector>

using namespace doclang::native;

namespace
{
  void archive_and_annotation_round_trip()
  {
    dclx_document document;
    CHECK(document.read("<doclang version=\"0.7\"><text>FeSe</text></doclang>"));
    archive source;
    source.set_text("document.xml", document.raw());
    source.set_text("assets/keep.txt", "opaque asset");
    source.set_text("annotations/edges.csv", "legacy graph");
    document.set_archive(std::move(source));
    document.mutable_properties().emplace_back("language", "/doclang[1]/text[1]", "en", 1.0f);
    document.mutable_instances().emplace_back("term", "", "/doclang[1]/text[1]", 1.0f, 42, 7, 0, 4,
                                              "FeSe", "FeSe");
    document.mutable_relations().emplace_back("contains", 0.8f, 42, 9);
    document.set_document_reference("@article{document}\n");

    auto summary = std::make_shared<dclg_document>();
    CHECK(summary->read("<doclang><text>Summary</text></doclang>"));
    document.set_summary(summary);
    CHECK(document.append_child("/doclang[1]", dclg_text("Added")) == "/doclang[1]/text[2]");

    std::vector<std::byte> bytes;
    CHECK(writer::write_dclx_buffer(document, bytes));
    archive output;
    CHECK(output.load_from_memory(bytes));
    CHECK(output.text("assets/keep.txt") == "opaque asset");
    CHECK(!output.has("annotations/edges.csv"));
    CHECK(output.text("document.xml")->find("Added") != std::string_view::npos);
    CHECK(output.text(ENTITIES_CSV)->find("FeSe") != std::string_view::npos);

    dclx_document restored;
    CHECK(reader::read_dclx_buffer(bytes, restored));
    CHECK(restored.has_archive());
    CHECK(restored.has_annotations());
    CHECK(restored.get_properties().size() == 1);
    CHECK(restored.get_instances().size() == 1);
    CHECK(restored.get_entities().size() == 1);
    CHECK(restored.get_relations().size() == 1);
    CHECK(restored.get_entities()[0].get_name() == "FeSe");
    CHECK(restored.get_document_reference() == "@article{document}\n");
    CHECK(restored.has_summary());
    CHECK(restored.get_summary().value()->at("/doclang[1]/text[1]") == "Summary");
    CHECK(restored.at("/doclang[1]/text[2]") == "Added");
    restored.clear();
    CHECK(!restored.has_archive());
    CHECK(!restored.has_annotations());
  }

  void writer_options_and_bad_input()
  {
    dclx_document document;
    CHECK(document.read("<doclang><text>Body</text></doclang>"));
    document.mutable_properties().emplace_back("language", "/doclang[1]/text[1]", "en", 1.0f);
    std::vector<std::byte> bytes;
    CHECK(writer::write_dclx_buffer(document, bytes, { .include_annotations = false }));
    archive result;
    CHECK(result.load_from_memory(bytes));
    CHECK(!result.has(PROPERTIES_CSV));
    CHECK(result.has("document.xml"));

    dclx_document bad;
    const std::vector<std::byte> invalid{ std::byte{ 0 }, std::byte{ 1 } };
    CHECK(!reader::read_dclx_buffer(invalid, bad));
    CHECK(!bad.get_last_error().empty());
  }
}

int main()
{
  return test_support::run(
      { { "archive and annotation round trip", archive_and_annotation_round_trip },
        { "writer options and bad input", writer_options_and_bad_input } });
}
