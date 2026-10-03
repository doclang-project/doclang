//-*-C++-*-

#ifndef DOCLANG_NATIVE_VIEW_H_
#define DOCLANG_NATIVE_VIEW_H_

#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <pugixml.hpp>

#include <doclang/dclg_document.h>

namespace doclang::native
{

  class element_view
  {
  public:

    element_view() = default;
    explicit element_view(pugi::xml_node value) : node_value(value)
    {
    }

    bool valid() const
    {
      return static_cast<bool>(node_value);
    }

    std::string name() const
    {
      return node_value.name();
    }
    std::string text_content() const
    {
      return node_value.child_value();
    }

    std::optional<unsigned> heading_level() const;
    std::vector<float> location() const;

    pugi::xml_node node() const
    {
      return node_value;
    }

  private:

    pugi::xml_node node_value;
  };

  class document_view
  {
  public:

    document_view() = default;
    explicit document_view(std::shared_ptr<const dclg_document> doc) : doc_ptr(std::move(doc))
    {
    }

    bool valid() const
    {
      return doc_ptr != nullptr and doc_ptr->root();
    }

    std::vector<element_view> body_elements() const;
    std::vector<element_view> elements_by_name(std::string_view name) const;
    std::vector<element_view> text_like_elements() const;
    std::vector<element_view> table_elements() const;

  private:

    bool is_text_like(pugi::xml_node node) const;

  private:

    std::shared_ptr<const dclg_document> doc_ptr;
  };

  inline std::optional<unsigned> element_view::heading_level() const
  {
    if(not node_value or std::string_view(node_value.name()) != "heading")
      {
        return std::nullopt;
      }

    pugi::xml_attribute attr = node_value.attribute("level");
    if(not attr)
      {
        return std::nullopt;
      }

    return attr.as_uint();
  }

  inline std::vector<float> element_view::location() const
  {
    std::vector<float> result;

    if(not node_value)
      {
        return result;
      }

    for(pugi::xml_node loc : node_value.children("location"))
      {
        pugi::xml_attribute attr = loc.attribute("value");
        if(attr)
          {
            result.push_back(attr.as_float());
          }
      }

    return result;
  }

  inline bool document_view::is_text_like(pugi::xml_node node) const
  {
    const std::string_view name = node.name();

    return (name == "text" or name == "heading" or name == "page_header" or name == "page_footer"
            or name == "footnote" or name == "caption" or name == "list" or name == "formula"
            or name == "equation" or name == "code");
  }

  inline std::vector<element_view> document_view::body_elements() const
  {
    std::vector<element_view> result;

    if(not valid())
      {
        return result;
      }

    doc_ptr->iterate_elements([&](pugi::xml_node node) { result.emplace_back(node); });

    return result;
  }

  inline std::vector<element_view> document_view::elements_by_name(std::string_view name) const
  {
    std::vector<element_view> result;

    if(not valid())
      {
        return result;
      }

    doc_ptr->iterate_elements(name, [&](pugi::xml_node node) { result.emplace_back(node); });

    return result;
  }

  inline std::vector<element_view> document_view::text_like_elements() const
  {
    std::vector<element_view> result;

    if(not valid())
      {
        return result;
      }

    doc_ptr->iterate_elements([&](pugi::xml_node node) {
      if(is_text_like(node))
        {
          result.emplace_back(node);
        }
    });

    return result;
  }

  inline std::vector<element_view> document_view::table_elements() const
  {
    return elements_by_name("table");
  }

}

#endif
