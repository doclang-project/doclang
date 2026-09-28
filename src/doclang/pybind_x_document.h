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
#include <doclang/pybind_document.h>
#include <doclang/reader.h>
#include <doclang/writer.h>

namespace doclang::binding
{
  namespace py = pybind11;

  namespace detail
  {
    inline std::string_view pandas_dtype(std::string_view column)
    {
      if(column=="type" or column=="subtype" or column=="xpath" or
         column=="label" or column=="name" or column=="original")
        {
          return "string";
        }
      if(column=="confidence" or column=="conf")
        {
          return "Float32";
        }
      if(column=="ehash" or column=="ihash" or column=="hash_i" or
         column=="hash_j" or column=="char_i" or column=="char_j" or
         column=="count")
        {
          return "UInt64";
        }
      return "";
    }

    template<typename record_type>
    py::object dataframe_from_records(const std::vector<record_type>& records)
    {
      // Import pandas only for callers that request a DataFrame.
      py::module_ pandas = py::module_::import("pandas");
      py::list rows;
      for(const auto& record:records)
        {
          rows.append(py::cast(record.values()));
        }

      py::object frame = pandas.attr("DataFrame")(
        rows, py::arg("columns")=py::cast(record_type::HEADERS));
      py::dict dtypes;
      for(const std::string& column:record_type::HEADERS)
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

  class DocLangXDocument: public DoclangDocument
  {
  public:
    DocLangXDocument(): DocLangXDocument(std::make_shared<native::dclx_document>()) {}

    static std::uint64_t hash(const std::string& text)
    {
      return native::dclx_document::hash(text);
    }

    bool read(const std::string& path)
    {
      return native::reader::read(path, *doc);
    }

    bool read_xml(const std::string& xml) override
    {
      // A plain DCLG buffer must not retain state from a previous DCLX read.
      doc->clear();
      return doc->read(xml);
    }

    bool write(const std::string& path)
    {
      return native::writer::write_dclx(path, *doc);
    }

    bool has_archive() const { return doc->has_archive(); }
    bool has_annotations() const { return doc->has_annotations(); }
    std::string source_path() const { return doc->get_source_path().string(); }

    std::vector<std::string> archive_paths() const
    {
      return doc->has_archive()? doc->artifacts().paths():std::vector<std::string>{};
    }

    std::vector<std::string> annotation_paths() const
    {
      return {native::PROPERTIES_CSV, native::INSTANCES_CSV,
              native::ENTITIES_CSV, native::RELATIONS_CSV,
              native::DOCUMENT_REFERENCE_BIB, native::REFERENCES_BIB,
              native::SUMMARY_DCLG, native::TOC_DCLG, native::CONCEPTS_DCLG};
    }

    std::optional<std::string> document_reference() const
    {
      return doc->get_document_reference();
    }

    std::optional<std::string> references() const
    {
      return doc->get_references();
    }

    std::optional<DoclangDocument> summary() const
    {
      return sidecar_wrapper(doc->get_summary());
    }

    std::optional<DoclangDocument> toc() const
    {
      return sidecar_wrapper(doc->get_toc());
    }

    std::optional<DoclangDocument> concepts() const
    {
      return sidecar_wrapper(doc->get_concepts());
    }

    void set_document_reference(const std::string& bibtex)
    {
      doc->set_document_reference(bibtex);
    }

    void set_references(const std::string& bibtex)
    {
      doc->set_references(bibtex);
    }

    bool set_document_summary(const std::string& dclg)
    {
      return native::set_summary_dclg(*doc, dclg);
    }

    bool set_toc(const std::string& dclg)
    {
      return native::set_toc_dclg(*doc, dclg);
    }

    bool set_concepts(const std::string& dclg)
    {
      return native::set_concepts_dclg(*doc, dclg);
    }

    void clear_document_reference() { doc->clear_document_reference(); }
    void clear_references() { doc->clear_references(); }
    void clear_document_summary() { doc->clear_summary(); }
    void clear_toc() { doc->clear_toc(); }
    void clear_concepts() { doc->clear_concepts(); }

    py::dict overview() const
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

    py::object properties() const
    {
      return detail::dataframe_from_records(doc->get_properties());
    }

    py::object entities() const
    {
      return detail::dataframe_from_records(doc->get_entities());
    }

    py::object instances() const
    {
      return detail::dataframe_from_records(doc->get_instances());
    }

    py::object relations() const
    {
      return detail::dataframe_from_records(doc->get_relations());
    }

    py::object query_properties(const std::string& type="",
                                const std::string& label="",
                                const std::string& xpath="",
                                float min_conf=0.0f) const
    {
      std::vector<native::base_property> matches;
      for(const auto& record:doc->get_properties())
        {
          if((not type.empty() and record.get_type()!=type) or
             (not label.empty() and record.get_label()!=label) or
             (not xpath.empty() and record.get_xpath()!=xpath) or
             record.get_conf()<min_conf)
            {
              continue;
            }
          matches.push_back(record);
        }
      return detail::dataframe_from_records(matches);
    }

    py::object query_entities(const std::string& type="",
                              const std::string& subtype="",
                              const std::string& name="",
                              const std::string& name_contains="",
                              std::size_t min_count=0) const
    {
      std::vector<native::base_entity> matches;
      for(const auto& record:doc->get_entities())
        {
          if((not type.empty() and record.get_type()!=type) or
             (not subtype.empty() and record.get_subtype()!=subtype) or
             (not name.empty() and record.get_name()!=name) or
             (not name_contains.empty() and
              record.get_name().find(name_contains)==std::string::npos) or
             record.get_count()<min_count)
            {
              continue;
            }
          matches.push_back(record);
        }
      return detail::dataframe_from_records(matches);
    }

    py::object query_instances(const std::string& type="",
                               const std::string& subtype="",
                               const std::string& name="",
                               const std::string& name_contains="",
                               const std::string& xpath="",
                               float min_conf=0.0f,
                               std::uint64_t entity_hash=0) const
    {
      std::vector<native::base_instance> matches;
      for(const auto& record:doc->get_instances())
        {
          if((not type.empty() and record.get_type()!=type) or
             (not subtype.empty() and record.get_subtype()!=subtype) or
             (not name.empty() and record.get_name()!=name) or
             (not name_contains.empty() and
              record.get_name().find(name_contains)==std::string::npos) or
             (not xpath.empty() and record.get_xpath()!=xpath) or
             record.get_conf()<min_conf or
             (entity_hash!=0 and record.get_ehash()!=entity_hash))
            {
              continue;
            }
          matches.push_back(record);
        }
      return detail::dataframe_from_records(matches);
    }

    py::object query_relations(const std::string& name="",
                               const std::string& name_contains="",
                               float min_conf=0.0f,
                               std::uint64_t hash_i=0,
                               std::uint64_t hash_j=0) const
    {
      std::vector<native::base_relation> matches;
      for(const auto& record:doc->get_relations())
        {
          if((not name.empty() and record.get_name()!=name) or
             (not name_contains.empty() and
              record.get_name().find(name_contains)==std::string::npos) or
             record.get_conf()<min_conf or
             (hash_i!=0 and record.get_hash_i()!=hash_i) or
             (hash_j!=0 and record.get_hash_j()!=hash_j))
            {
              continue;
            }
          matches.push_back(record);
        }
      return detail::dataframe_from_records(matches);
    }

    std::optional<std::pair<std::size_t, std::size_t>>
    table_coordinates(const std::string& xpath) const
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

  private:
    explicit DocLangXDocument(std::shared_ptr<native::dclx_document> value):
      DoclangDocument(value), doc(std::move(value))
    {}

    static std::optional<DoclangDocument> sidecar_wrapper(
      const native::dclx_document::sidecar_type& sidecar)
    {
      if(not sidecar) return std::nullopt;
      return DoclangDocument(sidecar.value());
    }

    std::shared_ptr<native::dclx_document> doc;
  };
}

#endif
