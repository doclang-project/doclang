#ifndef DOCLANG_NATIVE_DCLG_NODE_DCLG_LIST_H_
#define DOCLANG_NATIVE_DCLG_NODE_DCLG_LIST_H_

#include <cstddef>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>

#include <doclang/dclg_node.h>
#include <doclang/validation/element.h>

namespace doclang::native
{
  class dclg_list : public dclg_node
  {
  public:

    explicit dclg_list(std::string_view kind = "unordered");
    std::size_t item_count() const;
    void append_item(const dclg_node& content);
    void insert_item(std::size_t index, const dclg_node& content);
    void append_item_text(std::string_view text);
    void insert_item_text(std::size_t index, std::string_view text);
    void append_to_item(std::size_t index, const dclg_node& content);
    void delete_item(std::size_t index);
    validation_report validate_local() const;
    std::tuple<bool, std::string> is_valid() const;
    validation_report validate_in(const dclg_document& doc, const insertion_site& site) const;
    std::tuple<bool, std::string> is_valid_in(const dclg_document& doc,
                                              const insertion_site& site) const;

  private:

    pugi::xml_node item_marker(std::size_t index) const;
  };

  inline dclg_list::dclg_list(std::string_view kind)
      : dclg_node(dclg_node::element(element_tag::list))
  {
    if(kind != "ordered" and kind != "unordered")
      {
        throw std::invalid_argument("list kind must be ordered or unordered");
      }
    set_attribute(attribute_name::class_, kind);
  }

  inline std::size_t dclg_list::item_count() const
  {
    std::size_t count = 0;
    for(auto child : root().children(xml_name(element_tag::ldiv)))
      {
        ++count;
      }
    return count;
  }

  inline void dclg_list::append_item(const dclg_node& content)
  {
    insert_item(item_count(), content);
  }

  inline void dclg_list::insert_item(std::size_t index, const dclg_node& content)
  {
    if(not content.root())
      {
        throw std::invalid_argument("item content has no element root");
      }
    const auto count = item_count();
    if(index > count)
      {
        throw std::out_of_range("list item index out of range");
      }
    const auto anchor = index < count ? item_marker(index) : pugi::xml_node{};
    if(anchor)
      {
        root().insert_child_before(xml_name(element_tag::ldiv), anchor);
        root().insert_copy_before(content.root(), anchor);
      }
    else
      {
        root().append_child(xml_name(element_tag::ldiv));
        root().append_copy(content.root());
      }
  }

  inline void dclg_list::append_item_text(std::string_view text)
  {
    root().append_child(xml_name(element_tag::ldiv));
    root().append_child(pugi::node_pcdata).set_value(std::string(text).c_str());
  }

  inline void dclg_list::insert_item_text(std::size_t index, std::string_view text)
  {
    const auto count = item_count();
    if(index > count)
      {
        throw std::out_of_range("list item index out of range");
      }
    const auto anchor = index < count ? item_marker(index) : pugi::xml_node{};
    if(anchor)
      {
        root().insert_child_before(xml_name(element_tag::ldiv), anchor);
        root().insert_child_before(pugi::node_pcdata, anchor).set_value(std::string(text).c_str());
      }
    else
      {
        append_item_text(text);
      }
  }

  inline void dclg_list::append_to_item(std::size_t index, const dclg_node& content)
  {
    const auto marker = item_marker(index);
    auto end = marker.next_sibling();
    while(end and std::string_view(end.name()) != to_string_view(element_tag::ldiv))
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

  inline void dclg_list::delete_item(std::size_t index)
  {
    auto cursor = item_marker(index);
    do
      {
        auto next = cursor.next_sibling();
        root().remove_child(cursor);
        cursor = next;
      }
    while(cursor and std::string_view(cursor.name()) != to_string_view(element_tag::ldiv));
  }

  inline validation_report dclg_list::validate_local() const
  {
    return validate_local_element(*this);
  }

  inline std::tuple<bool, std::string> dclg_list::is_valid() const
  {
    return validate_local().is_valid();
  }

  inline validation_report dclg_list::validate_in(const dclg_document& doc,
                                                  const insertion_site& site) const
  {
    return validate_element_in(*this, doc, site);
  }

  inline std::tuple<bool, std::string> dclg_list::is_valid_in(const dclg_document& doc,
                                                              const insertion_site& site) const
  {
    return validate_in(doc, site).is_valid();
  }

  inline pugi::xml_node dclg_list::item_marker(std::size_t index) const
  {
    std::size_t count = 0;
    for(auto child : root().children(xml_name(element_tag::ldiv)))
      {
        if(count++ == index)
          {
            return child;
          }
      }
    throw std::out_of_range("list item index out of range");
  }
}

#endif
