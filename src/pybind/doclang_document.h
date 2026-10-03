//-*-C++-*-

#ifndef DOCLANG_PYBIND_DOCUMENT_H_
#define DOCLANG_PYBIND_DOCUMENT_H_

#include <array>
#include <cmath>
#include <cstddef>
#include <exception>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <doclang/dclg_document.h>

namespace doclang::binding
{

  class DoclangDocument
  {
  public:

    using bounding_box_type = std::pair<std::pair<float, float>, std::pair<float, float>>;

    class Iterator
    {
    public:

      Iterator(std::shared_ptr<doclang::native::dclg_document> value, pugi::xml_node parent,
               std::string parent_xpath, int page, bool include_xpath,
               std::optional<int> page_filter = std::nullopt);

      pybind11::object next();

    private:

      pybind11::object next_list_item();

      std::shared_ptr<doclang::native::dclg_document> doc;
      pugi::xml_node current;
      std::string parent_xpath;
      std::map<std::string, std::size_t> positions;
      int current_page;
      bool with_xpath;
      bool root_scope;
      std::optional<int> only_page;
      pugi::xml_node list_cursor;
      std::string list_xpath;
      std::optional<int> list_page;
      std::size_t list_index;
      std::size_t source_generation;
    };

    DoclangDocument();
    explicit DoclangDocument(const std::string& dclg);
    explicit DoclangDocument(std::shared_ptr<doclang::native::dclg_document> value);

    virtual ~DoclangDocument();

    virtual bool read_xml(const std::string& dclg);

    const native::dclg_document& native_document() const
    {
      return *dclg_doc;
    }

    static DoclangDocument empty();
    std::string append_child(const std::string& parent_xpath, const native::dclg_node& node);
    std::string prepend_child(const std::string& parent_xpath, const native::dclg_node& node);
    std::string insert_before(const std::string& sibling_xpath, const native::dclg_node& node);
    std::string insert_after(const std::string& sibling_xpath, const native::dclg_node& node);
    void delete_at(const std::string& xpath);
    native::validation_report validate(bool allow_empty_namespace = false, bool xsd_only = false,
                                       bool schematron_only = false) const;
    std::tuple<bool, std::string> is_valid(bool allow_empty_namespace = false,
                                           bool xsd_only = false,
                                           bool schematron_only = false) const;

    bool valid() const;
    std::optional<native::doclang_version> version() const;
    std::string xml() const;
    std::string last_error() const;
    std::string at(const std::string& xpath, const std::string& mode = "auto");
    std::optional<bounding_box_type> bounding_box(const std::string& xpath) const;
    std::optional<std::size_t> page_number(const std::string& xpath) const;
    Iterator iterate_items(const std::optional<std::string>& xpath = std::nullopt) const;
    Iterator iterate_items_on_page(int page_no) const;
    Iterator iter() const;

  private:

    std::shared_ptr<doclang::native::dclg_document> dclg_doc;
  };

  namespace detail
  {
    inline std::optional<std::array<float, 4>> doclang_location_values(pugi::xml_node node,
                                                                       std::string* error = nullptr)
    {
      std::array<float, 4> values{};
      std::size_t count = 0;
      for(pugi::xml_node location : node.children("location"))
        {
          const pugi::xml_attribute attribute = location.attribute("value");
          if(count == values.size() or not attribute)
            {
              if(error)
                {
                  *error = "invalid DocLang bounding box at: ";
                }
              return std::nullopt;
            }

          const std::string token = attribute.value();
          std::size_t parsed = 0;
          try
            {
              values[count] = std::stof(token, &parsed);
            }
          catch(const std::exception&)
            {
              if(error)
                {
                  *error = "invalid DocLang bounding box at: ";
                }
              return std::nullopt;
            }

          if(parsed != token.size() or not std::isfinite(values[count]) or values[count] < 0
             or values[count] > 1000)
            {
              if(error)
                {
                  *error = "invalid DocLang bounding box at: ";
                }
              return std::nullopt;
            }
          count += 1;
        }

      if(count != values.size())
        {
          if(error)
            {
              *error = "DocLang bounding box requires four locations at: ";
            }
          return std::nullopt;
        }

      return values;
    }

    inline int doclang_page_for_node(pugi::xml_node root, pugi::xml_node node)
    {
      if(not root or node == root)
        {
          return 1;
        }

      while(node.parent() != root)
        {
          node = node.parent();
        }

      int page = 1;
      for(pugi::xml_node sibling = node.previous_sibling(); sibling;
          sibling = sibling.previous_sibling())
        {
          if(sibling.type() == pugi::node_element
             and std::string_view(sibling.name()) == "page_break")
            {
              page += 1;
            }
        }
      return page;
    }

    inline std::string doclang_node_xpath(pugi::xml_node node)
    {
      std::string path;
      for(; node and node.type() == pugi::node_element; node = node.parent())
        {
          std::size_t index = 1;
          for(pugi::xml_node sibling = node.previous_sibling(node.name()); sibling;
              sibling = sibling.previous_sibling(node.name()))
            {
              index += 1;
            }
          path = "/" + std::string(node.name()) + "[" + std::to_string(index) + "]" + path;
        }
      return path;
    }

    inline void append_list_item_text(pugi::xml_node node, std::string& text)
    {
      if(node.type() == pugi::node_pcdata or node.type() == pugi::node_cdata)
        {
          text += node.value();
          return;
        }

      if(node.type() != pugi::node_element or std::string_view(node.name()) == "location"
         or std::string_view(node.name()) == "marker")
        {
          return;
        }

      for(pugi::xml_node child : node.children())
        {
          append_list_item_text(child, text);
        }
    }
  }

  inline DoclangDocument::Iterator::Iterator(std::shared_ptr<doclang::native::dclg_document> value,
                                             pugi::xml_node parent, std::string parent_xpath,
                                             int page, bool include_xpath,
                                             std::optional<int> page_filter)
      : doc(std::move(value)), current(parent.first_child()), parent_xpath(std::move(parent_xpath)),
        current_page(page), with_xpath(include_xpath), root_scope(parent == doc->root()),
        only_page(page_filter), list_index(0), source_generation(doc->generation())
  {
    if(with_xpath and std::string_view(parent.name()) == "list")
      {
        list_cursor = parent.child("ldiv");
        if(list_cursor)
          {
            list_xpath = this->parent_xpath;
            list_page = page;
            current = pugi::xml_node();
          }
      }
  }

  inline pybind11::object DoclangDocument::Iterator::next_list_item()
  {
    const pugi::xml_node delimiter = list_cursor;
    const pugi::xml_node next_delimiter = delimiter.next_sibling("ldiv");
    list_cursor = next_delimiter;
    list_index += 1;

    pugi::xml_document fragment;
    pugi::xml_node item_node = fragment.append_child("list_item");
    std::string text;
    for(pugi::xml_node node = delimiter; node and node != next_delimiter;
        node = node.next_sibling())
      {
        item_node.append_copy(node);
        detail::append_list_item_text(node, text);
      }

    pybind11::dict item;
    item["name"] = "list_item";
    item["xml"] = doclang::native::serialize_node(item_node);
    item["text"] = doclang::native::strip_content(text);

    std::optional<std::array<int, 4>> bbox;
    auto values = detail::doclang_location_values(item_node);
    if(not values)
      {
        values = detail::doclang_location_values(delimiter);
      }
    if(values)
      {
        std::array<int, 4> rounded{};
        for(std::size_t i = 0; i < rounded.size(); ++i)
          {
            rounded[i] = static_cast<int>(std::lround((*values)[i]));
          }
        bbox = rounded;
      }

    const std::string xpath = list_xpath + "/ldiv[" + std::to_string(list_index) + "]";
    return pybind11::make_tuple(xpath, item, list_page, bbox);
  }

  inline pybind11::object DoclangDocument::Iterator::next()
  {
    if(source_generation != doc->generation())
      {
        throw std::runtime_error("DocLang document changed during iteration");
      }
    while(current or list_cursor)
      {
        if(list_cursor)
          {
            return next_list_item();
          }

        if(root_scope and only_page and current_page > *only_page)
          {
            break;
          }

        const pugi::xml_node node = current;
        current = current.next_sibling();
        if(node.type() != pugi::node_element)
          {
            continue;
          }

        const std::string name = node.name();
        const std::size_t index = ++positions[name];
        std::optional<int> page_no = current_page;
        if(name == "page_break")
          {
            page_no = std::nullopt;
            if(root_scope)
              {
                current_page += 1;
              }
          }
        if(only_page and page_no != only_page)
          {
            continue;
          }

        const std::string xpath = parent_xpath + "/" + name + "[" + std::to_string(index) + "]";
        if(with_xpath and name == "list")
          {
            list_cursor = node.child("ldiv");
            if(list_cursor)
              {
                list_xpath = xpath;
                list_page = page_no;
                list_index = 0;
                continue;
              }
          }

        pybind11::dict item;
        item["name"] = name;
        item["xml"] = doclang::native::serialize_node(node);
        item["text"] = doclang::native::node_text_content(*doc, node);
        if(not with_xpath)
          {
            return item;
          }

        std::optional<std::array<int, 4>> bbox;
        if(const auto values = detail::doclang_location_values(node))
          {
            std::array<int, 4> rounded{};
            for(std::size_t i = 0; i < rounded.size(); ++i)
              {
                rounded[i] = static_cast<int>(std::lround((*values)[i]));
              }
            bbox = rounded;
          }
        return pybind11::make_tuple(xpath, item, page_no, bbox);
      }

    throw pybind11::stop_iteration();
  }

  inline DoclangDocument::DoclangDocument()
      : dclg_doc(std::make_shared<doclang::native::dclg_document>())
  {
  }

  inline DoclangDocument::DoclangDocument(const std::string& dclg) : DoclangDocument()
  {
    read_xml(dclg);
  }

  inline DoclangDocument::DoclangDocument(std::shared_ptr<doclang::native::dclg_document> value)
      : dclg_doc(std::move(value))
  {
  }

  inline DoclangDocument::~DoclangDocument()
  {
  }

  inline bool DoclangDocument::read_xml(const std::string& dclg)
  {
    return dclg_doc->read(dclg);
  }

  inline DoclangDocument DoclangDocument::empty()
  {
    return DoclangDocument(
        std::make_shared<native::dclg_document>(native::dclg_document::create_empty()));
  }

  inline std::string DoclangDocument::append_child(const std::string& parent_xpath,
                                                   const native::dclg_node& node)
  {
    return dclg_doc->append_child(parent_xpath, node);
  }

  inline std::string DoclangDocument::prepend_child(const std::string& parent_xpath,
                                                    const native::dclg_node& node)
  {
    return dclg_doc->prepend_child(parent_xpath, node);
  }

  inline std::string DoclangDocument::insert_before(const std::string& sibling_xpath,
                                                    const native::dclg_node& node)
  {
    return dclg_doc->insert_before(sibling_xpath, node);
  }

  inline std::string DoclangDocument::insert_after(const std::string& sibling_xpath,
                                                   const native::dclg_node& node)
  {
    return dclg_doc->insert_after(sibling_xpath, node);
  }

  inline void DoclangDocument::delete_at(const std::string& xpath)
  {
    dclg_doc->erase(xpath);
  }

  inline native::validation_report
  DoclangDocument::validate(bool allow_empty_namespace, bool xsd_only, bool schematron_only) const
  {
    return dclg_doc->validate({ allow_empty_namespace, xsd_only, schematron_only });
  }

  inline std::tuple<bool, std::string>
  DoclangDocument::is_valid(bool allow_empty_namespace, bool xsd_only, bool schematron_only) const
  {
    return dclg_doc->is_valid({ allow_empty_namespace, xsd_only, schematron_only });
  }

  inline bool DoclangDocument::valid() const
  {
    return dclg_doc->valid();
  }

  inline std::optional<native::doclang_version> DoclangDocument::version() const
  {
    return dclg_doc->version();
  }

  inline std::string DoclangDocument::xml() const
  {
    return dclg_doc->raw();
  }

  inline std::string DoclangDocument::last_error() const
  {
    return dclg_doc->get_last_error();
  }

  inline std::string DoclangDocument::at(const std::string& xpath, const std::string& mode)
  {
    return dclg_doc->at(xpath, mode);
  }

  inline std::optional<DoclangDocument::bounding_box_type>
  DoclangDocument::bounding_box(const std::string& xpath) const
  {
    const auto lookup = doclang::native::resolve_doclang_path(dclg_doc->root(), xpath);
    if(not lookup.found)
      {
        dclg_doc->set_last_error(lookup.error);
        return std::nullopt;
      }

    std::string error;
    const auto values = detail::doclang_location_values(lookup.node, &error);
    if(not values)
      {
        dclg_doc->set_last_error(error + xpath);
        return std::nullopt;
      }

    dclg_doc->set_last_error("");
    return bounding_box_type{ { (*values)[0], (*values)[1] }, { (*values)[2], (*values)[3] } };
  }

  inline std::optional<std::size_t> DoclangDocument::page_number(const std::string& xpath) const
  {
    const pugi::xml_node root = dclg_doc->root();
    const auto lookup = doclang::native::resolve_doclang_path(root, xpath);
    if(not lookup.found)
      {
        dclg_doc->set_last_error(lookup.error);
        return std::nullopt;
      }

    dclg_doc->set_last_error("");
    return detail::doclang_page_for_node(root, lookup.node);
  }

  inline DoclangDocument::Iterator
  DoclangDocument::iterate_items(const std::optional<std::string>& xpath) const
  {
    const pugi::xml_node root = dclg_doc->root();
    pugi::xml_node parent = root;
    if(xpath)
      {
        const auto lookup = doclang::native::resolve_doclang_path(root, *xpath);
        if(not lookup.found)
          {
            throw pybind11::value_error(lookup.error);
          }
        parent = lookup.node;
      }

    return Iterator(dclg_doc, parent, detail::doclang_node_xpath(parent),
                    detail::doclang_page_for_node(root, parent), true);
  }

  inline DoclangDocument::Iterator DoclangDocument::iterate_items_on_page(int page_no) const
  {
    if(page_no < 1)
      {
        throw pybind11::value_error("page_no must be at least 1");
      }

    const pugi::xml_node root = dclg_doc->root();
    return Iterator(dclg_doc, root, detail::doclang_node_xpath(root), 1, true, page_no);
  }

  inline DoclangDocument::Iterator DoclangDocument::iter() const
  {
    const pugi::xml_node root = dclg_doc->root();
    return Iterator(dclg_doc, root, detail::doclang_node_xpath(root), 1, false);
  }

}

#endif
