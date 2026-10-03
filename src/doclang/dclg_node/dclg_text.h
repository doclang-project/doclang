#ifndef DOCLANG_NATIVE_DCLG_NODE_DCLG_TEXT_H_
#define DOCLANG_NATIVE_DCLG_NODE_DCLG_TEXT_H_

#include <cstddef>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>

#include <doclang/dclg_node.h>
#include <doclang/validation/element.h>

namespace doclang::native
{
  class dclg_text : public dclg_node
  {
  public:

    explicit dclg_text(std::string_view text = "");
    validation_report validate_local() const;
    std::tuple<bool, std::string> is_valid() const;
    validation_report validate_in(const dclg_document& doc, const insertion_site& site) const;
    std::tuple<bool, std::string> is_valid_in(const dclg_document& doc,
                                              const insertion_site& site) const;
  };

  inline dclg_text::dclg_text(std::string_view text)
      : dclg_node(dclg_node::element(element_tag::text))
  {
    if(not text.empty())
      {
        append_text(text);
      }
  }

  inline validation_report dclg_text::validate_local() const
  {
    return validate_local_element(*this);
  }

  inline std::tuple<bool, std::string> dclg_text::is_valid() const
  {
    return validate_local().is_valid();
  }

  inline validation_report dclg_text::validate_in(const dclg_document& doc,
                                                  const insertion_site& site) const
  {
    return validate_element_in(*this, doc, site);
  }

  inline std::tuple<bool, std::string> dclg_text::is_valid_in(const dclg_document& doc,
                                                              const insertion_site& site) const
  {
    return validate_in(doc, site).is_valid();
  }
}

#endif
