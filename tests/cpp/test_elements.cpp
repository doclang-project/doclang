#include <doclang/dclg_node/dclg_field_item.h>
#include <doclang/dclg_node/dclg_field_region.h>
#include <doclang/dclg_node/dclg_footnote.h>
#include <doclang/dclg_node/dclg_formula.h>
#include <doclang/dclg_node/dclg_heading.h>
#include <doclang/dclg_node/dclg_list.h>
#include <doclang/dclg_node/dclg_picture.h>
#include <doclang/dclg_node/dclg_table.h>
#include <doclang/dclg_node/dclg_text.h>

#include "test_support.h"

#include <stdexcept>
#include <string>

using namespace doclang::native;

namespace
{
  void simple_elements()
  {
    CHECK(dclg_text("Body").name() == "text");
    CHECK(dclg_formula("x+y").to_xml().find("x+y") != std::string::npos);
    CHECK(dclg_heading("Title", 2).to_xml().find("level=\"2\"") != std::string::npos);
    CHECK(dclg_footnote("Note").name() == "footnote");
    CHECK(dclg_field_region().name() == "field_region");
    CHECK(dclg_field_item().name() == "field_item");
  }

  void list_items()
  {
    dclg_list list;
    list.append_item_text("Tail");
    list.insert_item(0, dclg_text("Head"));
    list.append_to_item(0, dclg_picture("image.png"));
    CHECK(list.item_count() == 2);
    CHECK(list.to_xml().find("Head") < list.to_xml().find("Tail"));
    CHECK(list.to_xml().find("image.png") != std::string::npos);
    const auto before = list.to_xml();
    CHECK_THROWS_AS(list.insert_item_text(3, "Bad"), std::out_of_range);
    CHECK(list.to_xml() == before);
    list.delete_item(0);
    CHECK(list.item_count() == 1);
    CHECK(list.to_xml().find("Head") == std::string::npos);
    CHECK_THROWS_AS(dclg_list("unknown"), std::invalid_argument);
  }

  void complex_table()
  {
    dclg_table table(2, 2);
    table.set_caption("Results");
    dclg_list paragraphs;
    paragraphs.append_item(dclg_text("One"));
    paragraphs.append_item(dclg_text("Two"));
    paragraphs.append_item(dclg_text("Three"));
    table.set_cell(0, 0, paragraphs);
    table.set_cell(0, 1, dclg_picture("plot.png"));
    CHECK(table.row_count() == 2);
    CHECK(table.column_count() == 2);
    CHECK(table.to_xml().find("Results") != std::string::npos);
    CHECK(table.to_xml().find("Three") != std::string::npos);
    CHECK(table.to_xml().find("plot.png") != std::string::npos);
    table.insert_row(1);
    table.insert_column(1);
    CHECK(table.row_count() == 3);
    CHECK(table.column_count() == 3);
    table.delete_row(1);
    table.delete_column(1);
    CHECK(table.row_count() == 2);
    CHECK(table.column_count() == 2);
    const auto before = table.to_xml();
    CHECK_THROWS_AS(table.insert_column(3), std::out_of_range);
    CHECK(table.to_xml() == before);
    CHECK_THROWS_AS(dclg_table(0, 1), std::invalid_argument);
  }

  void picture_with_tabular()
  {
    dclg_table table(1, 1);
    table.set_cell(0, 0, dclg_text("Value"));
    dclg_picture picture;
    picture.set_caption("Chart");
    picture.set_src("chart.png");
    picture.set_tabular(table);
    CHECK(picture.to_xml().find("Chart") != std::string::npos);
    CHECK(picture.to_xml().find("<src") < picture.to_xml().find("<tabular"));
    CHECK(picture.to_xml().find("Value") != std::string::npos);
    CHECK(table.name() == "table");
  }
}

int main()
{
  return test_support::run({ { "simple elements", simple_elements },
                             { "list items", list_items },
                             { "complex table", complex_table },
                             { "picture with tabular", picture_with_tabular } });
}
