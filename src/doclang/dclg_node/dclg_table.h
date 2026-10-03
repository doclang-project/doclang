#ifndef DOCLANG_NATIVE_DCLG_NODE_DCLG_TABLE_H_
#define DOCLANG_NATIVE_DCLG_NODE_DCLG_TABLE_H_

#include <cstddef>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>

#include <doclang/dclg_node.h>
#include <doclang/validation/element.h>
#include <doclang/dclg_node/caption.h>

namespace doclang::native
{
  class dclg_table : public dclg_node
  {
  public:

    dclg_table(std::size_t rows, std::size_t columns);
    void set_caption(std::string_view text);
    std::size_t row_count() const;
    std::size_t column_count() const;
    void insert_row(std::size_t index);
    void delete_row(std::size_t index);
    void insert_column(std::size_t index);
    void delete_column(std::size_t index);
    void append_to_cell(std::size_t row, std::size_t column, const dclg_node& content);
    void clear_cell(std::size_t row, std::size_t column);
    void set_cell(std::size_t row, std::size_t column, const dclg_node& content);
    validation_report validate_local() const;
    std::tuple<bool, std::string> is_valid() const;
    validation_report validate_in(const dclg_document& doc, const insertion_site& site) const;
    std::tuple<bool, std::string> is_valid_in(const dclg_document& doc,
                                              const insertion_site& site) const;

  private:

    pugi::xml_node row_separator(std::size_t row) const;
    std::size_t require_simple_grid() const;
    pugi::xml_node cell_marker(std::size_t row, std::size_t column) const;
  };

  inline dclg_table::dclg_table(std::size_t rows, std::size_t columns)
      : dclg_node(dclg_node::element(element_tag::table))
  {
    if(rows == 0 or columns == 0)
      {
        throw std::invalid_argument("table rows and columns must be positive");
      }
    for(std::size_t row = 0; row < rows; ++row)
      {
        for(std::size_t column = 0; column < columns; ++column)
          {
            root().append_child(xml_name(otsl_token::fc));
          }
        root().append_child(xml_name(otsl_token::nl));
      }
  }

  inline void dclg_table::set_caption(std::string_view text)
  {
    set_element_caption(root(), text);
  }

  inline std::size_t dclg_table::row_count() const
  {
    std::size_t rows = 0;
    for(auto child : root().children(xml_name(otsl_token::nl)))
      {
        ++rows;
      }
    return rows;
  }

  inline std::size_t dclg_table::column_count() const
  {
    std::size_t columns = 0;
    for(auto child : root().children())
      {
        if(std::string_view(child.name()) == to_string_view(otsl_token::nl))
          {
            break;
          }
        if(is_table_cell_marker(child.name()))
          {
            ++columns;
          }
      }
    return columns;
  }

  inline void dclg_table::insert_row(std::size_t index)
  {
    const auto columns = require_simple_grid();
    const auto rows = row_count();
    if(index > rows)
      {
        throw std::out_of_range("table row index out of range");
      }
    const auto anchor = index < rows ? cell_marker(index, 0) : pugi::xml_node{};
    for(std::size_t column = 0; column < columns; ++column)
      {
        if(anchor)
          {
            root().insert_child_before(xml_name(otsl_token::fc), anchor);
          }
        else
          {
            root().append_child(xml_name(otsl_token::fc));
          }
      }
    if(anchor)
      {
        root().insert_child_before(xml_name(otsl_token::nl), anchor);
      }
    else
      {
        root().append_child(xml_name(otsl_token::nl));
      }
  }

  inline void dclg_table::delete_row(std::size_t index)
  {
    require_simple_grid();
    if(row_count() == 1)
      {
        throw std::invalid_argument("cannot delete the last table row");
      }
    auto cursor = cell_marker(index, 0);
    while(cursor)
      {
        const bool last = std::string_view(cursor.name()) == to_string_view(otsl_token::nl);
        auto next = cursor.next_sibling();
        root().remove_child(cursor);
        if(last)
          {
            break;
          }
        cursor = next;
      }
  }

  inline void dclg_table::insert_column(std::size_t index)
  {
    const auto columns = require_simple_grid();
    if(index > columns)
      {
        throw std::out_of_range("table column index out of range");
      }
    for(std::size_t row = 0; row < row_count(); ++row)
      {
        const auto anchor = index < columns ? cell_marker(row, index) : row_separator(row);
        root().insert_child_before(xml_name(otsl_token::fc), anchor);
      }
  }

  inline void dclg_table::delete_column(std::size_t index)
  {
    const auto columns = require_simple_grid();
    if(columns == 1)
      {
        throw std::invalid_argument("cannot delete the last table column");
      }
    if(index >= columns)
      {
        throw std::out_of_range("table column index out of range");
      }
    for(std::size_t row = 0; row < row_count(); ++row)
      {
        auto cursor = cell_marker(row, index);
        do
          {
            auto next = cursor.next_sibling();
            root().remove_child(cursor);
            cursor = next;
          }
        while(cursor and std::string_view(cursor.name()) != to_string_view(otsl_token::nl)
              and not is_table_cell_marker(cursor.name()));
      }
  }

  inline void dclg_table::append_to_cell(std::size_t row, std::size_t column,
                                         const dclg_node& content)
  {
    if(not content.root())
      {
        throw std::invalid_argument("cell content has no element root");
      }
    const auto marker = cell_marker(row, column);
    auto end = marker.next_sibling();
    while(end and std::string_view(end.name()) != to_string_view(otsl_token::nl)
          and not is_table_cell_marker(end.name()))
      {
        end = end.next_sibling();
      }
    if(end)
      {
        root().insert_copy_before(content.root(), end);
      }
    else
      {
        root().append_copy(content.root());
      }
  }

  inline void dclg_table::clear_cell(std::size_t row, std::size_t column)
  {
    auto cursor = cell_marker(row, column).next_sibling();
    while(cursor and std::string_view(cursor.name()) != to_string_view(otsl_token::nl)
          and not is_table_cell_marker(cursor.name()))
      {
        auto next = cursor.next_sibling();
        root().remove_child(cursor);
        cursor = next;
      }
  }

  inline void dclg_table::set_cell(std::size_t row, std::size_t column, const dclg_node& content)
  {
    if(not content.root())
      {
        throw std::invalid_argument("cell content has no element root");
      }
    clear_cell(row, column);
    append_to_cell(row, column, content);
  }

  inline validation_report dclg_table::validate_local() const
  {
    return validate_local_element(*this);
  }

  inline std::tuple<bool, std::string> dclg_table::is_valid() const
  {
    return validate_local().is_valid();
  }

  inline validation_report dclg_table::validate_in(const dclg_document& doc,
                                                   const insertion_site& site) const
  {
    return validate_element_in(*this, doc, site);
  }

  inline std::tuple<bool, std::string> dclg_table::is_valid_in(const dclg_document& doc,
                                                               const insertion_site& site) const
  {
    return validate_in(doc, site).is_valid();
  }

  inline pugi::xml_node dclg_table::row_separator(std::size_t row) const
  {
    std::size_t index = 0;
    for(auto child : root().children(xml_name(otsl_token::nl)))
      {
        if(index++ == row)
          {
            return child;
          }
      }
    throw std::out_of_range("table row index out of range");
  }

  inline std::size_t dclg_table::require_simple_grid() const
  {
    const auto rows = row_count();
    const auto columns = column_count();
    if(rows == 0 or columns == 0)
      {
        throw std::invalid_argument("table has no simple grid");
      }
    std::size_t width = 0;
    for(auto child : root().children())
      {
        const std::string_view name = child.name();
        if(name == to_string_view(otsl_token::nl))
          {
            if(width != columns)
              {
                throw std::invalid_argument("table rows have different widths");
              }
            width = 0;
          }
        else if(is_table_cell_marker(name))
          {
            if(name != to_string_view(otsl_token::fc))
              {
                throw std::invalid_argument("structural edits require fcel markers");
              }
            ++width;
          }
      }
    if(width != 0)
      {
        throw std::invalid_argument("table row is missing its nl separator");
      }
    return columns;
  }

  inline pugi::xml_node dclg_table::cell_marker(std::size_t row, std::size_t column) const
  {
    std::size_t current_row = 0;
    std::size_t current_column = 0;
    for(auto child : root().children())
      {
        if(std::string_view(child.name()) == to_string_view(otsl_token::nl))
          {
            ++current_row;
            current_column = 0;
          }
        else if(is_table_cell_marker(child.name()))
          {
            if(current_row == row and current_column == column)
              {
                return child;
              }
            ++current_column;
          }
      }
    throw std::out_of_range("table cell index out of range");
  }
}

#endif
