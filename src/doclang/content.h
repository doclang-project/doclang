//-*-C++-*-

#ifndef DOCLANG_NATIVE_CONTENT_H_
#define DOCLANG_NATIVE_CONTENT_H_

#include <sstream>
#include <optional>
#include <utility>
#include <string>
#include <string_view>
#include <vector>

#include <pugixml.hpp>

#include <doclang/vocabulary.h>

namespace doclang::native
{

  enum class content_kind
  {
    element,
    text,
    cdata,
    other
  };

  struct content_node
  {
    content_kind kind;
    std::string_view name;
    std::string_view value;
    pugi::xml_node node;
  };

  struct path_lookup_result
  {
    bool found = false;
    pugi::xml_node node;
    std::string error;
  };

  inline bool is_xml_whitespace(const char* value)
  {
    if(value == nullptr)
      {
        return true;
      }

    for(const char* ptr = value; *ptr != '\0'; ptr++)
      {
        const char c = *ptr;
        if(c != ' ' and c != '\n' and c != '\r' and c != '\t')
          {
            return false;
          }
      }

    return true;
  }

  inline content_kind to_content_kind(pugi::xml_node_type type)
  {
    switch(type)
      {
      case pugi::node_element:
        return content_kind::element;

      case pugi::node_pcdata:
        return content_kind::text;

      case pugi::node_cdata:
        return content_kind::cdata;

      default:
        return content_kind::other;
      }
  }

  inline std::vector<content_node> child_content(pugi::xml_node parent,
                                                 bool include_whitespace_text = false)
  {
    std::vector<content_node> result;

    for(pugi::xml_node child : parent.children())
      {
        const content_kind kind = to_content_kind(child.type());

        if((kind == content_kind::text or kind == content_kind::cdata)
           and not include_whitespace_text and is_xml_whitespace(child.value()))
          {
            continue;
          }

        result.push_back({ kind, child.name(), child.value(), child });
      }

    return result;
  }

  inline std::string serialize_xml(const pugi::xml_document& doc)
  {
    std::ostringstream oss;
    doc.save(oss);
    return oss.str();
  }

  inline std::string serialize_node(pugi::xml_node node)
  {
    if(node.type() == pugi::node_pcdata or node.type() == pugi::node_cdata)
      {
        return node.value();
      }

    std::ostringstream oss;
    node.print(oss);
    return oss.str();
  }

  inline std::string direct_text_content(pugi::xml_node parent)
  {
    std::ostringstream oss;

    for(pugi::xml_node child : parent.children())
      {
        if(child.type() == pugi::node_pcdata or child.type() == pugi::node_cdata)
          {
            oss << child.value();
          }
      }

    return oss.str();
  }

  inline std::string strip_content(std::string value)
  {
    const auto first = value.find_first_not_of(" \n\r\t");
    if(first == std::string::npos)
      {
        return "";
      }

    const auto last = value.find_last_not_of(" \n\r\t");
    return value.substr(first, last - first + 1);
  }

  inline bool parse_indexed_step(std::string_view step, std::string& name, std::size_t& index,
                                 bool& is_text_step)
  {
    is_text_step = false;
    name.clear();
    index = 0;

    constexpr std::string_view text_prefix = "text()[";
    if(step.rfind(text_prefix, 0) == 0 and step.back() == ']')
      {
        is_text_step = true;
        name = "text()";
        step.remove_prefix(text_prefix.size());
        step.remove_suffix(1);
      }
    else
      {
        const auto open = step.find('[');
        if(open == std::string_view::npos or step.back() != ']' or open == 0)
          {
            return false;
          }

        name = std::string(step.substr(0, open));
        step.remove_prefix(open + 1);
        step.remove_suffix(1);
      }

    if(step.empty())
      {
        return false;
      }

    for(char c : step)
      {
        if(c < '0' or c > '9')
          {
            return false;
          }

        index = 10 * index + static_cast<std::size_t>(c - '0');
      }

    return index > 0;
  }

  inline path_lookup_result resolve_doclang_path(pugi::xml_node root, std::string_view path)
  {
    path_lookup_result result;

    if(not root)
      {
        result.error = "DocLang XML does not contain root <doclang>";
        return result;
      }

    if(path.empty() or path.front() != '/')
      {
        result.error = "DocLang path must be absolute: " + std::string(path);
        return result;
      }

    pugi::xml_node current = root;
    std::size_t pos = 1;
    bool first_step = true;

    while(pos <= path.size())
      {
        const auto next = path.find('/', pos);
        const std::string_view step
            = next == std::string_view::npos ? path.substr(pos) : path.substr(pos, next - pos);

        if(step.empty())
          {
            result.error = "empty DocLang path step: " + std::string(path);
            return result;
          }

        std::string name;
        std::size_t index = 0;
        bool is_text_step = false;
        if(not parse_indexed_step(step, name, index, is_text_step))
          {
            result.error = "unsupported DocLang path step: " + std::string(step);
            return result;
          }

        if(is_text_step)
          {
            std::size_t count = 0;
            for(pugi::xml_node child : current.children())
              {
                if((child.type() == pugi::node_pcdata or child.type() == pugi::node_cdata)
                   and not is_xml_whitespace(child.value()))
                  {
                    count += 1;
                    if(count == index)
                      {
                        current = child;
                        break;
                      }
                  }
              }

            if(count < index)
              {
                result.error = "DocLang path not found: " + std::string(path);
                return result;
              }
          }
        else if(first_step and name == root.name() and index == 1)
          {
            current = root;
          }
        else
          {
            std::size_t count = 0;
            for(pugi::xml_node child : current.children(name.c_str()))
              {
                count += 1;
                if(count == index)
                  {
                    current = child;
                    break;
                  }
              }

            if(count < index)
              {
                result.error = "DocLang path not found: " + std::string(path);
                return result;
              }
          }

        if(next == std::string_view::npos)
          {
            break;
          }

        pos = next + 1;
        first_step = false;
      }

    result.found = true;
    result.node = current;
    return result;
  }

  inline bool is_table_cell_marker(std::string_view name)
  {
    const auto token = otsl_token_from_string(name);
    return token.has_value() and token != otsl_token::nl and to_string_view(token.value()) == name;
  }

  inline std::optional<std::pair<std::size_t, std::size_t>>
  table_coordinates(pugi::xml_node root, std::string_view xpath)
  {
    const auto lookup = resolve_doclang_path(root, xpath);
    if(!lookup.found)
      {
        return std::nullopt;
      }

    pugi::xml_node target = lookup.node;
    pugi::xml_node table = target;
    while(table and std::string_view(table.name()) != "table")
      {
        table = table.parent();
      }
    if(!table or target == table)
      {
        return std::nullopt;
      }

    while(target.parent() != table)
      {
        target = target.parent();
      }
    std::size_t row = 0;
    std::size_t column = 0;
    bool in_cell = false;
    for(pugi::xml_node child : table.children())
      {
        const std::string_view name = child.name();
        if(name == "nl")
          {
            if(child == target)
              {
                return std::nullopt;
              }
            ++row;
            column = 0;
            in_cell = false;
          }
        else if(is_table_cell_marker(name))
          {
            if(in_cell)
              {
                ++column;
              }
            in_cell = true;
          }

        if(child == target)
          {
            if(!in_cell)
              {
                return std::nullopt;
              }
            return std::pair{ row, column };
          }
      }
    return std::nullopt;
  }

}

#endif
