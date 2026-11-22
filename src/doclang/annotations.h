//-*-C++-*-

#ifndef DOCLANG_NATIVE_ANNOTATIONS_H_
#define DOCLANG_NATIVE_ANNOTATIONS_H_

#include <charconv>
#include <cctype>
#include <cmath>
#include <exception>
#include <limits>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <system_error>
#include <string>
#include <string_view>
#include <vector>

#include <doclang/dclx_document.h>

namespace doclang::native
{

  const static inline std::string ANNOTATIONS_DIR = "annotations";
  const static inline std::string PROPERTIES_CSV = ANNOTATIONS_DIR + "/properties.csv";
  const static inline std::string INSTANCES_CSV = ANNOTATIONS_DIR + "/instances.csv";
  const static inline std::string ENTITIES_CSV = ANNOTATIONS_DIR + "/entities.csv";
  const static inline std::string RELATIONS_CSV = ANNOTATIONS_DIR + "/relations.csv";
  const static inline std::string REFERENCES_DCLG = ANNOTATIONS_DIR + "/references.dclg";
  const static inline std::string SUMMARY_DCLG = ANNOTATIONS_DIR + "/summary.dclg";
  const static inline std::string TOC_DCLG = ANNOTATIONS_DIR + "/toc.dclg";
  const static inline std::string CONCEPTS_DCLG = ANNOTATIONS_DIR + "/concepts.dclg";

  // parses one DCLG sidecar, forwards parse errors to the owning DCLX
  // document, then applies the sidecar-specific validation
  template <typename validator_type>
  inline bool parse_sidecar_dclg(dclx_document& doc, std::string_view xml, const std::string& path,
                                 validator_type&& validate, std::shared_ptr<dclg_document>& out)
  {
    auto sidecar = std::make_shared<dclg_document>();
    if(not sidecar->read(xml))
      {
        doc.set_last_error(path + ": " + sidecar->get_last_error());
        return false;
      }

    const auto report = sidecar->validate({ .allow_empty_namespace = true });
    if(not report.ok())
      {
        doc.set_last_error(path + ": " + report.first_error());
        return false;
      }

    std::string error;
    if(not validate(*sidecar, error))
      {
        doc.set_last_error(error);
        return false;
      }

    out = std::move(sidecar);
    return true;
  }

  inline bool validate_summary_dclg(const dclg_document&, std::string&)
  {
    // a valid DCLG root is all a summary sidecar has to satisfy
    return true;
  }

  inline bool validate_toc_dclg(const dclg_document& sidecar, std::string& error)
  {
    const auto root = sidecar.root();
    for(const auto child : root.children())
      {
        if(std::string_view(child.name()) == "head")
          {
            continue;
          }
        if(std::string_view(child.name()) != "heading" or not child.child("href")
           or std::string_view(child.child("href").attribute("uri").value()).empty())
          {
            error = TOC_DCLG + " must contain headings with source hrefs";
            return false;
          }
      }

    return true;
  }

  inline bool validate_toc_targets(const dclx_document& document, const dclg_document& sidecar,
                                   std::string& error)
  {
    for(const auto heading : sidecar.root().children("heading"))
      {
        const std::string uri = heading.child("href").attribute("uri").value();
        if(uri.empty() or uri.front() != '#')
          {
            error = TOC_DCLG + " heading href must be an encoded XPath fragment";
            return false;
          }
        std::string xpath;
        for(std::size_t i = 1; i < uri.size(); ++i)
          {
            if(uri[i] == '%' and i + 2 < uri.size()
               and std::isxdigit(static_cast<unsigned char>(uri[i + 1]))
               and std::isxdigit(static_cast<unsigned char>(uri[i + 2])))
              {
                const auto digit = [](char value) {
                  return value >= '0' and value <= '9'   ? value - '0'
                         : value >= 'A' and value <= 'F' ? value - 'A' + 10
                                                         : value - 'a' + 10;
                };
                xpath += static_cast<char>(digit(uri[i + 1]) * 16 + digit(uri[i + 2]));
                i += 2;
              }
            else
              {
                xpath += uri[i];
              }
          }
        if(not resolve_doclang_path(document.root(), xpath).found)
          {
            error = TOC_DCLG + " heading XPath does not resolve: " + xpath;
            return false;
          }
      }
    return true;
  }

  inline bool validate_concepts_dclg(const dclg_document&, std::string&)
  {
    return true;
  }

  inline bool validate_references_dclg(const dclg_document&, std::string&)
  {
    return true;
  }

  inline bool set_summary_dclg(dclx_document& doc, std::string_view xml)
  {
    std::shared_ptr<dclg_document> sidecar;
    if(not parse_sidecar_dclg(doc, xml, SUMMARY_DCLG, validate_summary_dclg, sidecar))
      {
        return false;
      }

    doc.set_summary(std::move(sidecar));
    return true;
  }

  inline bool set_toc_dclg(dclx_document& doc, std::string_view xml)
  {
    std::shared_ptr<dclg_document> sidecar;
    if(not parse_sidecar_dclg(doc, xml, TOC_DCLG, validate_toc_dclg, sidecar))
      {
        return false;
      }

    std::string error;
    if(not validate_toc_targets(doc, *sidecar, error))
      {
        doc.set_last_error(error);
        return false;
      }

    doc.set_toc(std::move(sidecar));
    return true;
  }

  inline bool set_concepts_dclg(dclx_document& doc, std::string_view xml)
  {
    std::shared_ptr<dclg_document> sidecar;
    if(not parse_sidecar_dclg(doc, xml, CONCEPTS_DCLG, validate_concepts_dclg, sidecar))
      {
        return false;
      }

    doc.set_concepts(std::move(sidecar));
    return true;
  }

  inline bool set_references_dclg(dclx_document& doc, std::string_view xml)
  {
    std::shared_ptr<dclg_document> sidecar;
    if(not parse_sidecar_dclg(doc, xml, REFERENCES_DCLG, validate_references_dclg, sidecar))
      {
        return false;
      }
    doc.set_references(std::move(sidecar));
    return true;
  }

  inline std::string csv_escape(const std::string& value)
  {
    bool needs_quotes = false;
    for(char c : value)
      {
        if(c == ',' or c == '"' or c == '\n' or c == '\r')
          {
            needs_quotes = true;
            break;
          }
      }

    if(not needs_quotes)
      {
        return value;
      }

    std::string result = "\"";
    for(char c : value)
      {
        if(c == '"')
          {
            result += "\"\"";
          }
        else
          {
            result += c;
          }
      }
    result += "\"";

    return result;
  }

  inline std::string csv_row(const std::vector<std::string>& row)
  {
    std::ostringstream oss;
    for(std::size_t i = 0; i < row.size(); i++)
      {
        if(i > 0)
          {
            oss << ",";
          }

        oss << csv_escape(row.at(i));
      }

    oss << "\n";
    return oss.str();
  }

  inline std::vector<std::vector<std::string>> parse_csv(std::string_view text)
  {
    std::vector<std::vector<std::string>> rows;
    std::vector<std::string> row;
    std::string cell;
    bool in_quotes = false;

    for(std::size_t i = 0; i < text.size(); i++)
      {
        const char c = text.at(i);

        if(in_quotes)
          {
            if(c == '"')
              {
                if(i + 1 < text.size() and text.at(i + 1) == '"')
                  {
                    cell += '"';
                    i += 1;
                  }
                else
                  {
                    in_quotes = false;
                  }
              }
            else
              {
                cell += c;
              }

            continue;
          }

        if(c == '"')
          {
            in_quotes = true;
          }
        else if(c == ',')
          {
            row.push_back(cell);
            cell.clear();
          }
        else if(c == '\n')
          {
            row.push_back(cell);
            cell.clear();
            rows.push_back(row);
            row.clear();
          }
        else if(c == '\r')
          {
          }
        else
          {
            cell += c;
          }
      }

    if(not cell.empty() or not row.empty())
      {
        row.push_back(cell);
        rows.push_back(row);
      }

    return rows;
  }

  inline bool headers_match(const std::vector<std::string>& lhs,
                            const std::vector<std::string>& rhs)
  {
    return lhs == rhs;
  }

  template <typename value_type> inline value_type parse_integral_cell(const std::string& cell)
  {
    unsigned long long result = 0;
    const auto [end, error] = std::from_chars(cell.data(), cell.data() + cell.size(), result);
    if(error != std::errc() or end != cell.data() + cell.size()
       or result > std::numeric_limits<value_type>::max())
      {
        throw std::invalid_argument("invalid unsigned integer: " + cell);
      }
    return static_cast<value_type>(result);
  }

  inline float parse_float_cell(const std::string& cell)
  {
    std::size_t end = 0;
    const float value = std::stof(cell, &end);
    if(end != cell.size() or not std::isfinite(value))
      {
        throw std::invalid_argument("invalid finite number: " + cell);
      }
    return value;
  }

  inline bool load_properties_csv(std::string_view csv, std::vector<base_property>& properties,
                                  std::string& error)
  {
    const auto rows = parse_csv(csv);
    if(rows.empty())
      {
        return true;
      }
    if(!headers_match(rows.front(), base_property::HEADERS))
      {
        error = "unexpected header in " + PROPERTIES_CSV;
        return false;
      }
    for(std::size_t i = 1; i < rows.size(); ++i)
      {
        const auto& row = rows[i];
        if(row.size() != base_property::HEADERS.size())
          {
            error = "unexpected row width in " + PROPERTIES_CSV;
            return false;
          }
        properties.emplace_back(row[0], row[1], row[2], parse_float_cell(row[3]));
      }
    return true;
  }

  inline bool load_instances_csv(std::string_view csv, std::vector<base_instance>& instances,
                                 std::string& error)
  {
    const auto rows = parse_csv(csv);
    if(rows.empty())
      {
        return true;
      }
    if(!headers_match(rows.front(), base_instance::HEADERS))
      {
        error = "unexpected header in " + INSTANCES_CSV;
        return false;
      }
    for(std::size_t i = 1; i < rows.size(); ++i)
      {
        const auto& row = rows[i];
        if(row.size() != base_instance::HEADERS.size())
          {
            error = "unexpected row width in " + INSTANCES_CSV;
            return false;
          }
        instances.emplace_back(row[0], row[1], row[2], parse_float_cell(row[3]),
                               parse_integral_cell<base_types::hash_type>(row[4]),
                               parse_integral_cell<base_types::hash_type>(row[5]),
                               parse_integral_cell<base_types::ind_type>(row[6]),
                               parse_integral_cell<base_types::ind_type>(row[7]), row[8], row[9]);
      }
    return true;
  }

  inline bool load_entities_csv(std::string_view csv, std::vector<base_entity>& entities,
                                std::string& error)
  {
    const auto rows = parse_csv(csv);
    if(rows.empty())
      {
        return true;
      }
    if(!headers_match(rows.front(), base_entity::HEADERS))
      {
        error = "unexpected header in " + ENTITIES_CSV;
        return false;
      }
    for(std::size_t i = 1; i < rows.size(); ++i)
      {
        const auto& row = rows[i];
        if(row.size() != base_entity::HEADERS.size())
          {
            error = "unexpected row width in " + ENTITIES_CSV;
            return false;
          }
        entities.emplace_back(row[0], row[1], row[2],
                              parse_integral_cell<base_types::hash_type>(row[3]),
                              parse_integral_cell<base_types::cnt_type>(row[4]));
      }
    return true;
  }

  inline bool load_relations_csv(std::string_view csv, std::vector<base_relation>& relations,
                                 std::string& error)
  {
    const auto rows = parse_csv(csv);
    if(rows.empty())
      {
        return true;
      }
    if(!headers_match(rows.front(), base_relation::HEADERS))
      {
        error = "unexpected header in " + RELATIONS_CSV;
        return false;
      }
    for(std::size_t i = 1; i < rows.size(); ++i)
      {
        const auto& row = rows[i];
        if(row.size() != base_relation::HEADERS.size())
          {
            error = "unexpected row width in " + RELATIONS_CSV;
            return false;
          }
        relations.emplace_back(row[0], parse_float_cell(row[1]),
                               parse_integral_cell<base_types::hash_type>(row[2]),
                               parse_integral_cell<base_types::hash_type>(row[3]));
      }
    return true;
  }

  inline bool load_annotations(dclx_document& doc)
  {
    doc.clear_annotations();
    if(!doc.has_archive())
      {
        return true;
      }
    std::string error;
    std::string current_path;
    bool has_entities = false;
    try
      {
        current_path = PROPERTIES_CSV;
        const auto properties = doc.artifacts().text(current_path);
        if(properties and not load_properties_csv(*properties, doc.mutable_properties(), error))
          {
            doc.set_last_error(error);
            return false;
          }
        current_path = INSTANCES_CSV;
        const auto instances = doc.artifacts().text(current_path);
        if(instances and not load_instances_csv(*instances, doc.mutable_instances(), error))
          {
            doc.set_last_error(error);
            return false;
          }
        current_path = ENTITIES_CSV;
        const auto entities = doc.artifacts().text(current_path);
        has_entities = entities.has_value();
        if(entities and not load_entities_csv(*entities, doc.mutable_entities(), error))
          {
            doc.set_last_error(error);
            return false;
          }
        current_path = RELATIONS_CSV;
        const auto relations = doc.artifacts().text(current_path);
        if(relations and not load_relations_csv(*relations, doc.mutable_relations(), error))
          {
            doc.set_last_error(error);
            return false;
          }
      }
    catch(const std::exception& exception)
      {
        doc.set_last_error("invalid value in " + current_path + ": " + exception.what());
        return false;
      }

    const auto references = doc.artifacts().text(REFERENCES_DCLG);
    if(references and not set_references_dclg(doc, *references))
      {
        return false;
      }
    if(doc.artifacts().has("annotations/references.bib"))
      {
        doc.set_last_error(
            "unsupported annotations/references.bib; use annotations/references.dclg");
        return false;
      }
    if(doc.artifacts().has("annotations/document_reference.bib"))
      {
        doc.set_last_error(
            "unsupported annotations/document_reference.bib; use annotations/references.dclg");
        return false;
      }
    const auto summary = doc.artifacts().text(SUMMARY_DCLG);
    if(summary && !set_summary_dclg(doc, *summary))
      {
        return false;
      }
    const auto toc = doc.artifacts().text(TOC_DCLG);
    if(toc and not set_toc_dclg(doc, *toc))
      {
        return false;
      }
    const auto concepts = doc.artifacts().text(CONCEPTS_DCLG);
    if(concepts and not set_concepts_dclg(doc, *concepts))
      {
        return false;
      }
    if(!has_entities and not doc.get_instances().empty())
      {
        doc.compute_entities();
      }
    return true;
  }

  template <typename record_type>
  inline std::string records_csv(const std::vector<record_type>& records)
  {
    std::ostringstream output;
    output << csv_row(record_type::HEADERS);
    for(const auto& record : records)
      {
        output << csv_row(record.to_row());
      }
    return output.str();
  }

  inline std::string to_properties_csv(const std::vector<base_property>& values)
  {
    return records_csv(values);
  }
  inline std::string to_instances_csv(const std::vector<base_instance>& values)
  {
    return records_csv(values);
  }
  inline std::string to_entities_csv(const std::vector<base_entity>& values)
  {
    return records_csv(values);
  }
  inline std::string to_relations_csv(const std::vector<base_relation>& values)
  {
    return records_csv(values);
  }
}

#endif
