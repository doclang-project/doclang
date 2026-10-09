#ifndef DOCLANG_NATIVE_DCLG_NODE_DCLG_FIELD_REGION_H_
#define DOCLANG_NATIVE_DCLG_NODE_DCLG_FIELD_REGION_H_

#include <cstddef>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>

#include <doclang/dclg_node.h>
#include <doclang/validation/element.h>

namespace doclang::native
{
  class dclg_field_region : public dclg_node
  {
  public:

    dclg_field_region();
    validation_report validate_local() const;
    std::tuple<bool, std::string> is_valid() const;
    validation_report validate_in(const dclg_document& doc, const insertion_site& site) const;
    std::tuple<bool, std::string> is_valid_in(const dclg_document& doc,
                                              const insertion_site& site) const;
  };

  inline dclg_field_region::dclg_field_region()
      : dclg_node(dclg_node::element(element_tag::field_region))
  {
  }

  inline validation_report dclg_field_region::validate_local() const
  {
    return validate_local_element(*this);
  }

  inline std::tuple<bool, std::string> dclg_field_region::is_valid() const
  {
    return validate_local().is_valid();
  }

  inline validation_report dclg_field_region::validate_in(const dclg_document& doc,
                                                          const insertion_site& site) const
  {
    return validate_element_in(*this, doc, site);
  }

  inline std::tuple<bool, std::string>
  dclg_field_region::is_valid_in(const dclg_document& doc, const insertion_site& site) const
  {
    return validate_in(doc, site).is_valid();
  }
}

#endif
