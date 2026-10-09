#ifndef DOCLANG_NATIVE_ELEMENT_VALIDATION_H_
#define DOCLANG_NATIVE_ELEMENT_VALIDATION_H_

#include <algorithm>
#include <set>
#include <string>
#include <utility>

#include <doclang/dclg_document.h>

namespace doclang::native
{
  enum class insertion_kind
  {
    append_child,
    prepend_child,
    before,
    after
  };

  struct insertion_site
  {
    insertion_kind kind;
    std::string xpath;

    static insertion_site append_child(std::string path)
    {
      return { insertion_kind::append_child, std::move(path) };
    }
    static insertion_site prepend_child(std::string path)
    {
      return { insertion_kind::prepend_child, std::move(path) };
    }
    static insertion_site before(std::string path)
    {
      return { insertion_kind::before, std::move(path) };
    }
    static insertion_site after(std::string path)
    {
      return { insertion_kind::after, std::move(path) };
    }
  };

  inline validation_report validate_local_element(const dclg_node& node)
  {
    validation_report report
        = validate_doclang_xml(node.to_xml(), { .allow_empty_namespace = true });
    report.scope = "local";
    const std::set<std::string> contextual
        = { "xref-thread-defined",  "thread-host-type-consistency",
            "field-heading-region", "field-item-region",
            "key-field-item",       "value-field-item",
            "location-value-range", "location-block-order" };
    std::erase_if(report.schematron_errors, [&](const validation_issue& issue) {
      return contextual.contains(issue.assertion);
    });
    return report;
  }

  inline validation_report validate_element_in(const dclg_node& node, const dclg_document& source,
                                               const insertion_site& site)
  {
    validation_report report;
    report.scope = "contextual";
    dclg_document candidate;
    if(not candidate.read(source.raw()))
      {
        report.xsd_errors.push_back({ 0, candidate.get_last_error() });
        return report;
      }
    try
      {
        switch(site.kind)
          {
          case insertion_kind::append_child:
            candidate.append_child(site.xpath, node);
            break;
          case insertion_kind::prepend_child:
            candidate.prepend_child(site.xpath, node);
            break;
          case insertion_kind::before:
            candidate.insert_before(site.xpath, node);
            break;
          case insertion_kind::after:
            candidate.insert_after(site.xpath, node);
            break;
          }
      }
    catch(const std::exception& error)
      {
        report.xsd_errors.push_back({ 0, error.what() });
        return report;
      }
    report = candidate.validate();
    report.scope = "contextual";
    return report;
  }
}

#endif
