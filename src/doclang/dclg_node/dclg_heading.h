#ifndef DOCLANG_NATIVE_DCLG_NODE_DCLG_HEADING_H_
#define DOCLANG_NATIVE_DCLG_NODE_DCLG_HEADING_H_

#include <cstddef>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>

#include <doclang/dclg_node.h>
#include <doclang/validation/element.h>

namespace doclang::native
{
  class dclg_heading : public dclg_node
  {
  public:

    dclg_heading(std::string_view text = "", std::size_t level = 1);
    validation_report validate_local() const;
    std::tuple<bool, std::string> is_valid() const;
    validation_report validate_in(const dclg_document& doc, const insertion_site& site) const;
    std::tuple<bool, std::string> is_valid_in(const dclg_document& doc,
                                              const insertion_site& site) const;
  };

  inline dclg_heading::dclg_heading(std::string_view text, std::size_t level)
      : dclg_node(dclg_node::element(element_tag::heading))
  {
    if(level == 0)
      {
        throw std::invalid_argument("heading level must be positive");
      }
    set_attribute(attribute_name::level, std::to_string(level));
    if(not text.empty())
      {
        append_text(text);
      }
  }

  inline validation_report dclg_heading::validate_local() const
  {
    return validate_local_element(*this);
  }

  inline std::tuple<bool, std::string> dclg_heading::is_valid() const
  {
    return validate_local().is_valid();
  }

  inline validation_report dclg_heading::validate_in(const dclg_document& doc,
                                                     const insertion_site& site) const
  {
    return validate_element_in(*this, doc, site);
  }

  inline std::tuple<bool, std::string> dclg_heading::is_valid_in(const dclg_document& doc,
                                                                 const insertion_site& site) const
  {
    return validate_in(doc, site).is_valid();
  }
}

#endif
