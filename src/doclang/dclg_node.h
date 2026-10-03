#ifndef DOCLANG_NATIVE_DCLG_NODE_H_
#define DOCLANG_NATIVE_DCLG_NODE_H_

#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

#include <pugixml.hpp>

#include <doclang/content.h>
#include <doclang/vocabulary.h>

namespace doclang::native
{
  class dclg_node
  {
  public:

    dclg_node();
    dclg_node(const dclg_node& other);
    dclg_node& operator=(const dclg_node& other);
    dclg_node(dclg_node&&);
    dclg_node& operator=(dclg_node&&);
    virtual ~dclg_node();
    static dclg_node element(std::string_view name);
    static dclg_node element(element_tag tag);
    static dclg_node from_xml(std::string_view fragment);
    pugi::xml_node root() const;
    std::string name() const;
    std::string to_xml() const;
    void set_attribute(std::string_view name, std::string_view value);
    void set_attribute(attribute_name name, std::string_view value);
    void remove_attribute(std::string_view name);
    void remove_attribute(attribute_name name);
    void append_text(std::string_view value);
    void append_child(const dclg_node& child);
    void prepend_child(const dclg_node& child);
    void insert_before(std::string_view child_path, const dclg_node& sibling);
    void insert_after(std::string_view child_path, const dclg_node& sibling);

  protected:

    pugi::xml_document document;

  private:

    void insert_relative(std::string_view path, const dclg_node& sibling, bool before);
  };

  inline dclg_node::dclg_node() = default;

  inline dclg_node::dclg_node(const dclg_node& other)
  {
    if(other.root())
      {
        document.append_copy(other.root());
      }
  }

  inline dclg_node& dclg_node::operator=(const dclg_node& other)
  {
    if(this != &other)
      {
        document.reset();
        if(other.root())
          {
            document.append_copy(other.root());
          }
      }
    return *this;
  }

  inline dclg_node::dclg_node(dclg_node&&) = default;

  inline dclg_node& dclg_node::operator=(dclg_node&&) = default;

  inline dclg_node::~dclg_node() = default;

  inline dclg_node dclg_node::element(std::string_view name)
  {
    if(name.empty() or name == "doclang"
       or name.find_first_of("<>/ \t\r\n") != std::string_view::npos)
      {
        throw std::invalid_argument("invalid DocLang element name");
      }

    dclg_node result;
    if(not result.document.append_child(std::string(name).c_str()))
      {
        throw std::invalid_argument("invalid DocLang element name");
      }
    return result;
  }

  inline dclg_node dclg_node::element(element_tag tag)
  {
    return element(to_string_view(tag));
  }

  inline dclg_node dclg_node::from_xml(std::string_view fragment)
  {
    pugi::xml_document parsed;
    const auto status = parsed.load_buffer(fragment.data(), fragment.size(),
                                           pugi::parse_default | pugi::parse_ws_pcdata);
    if(not status or not parsed.document_element() or parsed.document_element().next_sibling()
       or std::string_view(parsed.document_element().name()) == "doclang")
      {
        throw std::invalid_argument("expected one DocLang element fragment");
      }
    dclg_node result;
    result.document.append_copy(parsed.document_element());
    return result;
  }

  inline pugi::xml_node dclg_node::root() const
  {
    return document.document_element();
  }

  inline std::string dclg_node::name() const
  {
    return root() ? root().name() : "";
  }

  inline std::string dclg_node::to_xml() const
  {
    return root() ? serialize_node(root()) : "";
  }

  inline void dclg_node::set_attribute(std::string_view name, std::string_view value)
  {
    if(not root() or name.empty())
      {
        throw std::invalid_argument("node has no element root");
      }
    auto attribute = root().attribute(std::string(name).c_str());
    if(not attribute)
      {
        attribute = root().append_attribute(std::string(name).c_str());
      }
    if(not attribute or not attribute.set_value(std::string(value).c_str()))
      {
        throw std::invalid_argument("invalid DocLang attribute");
      }
  }

  inline void dclg_node::set_attribute(attribute_name name, std::string_view value)
  {
    set_attribute(to_string_view(name), value);
  }

  inline void dclg_node::remove_attribute(std::string_view name)
  {
    if(not root())
      {
        throw std::invalid_argument("node has no element root");
      }
    root().remove_attribute(std::string(name).c_str());
  }

  inline void dclg_node::remove_attribute(attribute_name name)
  {
    remove_attribute(to_string_view(name));
  }

  inline void dclg_node::append_text(std::string_view value)
  {
    if(not root())
      {
        throw std::invalid_argument("node has no element root");
      }
    auto text = root().append_child(pugi::node_pcdata);
    if(not text or not text.set_value(std::string(value).c_str()))
      {
        throw std::runtime_error("could not append text");
      }
  }

  inline void dclg_node::append_child(const dclg_node& child)
  {
    if(not root() or not child.root() or not root().append_copy(child.root()))
      {
        throw std::invalid_argument("could not append child node");
      }
  }

  inline void dclg_node::prepend_child(const dclg_node& child)
  {
    if(not root() or not child.root() or not root().prepend_copy(child.root()))
      {
        throw std::invalid_argument("could not prepend child node");
      }
  }

  inline void dclg_node::insert_before(std::string_view child_path, const dclg_node& sibling)
  {
    insert_relative(child_path, sibling, true);
  }

  inline void dclg_node::insert_after(std::string_view child_path, const dclg_node& sibling)
  {
    insert_relative(child_path, sibling, false);
  }

  inline void dclg_node::insert_relative(std::string_view path, const dclg_node& sibling,
                                         bool before)
  {
    const auto lookup = resolve_doclang_path(root(), path);
    if(not lookup.found)
      {
        throw std::out_of_range(lookup.error);
      }
    if(lookup.node == root() or lookup.node.type() != pugi::node_element or not sibling.root())
      {
        throw std::invalid_argument("sibling path must select a child element");
      }
    const auto inserted = before
                              ? lookup.node.parent().insert_copy_before(sibling.root(), lookup.node)
                              : lookup.node.parent().insert_copy_after(sibling.root(), lookup.node);
    if(not inserted)
      {
        throw std::runtime_error("could not insert sibling node");
      }
  }
}

#endif
