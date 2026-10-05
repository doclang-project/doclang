#include <doclang/archive.h>

#include "test_support.h"

#include <cstddef>
#include <string>
#include <vector>

using namespace doclang::native;

namespace
{
  void round_trip_and_preservation()
  {
    archive original;
    original.set_text("document.xml", "<doclang/>");
    original.set_text("assets/note.txt", "keep me");
    const std::vector<std::byte> opaque{ std::byte{ 0 }, std::byte{ 255 } };
    original.set_bytes("assets/data.bin", opaque);
    archive::bytes_type buffer;
    CHECK(original.write_to_memory(buffer));
    CHECK(!buffer.empty());

    archive restored;
    CHECK(restored.load_from_memory(buffer));
    CHECK(restored.text("document.xml") == "<doclang/>");
    CHECK(restored.text("assets/note.txt") == "keep me");
    CHECK(restored.bytes("assets/data.bin").has_value());
    CHECK(restored.bytes("assets/data.bin")->size() == opaque.size());
    CHECK((*restored.bytes("assets/data.bin"))[1] == std::byte{ 255 });
    restored.erase("assets/note.txt");
    CHECK(!restored.has("assets/note.txt"));
    CHECK(restored.has("document.xml"));
  }

  void bad_archive()
  {
    archive restored;
    const std::vector<std::byte> invalid{ std::byte{ 1 }, std::byte{ 2 } };
    CHECK(!restored.load_from_memory(invalid));
    CHECK(!restored.get_last_error().empty());

    archive missing_document;
    missing_document.set_text("assets/note.txt", "no document");
    archive::bytes_type buffer;
    CHECK(missing_document.write_to_memory(buffer));
    CHECK(!restored.load_from_memory(buffer));
    CHECK(restored.get_last_error().find("document.xml") != std::string::npos);
  }
}

int main()
{
  return test_support::run({ { "round trip and preservation", round_trip_and_preservation },
                             { "bad archive", bad_archive } });
}
