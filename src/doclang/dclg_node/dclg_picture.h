#ifndef DOCLANG_NATIVE_DCLG_NODE_DCLG_PICTURE_H_
#define DOCLANG_NATIVE_DCLG_NODE_DCLG_PICTURE_H_

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
  class dclg_picture : public dclg_node
  {
  public:

    explicit dclg_picture(std::string_view src = "");
    void set_src(std::string_view uri);
    void set_caption(std::string_view text);
    void set_tabular(const dclg_node& table);
    validation_report validate_local() const;
    std::tuple<bool, std::string> is_valid() const;
    validation_report validate_in(const dclg_document& doc, const insertion_site& site) const;
    std::tuple<bool, std::string> is_valid_in(const dclg_document& doc,
                                              const insertion_site& site) const;
  };

  inline dclg_picture::dclg_picture(std::string_view src)
      : dclg_node(dclg_node::element(element_tag::picture))
  {
    if(not src.empty())
      {
        set_src(src);
      }
  }

  inline void dclg_picture::set_src(std::string_view uri)
  {
    auto src = root().child(xml_name(element_tag::src));
    if(not src)
      {
        auto caption = root().child(xml_name(element_tag::caption));
        if(caption)
          {
            src = root().insert_child_after(xml_name(element_tag::src), caption);
          }
        else
          {
            auto anchor = root().child(xml_name(element_tag::tabular));
            if(not anchor)
              {
                for(auto child : root().children())
                  {
                    if(std::string_view(child.name()) != "label"
                       and std::string_view(child.name()) != "thread"
                       and std::string_view(child.name()) != "xref"
                       and std::string_view(child.name()) != "href"
                       and std::string_view(child.name()) != "layer"
                       and std::string_view(child.name()) != "location"
                       and std::string_view(child.name()) != "custom")
                      {
                        anchor = child;
                        break;
                      }
                  }
              }
            src = anchor ? root().insert_child_before(xml_name(element_tag::src), anchor)
                         : root().append_child(xml_name(element_tag::src));
          }
      }
    auto attribute = src.attribute(xml_name(attribute_name::uri));
    if(not attribute)
      {
        attribute = src.append_attribute(xml_name(attribute_name::uri));
      }
    attribute.set_value(std::string(uri).c_str());
  }

  inline void dclg_picture::set_caption(std::string_view text)
  {
    set_element_caption(root(), text);
  }

  inline void dclg_picture::set_tabular(const dclg_node& table)
  {
    if(table.name() != to_string_view(element_tag::table))
      {
        throw std::invalid_argument("tabular source must be a table node");
      }
    set_attribute(attribute_name::class_, "chart");
    auto tabular = root().child(xml_name(element_tag::tabular));
    if(not tabular)
      {
        auto src = root().child(xml_name(element_tag::src));
        auto caption = root().child(xml_name(element_tag::caption));
        if(src)
          {
            tabular = root().insert_child_after(xml_name(element_tag::tabular), src);
          }
        else if(caption)
          {
            tabular = root().insert_child_after(xml_name(element_tag::tabular), caption);
          }
        else
          {
            auto body = root().first_child();
            while(body
                  and (std::string_view(body.name()) == "label"
                       or std::string_view(body.name()) == "thread"
                       or std::string_view(body.name()) == "xref"
                       or std::string_view(body.name()) == "href"
                       or std::string_view(body.name()) == "layer"
                       or std::string_view(body.name()) == "location"
                       or std::string_view(body.name()) == "custom"))
              {
                body = body.next_sibling();
              }
            tabular = body ? root().insert_child_before(xml_name(element_tag::tabular), body)
                           : root().append_child(xml_name(element_tag::tabular));
          }
      }
    tabular.remove_children();
    bool in_table_head = true;
    for(auto child : table.root().children())
      {
        const std::string_view name = child.name();
        if(in_table_head
           and (name == "label" or name == "thread" or name == "xref" or name == "href"
                or name == "layer" or name == "location" or name == "caption" or name == "custom"))
          {
            continue;
          }
        in_table_head = false;
        tabular.append_copy(child);
      }
  }

  inline validation_report dclg_picture::validate_local() const
  {
    return validate_local_element(*this);
  }

  inline std::tuple<bool, std::string> dclg_picture::is_valid() const
  {
    return validate_local().is_valid();
  }

  inline validation_report dclg_picture::validate_in(const dclg_document& doc,
                                                     const insertion_site& site) const
  {
    return validate_element_in(*this, doc, site);
  }

  inline std::tuple<bool, std::string> dclg_picture::is_valid_in(const dclg_document& doc,
                                                                 const insertion_site& site) const
  {
    return validate_in(doc, site).is_valid();
  }
}

#endif
