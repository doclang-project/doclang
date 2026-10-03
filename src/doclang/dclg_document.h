//-*-C++-*-

#ifndef DOCLANG_NATIVE_DCLG_DOCUMENT_H_
#define DOCLANG_NATIVE_DCLG_DOCUMENT_H_

#include <array>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <pugixml.hpp>

// The DCLG layer owns XML, editing, and explicit validation.
#include <doclang/utils/hash.h>
#include <doclang/content.h>
#include <doclang/dclg_node.h>
#include <doclang/version.h>
#include <doclang/vocabulary.h>
#include <doclang/validation/full.h>

namespace doclang::native
{

  class dclg_document
  {
  public:

    dclg_document() = default;

    static dclg_document create_empty();

    static std::uint64_t hash(std::string_view text);

    void clear();

    bool read(std::string_view dclg);

    bool valid() const
    {
      return static_cast<bool>(root());
    }
    std::optional<doclang_version> version() const;
    std::string raw() const
    {
      return dirty ? serialize_xml(xml_doc) : raw_dclg;
    }
    std::size_t generation() const
    {
      return edit_generation;
    }

    pugi::xml_document& xml()
    {
      return xml_doc;
    }
    const pugi::xml_document& xml() const
    {
      return xml_doc;
    }

    pugi::xml_node root()
    {
      return xml_doc.child(xml_name(element_tag::doclang));
    }
    pugi::xml_node root() const
    {
      return xml_doc.child(xml_name(element_tag::doclang));
    }

    template <typename callback_type> void iterate_elements(callback_type&& callback) const;

    template <typename callback_type>
    void iterate_elements(std::string_view name, callback_type&& callback) const;

    template <typename callback_type> void iterate_table_text(callback_type&& callback) const;

    template <typename callback_type>
    void iterate_table_text(pugi::xml_node table, callback_type&& callback) const;

    template <typename callback_type> void iterate_picture_text(callback_type&& callback) const;

    template <typename callback_type>
    void iterate_picture_text(pugi::xml_node picture, callback_type&& callback) const;

    std::string at(std::string_view xpath, std::string_view mode = "auto");

    std::string append_child(std::string_view parent_path, const dclg_node& node);
    std::string prepend_child(std::string_view parent_path, const dclg_node& node);
    std::string insert_before(std::string_view sibling_path, const dclg_node& node);
    std::string insert_after(std::string_view sibling_path, const dclg_node& node);
    void erase(std::string_view element_path);
    validation_report validate(validation_options options = {}) const;
    std::tuple<bool, std::string> is_valid(validation_options options = {}) const;

    const std::string& get_last_error() const
    {
      return last_error;
    }
    void set_last_error(std::string msg)
    {
      last_error = std::move(msg);
    }

  private:

    std::string raw_dclg;
    pugi::xml_document xml_doc;
    std::string last_error;
    bool dirty = false;
    std::size_t edit_generation = 0;

    pugi::xml_node require_element(std::string_view path) const;
    static std::string path_of(pugi::xml_node node);
  };

  inline dclg_document dclg_document::create_empty()
  {
    dclg_document result;
    auto root = result.xml_doc.append_child(xml_name(element_tag::doclang));
    root.append_attribute(xml_name(attribute_name::xmlns)) = "https://www.doclang.ai/ns/v0";
    root.append_attribute(xml_name(attribute_name::version))
        = default_doclang_version.to_string().c_str();
    result.dirty = true;
    return result;
  }

  inline std::optional<doclang_version> dclg_document::version() const
  {
    if(not root())
      {
        return std::nullopt;
      }
    const auto attribute = root().attribute(xml_name(attribute_name::version));
    return attribute ? doclang_version::parse(attribute.value()) : default_doclang_version;
  }

  inline std::uint64_t dclg_document::hash(std::string_view text)
  {
    return reproducible_hash(std::string(text));
  }

  inline void dclg_document::clear()
  {
    raw_dclg.clear();
    xml_doc.reset();
    last_error.clear();
    dirty = false;
    ++edit_generation;
  }

  inline bool dclg_document::read(std::string_view dclg)
  {
    clear();

    const auto result = xml_doc.load_buffer(dclg.data(), dclg.size(),
                                            pugi::parse_default | pugi::parse_ws_pcdata);
    if(not result)
      {
        std::stringstream ss;
        ss << "could not parse DocLang XML: " << result.description() << " at offset "
           << result.offset;

        xml_doc.reset();
        last_error = ss.str();
        return false;
      }

    if(not root())
      {
        xml_doc.reset();
        last_error = "DocLang XML does not contain root <doclang>";
        return false;
      }

    raw_dclg = std::string(dclg);
    return true;
  }

  inline pugi::xml_node dclg_document::require_element(std::string_view path) const
  {
    const auto lookup = resolve_doclang_path(root(), path);
    if(not lookup.found)
      {
        throw std::out_of_range(lookup.error);
      }
    if(lookup.node.type() != pugi::node_element)
      {
        throw std::invalid_argument("DocLang path must select an element");
      }
    return lookup.node;
  }

  inline std::string dclg_document::path_of(pugi::xml_node node)
  {
    std::string path;
    for(; node and node.type() == pugi::node_element; node = node.parent())
      {
        std::size_t index = 1;
        for(auto sibling = node.previous_sibling(node.name()); sibling;
            sibling = sibling.previous_sibling(node.name()))
          {
            ++index;
          }
        path = "/" + std::string(node.name()) + "[" + std::to_string(index) + "]" + path;
      }
    return path;
  }

  inline std::string dclg_document::append_child(std::string_view parent_path,
                                                 const dclg_node& node)
  {
    auto parent = require_element(parent_path);
    if(not node.root())
      {
        throw std::invalid_argument("node has no element root");
      }
    const auto inserted = parent.append_copy(node.root());
    if(not inserted)
      {
        throw std::runtime_error("could not append child node");
      }
    dirty = true;
    ++edit_generation;
    last_error.clear();
    return path_of(inserted);
  }

  inline std::string dclg_document::prepend_child(std::string_view parent_path,
                                                  const dclg_node& node)
  {
    auto parent = require_element(parent_path);
    if(not node.root())
      {
        throw std::invalid_argument("node has no element root");
      }
    const auto inserted = parent.prepend_copy(node.root());
    if(not inserted)
      {
        throw std::runtime_error("could not prepend child node");
      }
    dirty = true;
    ++edit_generation;
    last_error.clear();
    return path_of(inserted);
  }

  inline std::string dclg_document::insert_before(std::string_view sibling_path,
                                                  const dclg_node& node)
  {
    const auto sibling = require_element(sibling_path);
    if(sibling == root() or not node.root())
      {
        throw std::invalid_argument("cannot insert beside the DocLang root");
      }
    const auto inserted = sibling.parent().insert_copy_before(node.root(), sibling);
    if(not inserted)
      {
        throw std::runtime_error("could not insert sibling node");
      }
    dirty = true;
    ++edit_generation;
    last_error.clear();
    return path_of(inserted);
  }

  inline std::string dclg_document::insert_after(std::string_view sibling_path,
                                                 const dclg_node& node)
  {
    const auto sibling = require_element(sibling_path);
    if(sibling == root() or not node.root())
      {
        throw std::invalid_argument("cannot insert beside the DocLang root");
      }
    const auto inserted = sibling.parent().insert_copy_after(node.root(), sibling);
    if(not inserted)
      {
        throw std::runtime_error("could not insert sibling node");
      }
    dirty = true;
    ++edit_generation;
    last_error.clear();
    return path_of(inserted);
  }

  inline void dclg_document::erase(std::string_view element_path)
  {
    const auto node = require_element(element_path);
    if(node == root())
      {
        throw std::invalid_argument("cannot delete the DocLang root");
      }
    if(not node.parent().remove_child(node))
      {
        throw std::runtime_error("could not delete DocLang element");
      }
    dirty = true;
    ++edit_generation;
    last_error.clear();
  }

  inline validation_report dclg_document::validate(validation_options options) const
  {
    return validate_doclang_xml(raw(), options);
  }

  inline std::tuple<bool, std::string> dclg_document::is_valid(validation_options options) const
  {
    return validate(options).is_valid();
  }

  template <typename callback_type>
  void dclg_document::iterate_elements(callback_type&& callback) const
  {
    for(pugi::xml_node node : root().children())
      {
        if(node.type() == pugi::node_element)
          {
            callback(node);
          }
      }
  }

  template <typename callback_type>
  void dclg_document::iterate_elements(std::string_view name, callback_type&& callback) const
  {
    iterate_elements([&](pugi::xml_node node) {
      if(std::string_view(node.name()) == name)
        {
          callback(node);
        }
    });
  }

  template <typename callback_type>
  void dclg_document::iterate_table_text(callback_type&& callback) const
  {
    iterate_elements("table", [&](pugi::xml_node table) { iterate_table_text(table, callback); });
  }

  template <typename callback_type>
  void dclg_document::iterate_table_text(pugi::xml_node table, callback_type&& callback) const
  {
    if(not table or std::string_view(table.name()) != "table")
      {
        return;
      }

    for(pugi::xml_node child : table.children())
      {
        if((child.type() == pugi::node_pcdata or child.type() == pugi::node_cdata)
           and not is_xml_whitespace(child.value()))
          {
            callback(table, child);
          }
      }
  }

  inline bool is_picture_like_name(std::string_view name)
  {
    return name == "picture" or name == "figure";
  }

  inline bool is_picture_text_skip_name(std::string_view name)
  {
    return name == "location" or name == "src" or name == "ldiv" or name == "marker";
  }

  template <typename callback_type>
  void iterate_picture_text_descendants(pugi::xml_node picture, pugi::xml_node node,
                                        callback_type& callback)
  {
    for(pugi::xml_node child : node.children())
      {
        if(child.type() != pugi::node_element)
          {
            continue;
          }

        const std::string_view name = child.name();
        if(is_picture_text_skip_name(name))
          {
            continue;
          }

        const std::string text = direct_text_content(child);
        if(not is_xml_whitespace(text.c_str()))
          {
            callback(picture, child);
          }

        iterate_picture_text_descendants(picture, child, callback);
      }
  }

  template <typename callback_type>
  void dclg_document::iterate_picture_text(callback_type&& callback) const
  {
    iterate_elements([&](pugi::xml_node node) {
      if(is_picture_like_name(node.name()))
        {
          iterate_picture_text(node, callback);
        }
    });
  }

  template <typename callback_type>
  void dclg_document::iterate_picture_text(pugi::xml_node picture, callback_type&& callback) const
  {
    if(not picture or not is_picture_like_name(picture.name()))
      {
        return;
      }

    iterate_picture_text_descendants(picture, picture, callback);
  }

  inline std::string join_doclang_text(std::vector<std::string> values)
  {
    std::ostringstream oss;

    bool first = true;
    for(const auto& value : values)
      {
        if(value.empty())
          {
            continue;
          }

        if(not first)
          {
            oss << "\n";
          }

        oss << value;
        first = false;
      }

    return oss.str();
  }

  inline std::string table_text_content(pugi::xml_node table)
  {
    std::vector<std::string> values;

    for(pugi::xml_node child : table.children())
      {
        if((child.type() == pugi::node_pcdata or child.type() == pugi::node_cdata)
           and not is_xml_whitespace(child.value()))
          {
            values.push_back(strip_content(child.value()));
          }
      }

    return join_doclang_text(values);
  }

  inline std::string picture_text_content(const dclg_document& doc, pugi::xml_node picture)
  {
    std::vector<std::string> values;

    doc.iterate_picture_text(picture, [&](pugi::xml_node, pugi::xml_node text_node) {
      values.push_back(strip_content(direct_text_content(text_node)));
    });

    return join_doclang_text(values);
  }

  inline std::string node_text_content(const dclg_document& doc, pugi::xml_node node)
  {
    if(node.type() == pugi::node_pcdata or node.type() == pugi::node_cdata)
      {
        return strip_content(node.value());
      }

    if(std::string_view(node.name()) == "table")
      {
        return table_text_content(node);
      }

    if(is_picture_like_name(node.name()))
      {
        return picture_text_content(doc, node);
      }

    return strip_content(direct_text_content(node));
  }

  inline std::string dclg_document::at(std::string_view xpath, std::string_view mode)
  {
    const auto lookup = resolve_doclang_path(root(), xpath);
    if(not lookup.found)
      {
        set_last_error(lookup.error);
        return "";
      }

    if(mode == "doclang")
      {
        last_error.clear();
        return serialize_node(lookup.node);
      }

    if(mode == "text")
      {
        last_error.clear();
        return node_text_content(*this, lookup.node);
      }

    if(mode == "auto")
      {
        const std::string text = node_text_content(*this, lookup.node);
        if(not text.empty() or lookup.node.type() == pugi::node_pcdata
           or lookup.node.type() == pugi::node_cdata
           or std::string_view(lookup.node.name()) == "table"
           or is_picture_like_name(lookup.node.name()))
          {
            last_error.clear();
            return text;
          }

        last_error.clear();
        return serialize_node(lookup.node);
      }

    set_last_error("unsupported DocLang access mode: " + std::string(mode));
    return "";
  }

}

#endif
