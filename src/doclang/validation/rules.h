#ifndef DOCLANG_NATIVE_VALIDATION_RULES_H_
#define DOCLANG_NATIVE_VALIDATION_RULES_H_

#include <cmath>
#include <cstdlib>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include <pugixml.hpp>

#include <doclang/content.h>

namespace doclang::native
{
  struct validation_issue
  {
    std::string assertion;
    std::string location;
    std::string message;
  };

  namespace validation_detail
  {
    constexpr std::string_view doclang_namespace = "https://www.doclang.ai/ns/v0";

    inline std::string_view local_name(pugi::xml_node node)
    {
      const std::string_view name(node.name());
      const auto colon = name.find(':');
      return colon == std::string_view::npos ? name : name.substr(colon + 1);
    }

    inline std::string namespace_uri(pugi::xml_node node)
    {
      const std::string_view name(node.name());
      const auto colon = name.find(':');
      const std::string attribute = colon == std::string_view::npos
                                        ? "xmlns"
                                        : "xmlns:" + std::string(name.substr(0, colon));
      for(pugi::xml_node ancestor = node; ancestor; ancestor = ancestor.parent())
        {
          if(const auto declaration = ancestor.attribute(attribute.c_str()))
            {
              return declaration.value();
            }
        }
      return "";
    }

    inline bool named(pugi::xml_node node, std::string_view name, bool accept_empty_namespace)
    {
      if(node.type() != pugi::node_element or local_name(node) != name)
        {
          return false;
        }
      const std::string uri = namespace_uri(node);
      return uri == doclang_namespace or (accept_empty_namespace and uri.empty());
    }

    inline bool is_head(pugi::xml_node node, bool accept_empty_namespace)
    {
      for(const std::string_view name : { "label", "thread", "xref", "href", "layer", "location",
                                          "caption", "description", "summary", "custom" })
        {
          if(named(node, name, accept_empty_namespace))
            {
              return true;
            }
        }
      return false;
    }

    inline bool is_cell(pugi::xml_node node, bool accept_empty_namespace)
    {
      return node.type() == pugi::node_element
             and (namespace_uri(node) == doclang_namespace
                  or (accept_empty_namespace and namespace_uri(node).empty()))
             and is_table_cell_marker(local_name(node));
    }

    inline pugi::xml_node first_child(pugi::xml_node parent, std::string_view name,
                                      bool accept_empty_namespace)
    {
      for(pugi::xml_node child : parent.children())
        {
          if(named(child, name, accept_empty_namespace))
            {
              return child;
            }
        }
      return {};
    }

    inline bool has_ancestor(pugi::xml_node node, std::string_view name,
                             bool accept_empty_namespace)
    {
      for(node = node.parent(); node; node = node.parent())
        {
          if(named(node, name, accept_empty_namespace))
            {
              return true;
            }
        }
      return false;
    }

    inline std::string xpath(pugi::xml_node node)
    {
      std::string path;
      for(; node and node.type() == pugi::node_element; node = node.parent())
        {
          std::size_t index = 1;
          for(pugi::xml_node sibling = node.previous_sibling(); sibling;
              sibling = sibling.previous_sibling())
            {
              if(local_name(sibling) == local_name(node)
                 and namespace_uri(sibling) == namespace_uri(node))
                {
                  ++index;
                }
            }
          path = "/" + std::string(local_name(node)) + "[" + std::to_string(index) + "]" + path;
        }
      return path;
    }

    inline void add(std::vector<validation_issue>& issues, std::string_view assertion,
                    pugi::xml_node node, std::string_view message)
    {
      issues.push_back({ std::string(assertion), xpath(node), std::string(message) });
    }

    inline std::vector<pugi::xml_node> descendants(pugi::xml_node root)
    {
      std::vector<pugi::xml_node> result;
      if(root.type() != pugi::node_element)
        {
          return result;
        }
      result.push_back(root);
      for(std::size_t i = 0; i < result.size(); ++i)
        {
          for(pugi::xml_node child : result[i].children())
            {
              if(child.type() == pugi::node_element)
                {
                  result.push_back(child);
                }
            }
        }
      return result;
    }

    inline pugi::xml_node first_body_element(pugi::xml_node parent, bool accept_empty_namespace)
    {
      for(pugi::xml_node child : parent.children())
        {
          if(child.type() == pugi::node_element and not is_head(child, accept_empty_namespace))
            {
              return child;
            }
        }
      return {};
    }

    inline bool text_before_first_header(pugi::xml_node first, pugi::xml_node stop,
                                         bool accept_empty_namespace)
    {
      bool text_seen = false;
      for(pugi::xml_node node = first; node and node != stop; node = node.next_sibling())
        {
          if((node.type() == pugi::node_pcdata or node.type() == pugi::node_cdata)
             and not is_xml_whitespace(node.value()))
            {
              text_seen = true;
            }
          if(is_head(node, accept_empty_namespace))
            {
              return text_seen;
            }
        }
      return false;
    }

    inline double number(const char* value)
    {
      if(value == nullptr or *value == '\0')
        {
          return std::numeric_limits<double>::quiet_NaN();
        }
      char* end = nullptr;
      const double parsed = std::strtod(value, &end);
      while(*end == ' ' or *end == '\n' or *end == '\r' or *end == '\t')
        {
          ++end;
        }
      return end != value and * end == '\0' ? parsed : std::numeric_limits<double>::quiet_NaN();
    }

    inline double default_limit(pugi::xml_node root, bool x_axis, bool accept_empty_namespace)
    {
      const auto head = first_child(root, "head", accept_empty_namespace);
      const auto resolution = first_child(head, "default_resolution", accept_empty_namespace);
      const auto attribute = resolution.attribute(x_axis ? "width" : "height");
      return attribute ? number(attribute.value()) : 512.0;
    }

    inline double coordinate_resolution(pugi::xml_node location, pugi::xml_node root, bool x_axis,
                                        bool accept_empty_namespace)
    {
      const auto attribute = location.attribute("resolution");
      return attribute ? number(attribute.value())
                       : default_limit(root, x_axis, accept_empty_namespace);
    }

    inline std::size_t own_key_count(pugi::xml_node field_item, bool accept_empty_namespace)
    {
      std::size_t count = 0;
      std::vector<pugi::xml_node> pending{ field_item };
      while(not pending.empty())
        {
          const pugi::xml_node parent = pending.back();
          pending.pop_back();
          for(pugi::xml_node child : parent.children())
            {
              if(child.type() != pugi::node_element
                 or named(child, "field_item", accept_empty_namespace))
                {
                  continue;
                }
              if(named(child, "key", accept_empty_namespace))
                {
                  ++count;
                }
              pending.push_back(child);
            }
        }
      return count;
    }

    inline std::string thread_host(pugi::xml_node thread, bool accept_empty_namespace)
    {
      const pugi::xml_node parent = thread.parent();
      if(named(parent, "list", accept_empty_namespace))
        {
          for(pugi::xml_node previous = thread.previous_sibling(); previous;
              previous = previous.previous_sibling())
            {
              if(named(previous, "ldiv", accept_empty_namespace))
                {
                  return "list-item";
                }
            }
          return "list";
        }
      if(named(parent, "table", accept_empty_namespace)
         or named(parent, "index", accept_empty_namespace))
        {
          for(pugi::xml_node previous = thread.previous_sibling(); previous;
              previous = previous.previous_sibling())
            {
              if(is_cell(previous, accept_empty_namespace))
                {
                  return "table-cell";
                }
            }
        }
      return std::string(local_name(parent));
    }

    inline pugi::xml_node previous_element(pugi::xml_node node)
    {
      for(node = node.previous_sibling(); node; node = node.previous_sibling())
        {
          if(node.type() == pugi::node_element)
            {
              return node;
            }
        }
      return {};
    }

    inline pugi::xml_node next_element(pugi::xml_node node)
    {
      for(node = node.next_sibling(); node; node = node.next_sibling())
        {
          if(node.type() == pugi::node_element)
            {
              return node;
            }
        }
      return {};
    }

    inline double timestamp_ms(pugi::xml_node seconds, bool accept_empty_namespace)
    {
      if(not seconds)
        {
          return std::numeric_limits<double>::quiet_NaN();
        }
      double hours = 0;
      double minutes = 0;
      double msecs = 0;
      auto before = previous_element(seconds);
      if(named(before, "minutes", accept_empty_namespace))
        {
          minutes = number(before.attribute("value").value());
          before = previous_element(before);
        }
      if(named(before, "hours", accept_empty_namespace))
        {
          hours = number(before.attribute("value").value());
        }
      const auto after = next_element(seconds);
      if(named(after, "msecs", accept_empty_namespace))
        {
          msecs = number(after.attribute("value").value());
        }
      return 3600000 * hours + 60000 * minutes + 1000 * number(seconds.attribute("value").value())
             + msecs;
    }

    inline void validate_track(pugi::xml_node track, bool accept_empty_namespace,
                               std::vector<validation_issue>& issues)
    {
      const auto first_body = first_body_element(track, accept_empty_namespace);
      if(first_body and not named(first_body, "cover", accept_empty_namespace)
         and not named(first_body, "bdiv", accept_empty_namespace))
        {
          add(issues, "track-structure", track,
              "Track must begin with a cue block, optionally preceded by a cover.");
        }

      pugi::xml_node first_bdiv;
      for(const auto child : track.children())
        {
          if(named(child, "bdiv", accept_empty_namespace))
            {
              first_bdiv = child;
              break;
            }
        }
      if(first_bdiv)
        {
          for(auto child = track.first_child(); child and child != first_bdiv;
              child = child.next_sibling())
            {
              if((child.type() == pugi::node_pcdata or child.type() == pugi::node_cdata)
                 and not is_xml_whitespace(child.value()))
                {
                  add(issues, "track-structure", track,
                      "Track must not contain text before its first cue block.");
                  break;
                }
            }
        }

      bool have_previous_start = false;
      bool have_previous_chapter = false;
      double previous_start = 0;
      double previous_chapter = 0;
      for(auto bdiv = first_bdiv; bdiv;)
        {
          pugi::xml_node next_bdiv;
          std::vector<pugi::xml_node> seconds;
          std::vector<pugi::xml_node> chapters;
          bool audio = false;
          bool seen_element = false;
          bool text_before_element = false;
          pugi::xml_node first_element;
          for(auto child = bdiv.next_sibling(); child; child = child.next_sibling())
            {
              if(named(child, "bdiv", accept_empty_namespace))
                {
                  next_bdiv = child;
                  break;
                }
              if(child.type() == pugi::node_element)
                {
                  if(not seen_element)
                    {
                      first_element = child;
                      seen_element = true;
                    }
                  if(named(child, "seconds", accept_empty_namespace))
                    {
                      seconds.push_back(child);
                    }
                  if(named(child, "chapter", accept_empty_namespace))
                    {
                      chapters.push_back(child);
                    }
                  audio = audio or named(child, "audio", accept_empty_namespace);
                }
              else if((child.type() == pugi::node_pcdata or child.type() == pugi::node_cdata)
                      and not seen_element and not is_xml_whitespace(child.value()))
                {
                  text_before_element = true;
                }
            }
          if(first_element and not named(first_element, "hours", accept_empty_namespace)
             and not named(first_element, "minutes", accept_empty_namespace)
             and not named(first_element, "seconds", accept_empty_namespace))
            {
              add(issues, "track-cue-block", bdiv,
                  "A track cue block must begin with a start timestamp.");
            }
          if(text_before_element)
            {
              add(issues, "track-cue-block", bdiv,
                  "A track cue block must not contain text before its start timestamp.");
            }
          const double start = timestamp_ms(seconds.empty() ? pugi::xml_node{} : seconds[0],
                                            accept_empty_namespace);
          if(seconds.size() == 2 and not(timestamp_ms(seconds[1], accept_empty_namespace) >= start))
            {
              add(issues, "track-cue-block-timestamp-order", bdiv,
                  "A track cue block end time must not be earlier than its start time.");
            }
          if(have_previous_start and not(start >= previous_start))
            {
              add(issues, "track-cue-block-sequence", bdiv,
                  "Track cue blocks must appear in non-decreasing start-time order.");
            }
          if(audio and seconds.size() != 2)
            {
              add(issues, "track-audio-requires-end", bdiv,
                  "A track cue block with audio must have an end time.");
            }
          for(const auto chapter : chapters)
            {
              if(have_previous_chapter and not(start > previous_chapter))
                {
                  add(issues, "track-chapter-strictly-increasing", chapter,
                      "Chapter boundaries must have strictly increasing start times.");
                }
              previous_chapter = start;
              have_previous_chapter = true;
            }
          previous_start = start;
          have_previous_start = true;
          bdiv = next_bdiv;
        }
    }
  }

  inline std::vector<validation_issue> validate_schematron(const pugi::xml_document& document,
                                                           bool allow_empty_namespace = false)
  {
    namespace detail = validation_detail;
    std::vector<validation_issue> issues;
    const pugi::xml_node root = document.document_element();
    if(not root)
      {
        return issues;
      }
    const bool accept_empty_namespace
        = allow_empty_namespace and detail::namespace_uri(root).empty();
    const auto nodes = detail::descendants(root);

    // list-structure, track-structure, and table-structure
    for(const auto node : nodes)
      {
        if(detail::named(node, "list", accept_empty_namespace))
          {
            const auto first = detail::first_body_element(node, accept_empty_namespace);
            if(first and not detail::named(first, "ldiv", accept_empty_namespace))
              {
                detail::add(issues, "list-structure", node,
                            "List must have ldiv as first element after optional element head.");
              }
          }
        if(detail::named(node, "track", accept_empty_namespace))
          {
            detail::validate_track(node, accept_empty_namespace, issues);
          }
      }
    for(const auto node : nodes)
      {
        if(detail::named(node, "table", accept_empty_namespace)
           or detail::named(node, "index", accept_empty_namespace))
          {
            const auto first = detail::first_body_element(node, accept_empty_namespace);
            if(first and not detail::is_cell(first, accept_empty_namespace))
              {
                detail::add(issues, "table-structure", node,
                            "Table and index must have cell-starting token as first element after "
                            "optional element head.");
              }
          }
      }

    // table-rectangular-grid: rows ending at nl tokens must agree.
    for(const auto node : nodes)
      {
        if(not detail::named(node, "table", accept_empty_namespace)
           and not detail::named(node, "index", accept_empty_namespace))
          {
            continue;
          }
        std::size_t first_row = 0;
        std::size_t cells = 0;
        bool seen_first_nl = false;
        bool mismatch = false;
        for(const auto child : node.children())
          {
            if(detail::is_cell(child, accept_empty_namespace))
              {
                ++cells;
              }
            if(detail::named(child, "nl", accept_empty_namespace))
              {
                if(not seen_first_nl)
                  {
                    first_row = cells;
                    seen_first_nl = true;
                  }
                else if(cells != first_row)
                  {
                    mismatch = true;
                  }
                cells = 0;
              }
          }
        if(mismatch)
          {
            detail::add(issues, "table-rectangular-grid", node,
                        "Table and index must follow the rectangular rule: all rows must have the "
                        "same number of cells.");
          }
      }

    // element-head-placement
    const std::set<std::string_view> head_hosts
        = { "text",         "heading",       "code",        "formula",  "caption", "description",
            "summary",      "page_header",   "page_footer", "footnote", "picture", "marker",
            "field_region", "field_heading", "field_item",  "key",      "value",   "list",
            "table",        "index",         "group",       "track",    "voice",   "chapter",
            "cover",        "frame",         "audio" };
    for(const auto node : nodes)
      {
        if(detail::namespace_uri(node) != detail::doclang_namespace
           and not(accept_empty_namespace and detail::namespace_uri(node).empty()))
          {
            continue;
          }
        if(not head_hosts.contains(detail::local_name(node)))
          {
            continue;
          }
        bool text_seen = false;
        for(const auto child : node.children())
          {
            if((detail::named(node, "list", accept_empty_namespace)
                and detail::named(child, "ldiv", accept_empty_namespace))
               or ((detail::named(node, "table", accept_empty_namespace)
                    or detail::named(node, "index", accept_empty_namespace))
                   and detail::is_cell(child, accept_empty_namespace)))
              {
                break;
              }
            if((child.type() == pugi::node_pcdata or child.type() == pugi::node_cdata)
               and not is_xml_whitespace(child.value()))
              {
                text_seen = true;
              }
            if(text_seen and detail::is_head(child, accept_empty_namespace))
              {
                detail::add(issues, "element-head-placement", node,
                            "Property elements in the element head must appear before any "
                            "non-whitespace text content.");
                break;
              }
          }
      }

    // xref-href-mutual-exclusivity and xref-thread-defined
    std::set<std::string> thread_ids;
    for(const auto node : nodes)
      {
        if(detail::named(node, "thread", accept_empty_namespace))
          {
            if(const auto id = node.attribute("thread_id"))
              {
                thread_ids.insert(id.value());
              }
          }
        if(detail::first_child(node, "xref", accept_empty_namespace)
           and detail::first_child(node, "href", accept_empty_namespace))
          {
            detail::add(issues, "xref-href-mutual-exclusivity", node,
                        "Element head must not contain both xref and href elements; they are "
                        "mutually exclusive.");
          }
      }
    for(const auto node : nodes)
      {
        if(detail::named(node, "xref", accept_empty_namespace))
          {
            const auto id = node.attribute("thread_id");
            if(not id or not thread_ids.contains(id.value()))
              {
                detail::add(issues, "xref-thread-defined", node,
                            "Element xref references a thread_id that no thread element defines.");
              }
          }
      }

    // location-value-range and location-block-order
    for(const auto node : nodes)
      {
        if(detail::named(node, "location", accept_empty_namespace))
          {
            std::size_t index = 1;
            for(auto previous = node.previous_sibling(); previous;
                previous = previous.previous_sibling())
              {
                if(detail::named(previous, "location", accept_empty_namespace))
                  {
                    ++index;
                  }
              }
            const bool x_axis = index % 2 == 1;
            const double value = detail::number(node.attribute("value").value());
            const double limit
                = detail::coordinate_resolution(node, root, x_axis, accept_empty_namespace);
            if(not(value >= 0 and value < limit))
              {
                detail::add(issues, "location-value-range", node,
                            "Location value must satisfy 0 <= value < axis_limit.");
              }
          }

        std::vector<pugi::xml_node> locations;
        for(const auto child : node.children())
          {
            if(detail::named(child, "location", accept_empty_namespace))
              {
                locations.push_back(child);
              }
          }
        if(locations.empty())
          {
            continue;
          }

        const double nan = std::numeric_limits<double>::quiet_NaN();
        const auto normalized = [&](std::size_t i, bool x_axis) {
          if(i >= locations.size())
            {
              return nan;
            }
          return detail::number(locations[i].attribute("value").value())
                 / detail::coordinate_resolution(locations[i], root, x_axis,
                                                 accept_empty_namespace);
        };
        if(not(normalized(0, true) <= normalized(2, true)
               and normalized(1, false) <= normalized(3, false)))
          {
            detail::add(issues, "location-block-order", node,
                        "Location block must satisfy x0_norm <= x1_norm and y0_norm <= y1_norm.");
          }
      }

    // thread-host-type-consistency
    std::map<std::string, std::set<std::string>> hosts;
    for(const auto node : nodes)
      {
        if(detail::named(node, "thread", accept_empty_namespace))
          {
            hosts[node.attribute("thread_id").value()].insert(
                detail::thread_host(node, accept_empty_namespace));
          }
      }
    for(const auto& [id, types] : hosts)
      {
        (void)id;
        if(types.size() > 1)
          {
            detail::add(
                issues, "thread-host-type-consistency", root,
                "All thread elements with the same thread_id must use the same host element type.");
            break;
          }
      }

    // Virtual text in lists and table cells.
    for(const auto node : nodes)
      {
        if(detail::named(node, "ldiv", accept_empty_namespace)
           and detail::named(node.parent(), "list", accept_empty_namespace))
          {
            pugi::xml_node stop;
            for(auto next = node.next_sibling(); next; next = next.next_sibling())
              {
                if(detail::named(next, "ldiv", accept_empty_namespace))
                  {
                    stop = next;
                    break;
                  }
              }
            if(detail::text_before_first_header(node.next_sibling(), stop, accept_empty_namespace))
              {
                detail::add(issues, "list-virtual-text-element-head", node,
                            "In list items, property elements in the element head must appear "
                            "before non-whitespace text content.");
              }
          }
        if(detail::is_cell(node, accept_empty_namespace)
           and (detail::named(node.parent(), "table", accept_empty_namespace)
                or detail::named(node.parent(), "index", accept_empty_namespace)))
          {
            pugi::xml_node stop;
            for(auto next = node.next_sibling(); next; next = next.next_sibling())
              {
                if(detail::is_cell(next, accept_empty_namespace)
                   or detail::named(next, "nl", accept_empty_namespace))
                  {
                    stop = next;
                    break;
                  }
              }
            if(detail::text_before_first_header(node.next_sibling(), stop, accept_empty_namespace))
              {
                detail::add(issues, "table-virtual-text-element-head", node,
                            "In table and index cells, property elements in the element head must "
                            "appear before non-whitespace text content.");
              }
          }
      }

    // Field ancestry and the per-field-item key limit.
    for(const auto node : nodes)
      {
        if(detail::named(node, "field_heading", accept_empty_namespace)
           and not detail::has_ancestor(node, "field_region", accept_empty_namespace))
          {
            detail::add(issues, "field-heading-region", node,
                        "field_heading and field_item must be descendants of field_region.");
          }
        if(detail::named(node, "field_item", accept_empty_namespace))
          {
            if(not detail::has_ancestor(node, "field_region", accept_empty_namespace))
              {
                detail::add(issues, "field-item-region", node,
                            "field_heading and field_item must be descendants of field_region.");
              }
            if(detail::own_key_count(node, accept_empty_namespace) > 1)
              {
                detail::add(issues, "field-item-own-key", node,
                            "A field_item may contain at most one own descendant key.");
              }
          }
        if(detail::named(node, "key", accept_empty_namespace)
           and not detail::has_ancestor(node, "field_item", accept_empty_namespace))
          {
            detail::add(issues, "key-field-item", node,
                        "key and value must be descendants of field_item.");
          }
        if(detail::named(node, "value", accept_empty_namespace)
           and not detail::has_ancestor(node, "field_item", accept_empty_namespace))
          {
            detail::add(issues, "value-field-item", node,
                        "key and value must be descendants of field_item.");
          }
      }

    // Picture body rules.
    for(const auto node : nodes)
      {
        if(not detail::named(node, "picture", accept_empty_namespace))
          {
            continue;
          }
        const auto src = detail::first_child(node, "src", accept_empty_namespace);
        const auto tabular = detail::first_child(node, "tabular", accept_empty_namespace);
        const auto body = detail::first_body_element(node, accept_empty_namespace);
        if(tabular and std::string_view(node.attribute("class").value()) != "chart")
          {
            detail::add(issues, "picture-tabular-chart", node,
                        "Element tabular is only allowed in picture with class=\"chart\".");
          }
        if(src and src != body)
          {
            detail::add(issues, "picture-src-first", node,
                        "Element src must be the first element of the picture body when present.");
          }
        if(tabular)
          {
            pugi::xml_node after_src;
            for(auto next = src.next_sibling(); next; next = next.next_sibling())
              {
                if(next.type() == pugi::node_element)
                  {
                    after_src = next;
                    break;
                  }
              }
            if((not src and tabular != body) or (src and tabular != after_src))
              {
                detail::add(issues, "picture-tabular-after-src", node,
                            "Element tabular must immediately follow src when src is present, "
                            "otherwise it may be the first body element.");
              }
          }
      }

    return issues;
  }

  inline std::vector<validation_issue> validate_schematron_xml(std::string_view xml,
                                                               bool allow_empty_namespace = false)
  {
    pugi::xml_document document;
    const auto parse
        = document.load_buffer(xml.data(), xml.size(), pugi::parse_default | pugi::parse_ws_pcdata);
    if(not parse)
      {
        throw std::invalid_argument(std::string("could not parse DocLang XML: ")
                                    + parse.description());
      }
    return validate_schematron(document, allow_empty_namespace);
  }
}

#endif
