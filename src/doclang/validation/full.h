#ifndef DOCLANG_NATIVE_FULL_VALIDATION_H_
#define DOCLANG_NATIVE_FULL_VALIDATION_H_

#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

#include <libxml/parser.h>
#include <libxml/xmlschemas.h>

#include <doclang/content.h>
#include <doclang/validation/rules.h>
#include <doclang/validation/schema_data.h>

namespace doclang::native
{
  struct xsd_issue
  {
    int line = 0;
    std::string message;
  };

  struct validation_options
  {
    bool allow_empty_namespace = false;
    bool xsd_only = false;
    bool schematron_only = false;
  };

  struct validation_report
  {
    std::vector<xsd_issue> xsd_errors;
    std::vector<validation_issue> schematron_errors;
    std::string scope = "document";

    bool ok() const
    {
      return xsd_errors.empty() and schematron_errors.empty();
    }

    std::string first_error() const
    {
      if(not xsd_errors.empty())
        {
          const auto& issue = xsd_errors.front();
          return "XSD" + (issue.line > 0 ? " line " + std::to_string(issue.line) : "") + ": "
                 + issue.message;
        }
      if(not schematron_errors.empty())
        {
          const auto& issue = schematron_errors.front();
          return "Schematron " + issue.location + ": " + issue.message;
        }
      return "";
    }

    std::tuple<bool, std::string> is_valid() const
    {
      return { ok(), first_error() };
    }
  };

  namespace validation_detail
  {
    inline bool contains_entity_reference(xmlNodePtr node)
    {
      for(; node; node = node->next)
        {
          if(node->type == XML_ENTITY_REF_NODE or contains_entity_reference(node->children))
            {
              return true;
            }
        }
      return false;
    }

    inline bool has_forbidden_dtd_or_entities(std::string_view xml)
    {
      auto document = std::unique_ptr<xmlDoc, decltype(&xmlFreeDoc)>(
          xmlReadMemory(xml.data(), static_cast<int>(xml.size()), "doclang.xml", nullptr,
                        XML_PARSE_NONET | XML_PARSE_NOERROR | XML_PARSE_NOWARNING),
          &xmlFreeDoc);
      return document
             and (document->intSubset or document->extSubset
                  or contains_entity_reference(document->children));
    }

    inline void collect_xsd_error(void* context, xmlErrorPtr error)
    {
      if(not context or not error)
        {
          return;
        }
      auto& issues = *static_cast<std::vector<xsd_issue>*>(context);
      std::string message = error->message ? error->message : "XML Schema validation failed";
      while(not message.empty() and (message.back() == '\n' or message.back() == '\r'))
        {
          message.pop_back();
        }
      issues.push_back({ error->line, std::move(message) });
    }

    inline xmlSchemaPtr compiled_schema()
    {
      static const auto schema = []() {
        auto parser
            = xmlSchemaNewMemParserCtxt(bundled_xsd, static_cast<int>(sizeof(bundled_xsd) - 1));
        if(not parser)
          {
            throw std::runtime_error("could not create DocLang XSD parser");
          }
        xmlSchemaPtr result = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if(not result)
          {
            throw std::runtime_error("could not compile DocLang XSD");
          }
        return std::unique_ptr<xmlSchema, decltype(&xmlSchemaFree)>(result, &xmlSchemaFree);
      }();
      return schema.get();
    }

    inline std::vector<xsd_issue> validate_xsd_xml(std::string_view xml)
    {
      std::vector<xsd_issue> issues;
      auto document = std::unique_ptr<xmlDoc, decltype(&xmlFreeDoc)>(
          xmlReadMemory(xml.data(), static_cast<int>(xml.size()), "doclang.xml", nullptr,
                        XML_PARSE_NONET),
          &xmlFreeDoc);
      if(not document)
        {
          issues.push_back({ 0, "could not parse DocLang XML" });
          return issues;
        }
      auto validator = std::unique_ptr<xmlSchemaValidCtxt, decltype(&xmlSchemaFreeValidCtxt)>(
          xmlSchemaNewValidCtxt(compiled_schema()), &xmlSchemaFreeValidCtxt);
      if(not validator)
        {
          throw std::runtime_error("could not create XSD validator");
        }
      xmlSchemaSetValidStructuredErrors(validator.get(), collect_xsd_error, &issues);
      const int result = xmlSchemaValidateDoc(validator.get(), document.get());
      if(result != 0 and issues.empty())
        {
          issues.push_back({ 0, "XML Schema validation failed" });
        }
      return issues;
    }
  }

  inline validation_report validate_doclang_xml(std::string_view xml,
                                                validation_options options = {})
  {
    validation_report report;
    pugi::xml_document document;
    const auto status
        = document.load_buffer(xml.data(), xml.size(), pugi::parse_default | pugi::parse_ws_pcdata);
    if(not status)
      {
        report.xsd_errors.push_back(
            { 0, std::string("could not parse DocLang XML: ") + status.description() });
        return report;
      }

    if(validation_detail::has_forbidden_dtd_or_entities(xml))
      {
        report.xsd_errors.push_back(
            { 0, "DTD declarations and entity references are not allowed in DocLang documents" });
        return report;
      }

    if(not options.schematron_only)
      {
        if(options.allow_empty_namespace and document.document_element()
           and validation_detail::namespace_uri(document.document_element()).empty())
          {
            document.document_element().append_attribute("xmlns") = "https://www.doclang.ai/ns/v0";
            report.xsd_errors = validation_detail::validate_xsd_xml(serialize_xml(document));
            document.document_element().remove_attribute("xmlns");
          }
        else
          {
            report.xsd_errors = validation_detail::validate_xsd_xml(xml);
          }
      }
    if(not options.xsd_only)
      {
        report.schematron_errors = validate_schematron(document, options.allow_empty_namespace);
      }
    return report;
  }
}

#endif
