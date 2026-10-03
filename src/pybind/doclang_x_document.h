#ifndef DOCLANG_PYBIND_X_DOCUMENT_H_
#define DOCLANG_PYBIND_X_DOCUMENT_H_

#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <doclang/annotations.h>
#include <doclang/dclx_document.h>
#include <doclang/io/reader.h>
#include <doclang/io/writer.h>
#include <pybind/doclang_document.h>

namespace doclang::binding
{
  namespace py = pybind11;

  class DocLangXDocument : public DoclangDocument
  {
  public:

    DocLangXDocument();

    static std::uint64_t hash(const std::string& text);
    bool read(const std::string& path);
    bool read_xml(const std::string& xml) override;
    bool write(const std::string& path, bool allow_stale_annotations = false);
    bool annotations_stale() const;
    bool has_archive() const;
    bool has_annotations() const;
    std::string source_path() const;
    std::vector<std::string> archive_paths() const;
    std::vector<std::string> annotation_paths() const;
    std::optional<std::string> document_reference() const;
    std::optional<std::string> references() const;
    std::optional<DoclangDocument> summary() const;
    std::optional<DoclangDocument> toc() const;
    std::optional<DoclangDocument> concepts() const;
    void set_document_reference(const std::string& bibtex);
    void set_references(const std::string& bibtex);
    bool set_document_summary(const std::string& dclg);
    bool set_toc(const std::string& dclg);
    bool set_concepts(const std::string& dclg);
    void clear_document_reference();
    void clear_references();
    void clear_document_summary();
    void clear_toc();
    void clear_concepts();
    py::dict overview() const;
    py::object properties() const;
    py::object entities() const;
    py::object instances() const;
    py::object relations() const;
    py::object query_properties(const std::string& type = "", const std::string& label = "",
                                const std::string& xpath = "", float min_conf = 0.0f) const;
    py::object query_entities(const std::string& type = "", const std::string& subtype = "",
                              const std::string& name = "", const std::string& name_contains = "",
                              std::size_t min_count = 0) const;
    py::object query_instances(const std::string& type = "", const std::string& subtype = "",
                               const std::string& name = "", const std::string& name_contains = "",
                               const std::string& xpath = "", float min_conf = 0.0f,
                               std::uint64_t entity_hash = 0) const;
    py::object query_relations(const std::string& name = "", const std::string& name_contains = "",
                               float min_conf = 0.0f, std::uint64_t hash_i = 0,
                               std::uint64_t hash_j = 0) const;
    std::optional<std::pair<std::size_t, std::size_t>>
    table_coordinates(const std::string& xpath) const;

  private:

    explicit DocLangXDocument(std::shared_ptr<native::dclx_document> value);
    static std::optional<DoclangDocument>
    sidecar_wrapper(const native::dclx_document::sidecar_type& sidecar);

    std::shared_ptr<native::dclx_document> doc;
    std::size_t annotation_generation = 0;
  };

  namespace detail
  {
    inline std::string_view pandas_dtype(std::string_view column)
    {
      if(column == "type" or column == "subtype" or column == "xpath" or column == "label"
         or column == "name" or column == "original")
        {
          return "string";
        }
      if(column == "confidence" or column == "conf")
        {
          return "Float32";
        }
      if(column == "ehash" or column == "ihash" or column == "hash_i" or column == "hash_j"
         or column == "char_i" or column == "char_j" or column == "count")
        {
          return "UInt64";
        }
      return "";
    }

    template <typename record_type>
    py::object dataframe_from_records(const std::vector<record_type>& records)
    {
      // Import pandas only for callers that request a DataFrame.
      py::module_ pandas = py::module_::import("pandas");
      py::list rows;
      for(const auto& record : records)
        {
          rows.append(py::cast(record.values()));
        }

      py::object frame
          = pandas.attr("DataFrame")(rows, py::arg("columns") = py::cast(record_type::HEADERS));
      py::dict dtypes;
      for(const std::string& column : record_type::HEADERS)
        {
          const std::string_view dtype = pandas_dtype(column);
          if(not dtype.empty())
            {
              dtypes[py::str(column)] = py::str(dtype);
            }
        }
      return frame.attr("astype")(dtypes);
    }
  }

  inline DocLangXDocument::DocLangXDocument()
      : DocLangXDocument(std::make_shared<native::dclx_document>())
  {
  }

  inline std::uint64_t DocLangXDocument::hash(const std::string& text)
  {
    return native::dclx_document::hash(text);
  }

  inline bool DocLangXDocument::read(const std::string& path)
  {
    const bool result = native::reader::read(path, *doc);
    if(result)
      {
        annotation_generation = doc->generation();
      }
    return result;
  }

  inline bool DocLangXDocument::read_xml(const std::string& xml)
  {
    // A plain DCLG buffer must not retain state from a previous DCLX read.
    doc->clear();
    const bool result = doc->read(xml);
    if(result)
      {
        annotation_generation = doc->generation();
      }
    return result;
  }

  inline bool DocLangXDocument::annotations_stale() const
  {
    return doc->has_annotations() and doc->generation() != annotation_generation;
  }

  inline bool DocLangXDocument::write(const std::string& path, bool allow_stale_annotations)
  {
    if(annotations_stale() and not allow_stale_annotations)
      {
        doc->set_last_error("DocLang edits may have shifted annotation XPath references; "
                            "pass allow_stale_annotations=True after reviewing them");
        return false;
      }
    const bool result = native::writer::write_dclx(path, *doc);
    if(result)
      {
        annotation_generation = doc->generation();
      }
    return result;
  }

  inline bool DocLangXDocument::has_archive() const
  {
    return doc->has_archive();
  }

  inline bool DocLangXDocument::has_annotations() const
  {
    return doc->has_annotations();
  }

  inline std::string DocLangXDocument::source_path() const
  {
    return doc->get_source_path().string();
  }

  inline std::vector<std::string> DocLangXDocument::archive_paths() const
  {
    return doc->has_archive() ? doc->artifacts().paths() : std::vector<std::string>{};
  }

  inline std::vector<std::string> DocLangXDocument::annotation_paths() const
  {
    return { native::PROPERTIES_CSV,         native::INSTANCES_CSV,
             native::ENTITIES_CSV,           native::RELATIONS_CSV,
             native::DOCUMENT_REFERENCE_BIB, native::REFERENCES_BIB,
             native::SUMMARY_DCLG,           native::TOC_DCLG,
             native::CONCEPTS_DCLG };
  }

  inline std::optional<std::string> DocLangXDocument::document_reference() const
  {
    return doc->get_document_reference();
  }

  inline std::optional<std::string> DocLangXDocument::references() const
  {
    return doc->get_references();
  }

  inline std::optional<DoclangDocument> DocLangXDocument::summary() const
  {
    return sidecar_wrapper(doc->get_summary());
  }

  inline std::optional<DoclangDocument> DocLangXDocument::toc() const
  {
    return sidecar_wrapper(doc->get_toc());
  }

  inline std::optional<DoclangDocument> DocLangXDocument::concepts() const
  {
    return sidecar_wrapper(doc->get_concepts());
  }

  inline void DocLangXDocument::set_document_reference(const std::string& bibtex)
  {
    doc->set_document_reference(bibtex);
  }

  inline void DocLangXDocument::set_references(const std::string& bibtex)
  {
    doc->set_references(bibtex);
  }

  inline bool DocLangXDocument::set_document_summary(const std::string& dclg)
  {
    return native::set_summary_dclg(*doc, dclg);
  }

  inline bool DocLangXDocument::set_toc(const std::string& dclg)
  {
    return native::set_toc_dclg(*doc, dclg);
  }

  inline bool DocLangXDocument::set_concepts(const std::string& dclg)
  {
    return native::set_concepts_dclg(*doc, dclg);
  }

  inline void DocLangXDocument::clear_document_reference()
  {
    doc->clear_document_reference();
  }

  inline void DocLangXDocument::clear_references()
  {
    doc->clear_references();
  }

  inline void DocLangXDocument::clear_document_summary()
  {
    doc->clear_summary();
  }

  inline void DocLangXDocument::clear_toc()
  {
    doc->clear_toc();
  }

  inline void DocLangXDocument::clear_concepts()
  {
    doc->clear_concepts();
  }

  inline py::dict DocLangXDocument::overview() const
  {
    py::dict result;
    result["valid"] = valid();
    result["source_path"] = source_path();
    result["has_archive"] = has_archive();
    result["has_annotations"] = has_annotations();
    result["properties"] = doc->get_properties().size();
    result["instances"] = doc->get_instances().size();
    result["entities"] = doc->get_entities().size();
    result["relations"] = doc->get_relations().size();
    result["has_document_reference"] = doc->has_document_reference();
    result["has_references"] = doc->has_references();
    result["has_summary"] = doc->has_summary();
    result["has_toc"] = doc->has_toc();
    result["has_concepts"] = doc->has_concepts();
    return result;
  }

  inline py::object DocLangXDocument::properties() const
  {
    return detail::dataframe_from_records(doc->get_properties());
  }

  inline py::object DocLangXDocument::entities() const
  {
    return detail::dataframe_from_records(doc->get_entities());
  }

  inline py::object DocLangXDocument::instances() const
  {
    return detail::dataframe_from_records(doc->get_instances());
  }

  inline py::object DocLangXDocument::relations() const
  {
    return detail::dataframe_from_records(doc->get_relations());
  }

  inline py::object DocLangXDocument::query_properties(const std::string& type,
                                                       const std::string& label,
                                                       const std::string& xpath,
                                                       float min_conf) const
  {
    std::vector<native::base_property> matches;
    for(const auto& record : doc->get_properties())
      {
        if((not type.empty() and record.get_type() != type)
           or (not label.empty() and record.get_label() != label)
           or (not xpath.empty() and record.get_xpath() != xpath) or record.get_conf() < min_conf)
          {
            continue;
          }
        matches.push_back(record);
      }
    return detail::dataframe_from_records(matches);
  }

  inline py::object DocLangXDocument::query_entities(const std::string& type,
                                                     const std::string& subtype,
                                                     const std::string& name,
                                                     const std::string& name_contains,
                                                     std::size_t min_count) const
  {
    std::vector<native::base_entity> matches;
    for(const auto& record : doc->get_entities())
      {
        if((not type.empty() and record.get_type() != type)
           or (not subtype.empty() and record.get_subtype() != subtype)
           or (not name.empty() and record.get_name() != name)
           or (not name_contains.empty()
               and record.get_name().find(name_contains) == std::string::npos)
           or record.get_count() < min_count)
          {
            continue;
          }
        matches.push_back(record);
      }
    return detail::dataframe_from_records(matches);
  }

  inline py::object DocLangXDocument::query_instances(const std::string& type,
                                                      const std::string& subtype,
                                                      const std::string& name,
                                                      const std::string& name_contains,
                                                      const std::string& xpath, float min_conf,
                                                      std::uint64_t entity_hash) const
  {
    std::vector<native::base_instance> matches;
    for(const auto& record : doc->get_instances())
      {
        if((not type.empty() and record.get_type() != type)
           or (not subtype.empty() and record.get_subtype() != subtype)
           or (not name.empty() and record.get_name() != name)
           or (not name_contains.empty()
               and record.get_name().find(name_contains) == std::string::npos)
           or (not xpath.empty() and record.get_xpath() != xpath) or record.get_conf() < min_conf
           or (entity_hash != 0 and record.get_ehash() != entity_hash))
          {
            continue;
          }
        matches.push_back(record);
      }
    return detail::dataframe_from_records(matches);
  }

  inline py::object DocLangXDocument::query_relations(const std::string& name,
                                                      const std::string& name_contains,
                                                      float min_conf, std::uint64_t hash_i,
                                                      std::uint64_t hash_j) const
  {
    std::vector<native::base_relation> matches;
    for(const auto& record : doc->get_relations())
      {
        if((not name.empty() and record.get_name() != name)
           or (not name_contains.empty()
               and record.get_name().find(name_contains) == std::string::npos)
           or record.get_conf() < min_conf or (hash_i != 0 and record.get_hash_i() != hash_i)
           or (hash_j != 0 and record.get_hash_j() != hash_j))
          {
            continue;
          }
        matches.push_back(record);
      }
    return detail::dataframe_from_records(matches);
  }

  inline std::optional<std::pair<std::size_t, std::size_t>>
  DocLangXDocument::table_coordinates(const std::string& xpath) const
  {
    const auto lookup = native::resolve_doclang_path(doc->root(), xpath);
    if(not lookup.found)
      {
        doc->set_last_error(lookup.error);
        return std::nullopt;
      }
    doc->set_last_error("");
    return native::table_coordinates(doc->root(), xpath);
  }

  inline DocLangXDocument::DocLangXDocument(std::shared_ptr<native::dclx_document> value)
      : DoclangDocument(value), doc(std::move(value))
  {
  }

  inline std::optional<DoclangDocument>
  DocLangXDocument::sidecar_wrapper(const native::dclx_document::sidecar_type& sidecar)
  {
    if(not sidecar)
      {
        return std::nullopt;
      }
    return DoclangDocument(sidecar.value());
  }
}

#endif
