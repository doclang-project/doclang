#ifndef DOCLANG_PYBIND_X_DOCUMENT_H_
#define DOCLANG_PYBIND_X_DOCUMENT_H_

#include <cstddef>
#include <cstdint>
#include <functional>
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
#include <doclang/opc.h>
#include <pybind/doclang_document.h>

namespace doclang::binding
{
  namespace py = pybind11;

  class DocLangXDocument : public DoclangDocument
  {
  public:

    DocLangXDocument();

    static std::uint64_t hash(const std::string& text);
    bool read(const std::string& path, const native::archive::limits& bounds = {});
    bool read_bytes(py::bytes data, const native::archive::limits& bounds = {});
    bool read_xml(const std::string& xml) override;
    bool write(const std::string& path, bool allow_stale_annotations = false,
               bool allow_stale_sidecars = false);
    py::bytes write_bytes(bool allow_stale_annotations = false, bool allow_stale_sidecars = false);
    bool annotations_stale() const;
    bool sidecars_stale() const;
    bool has_archive() const;
    bool has_annotations() const;
    std::string source_path() const;
    std::vector<std::string> archive_paths() const;
    std::optional<py::bytes> get_part_bytes(const std::string& path) const;
    std::optional<std::string> get_part_text(const std::string& path) const;
    void set_part_bytes(const std::string& path, py::bytes data, const std::string& content_type);
    void set_part_text(const std::string& path, const std::string& data,
                       const std::string& content_type);
    void remove_part(const std::string& path);
    py::dict validate_package() const;
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
    bool set_summary_document(const DoclangDocument& value);
    bool set_toc_document(const DoclangDocument& value);
    bool set_concepts_document(const DoclangDocument& value);
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
    std::size_t summary_generation = 0;
    std::size_t toc_generation = 0;
    std::size_t concepts_generation = 0;
    bool can_write(bool allow_stale_annotations, bool allow_stale_sidecars);
    void reset_generations();
    static bool protected_part(const std::string& path);
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

  inline void DocLangXDocument::reset_generations()
  {
    annotation_generation = doc->generation();
    summary_generation = doc->generation();
    toc_generation = doc->generation();
    concepts_generation = doc->generation();
  }

  inline bool DocLangXDocument::read(const std::string& path, const native::archive::limits& bounds)
  {
    const bool result = native::reader::read(path, *doc, bounds);
    if(result)
      {
        reset_generations();
      }
    return result;
  }

  inline bool DocLangXDocument::read_bytes(py::bytes data, const native::archive::limits& bounds)
  {
    const std::string buffer = data;
    const auto* ptr = reinterpret_cast<const std::byte*>(buffer.data());
    const bool result = native::reader::read_dclx_buffer(
        std::span<const std::byte>(ptr, buffer.size()), *doc, bounds);
    if(result)
      {
        reset_generations();
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
        reset_generations();
      }
    return result;
  }

  inline bool DocLangXDocument::annotations_stale() const
  {
    return (not doc->get_properties().empty() or not doc->get_instances().empty()
            or not doc->get_entities().empty() or not doc->get_relations().empty())
           and doc->generation() != annotation_generation;
  }

  inline bool DocLangXDocument::sidecars_stale() const
  {
    return (doc->has_summary() and summary_generation != doc->generation())
           or (doc->has_toc() and toc_generation != doc->generation())
           or (doc->has_concepts() and concepts_generation != doc->generation());
  }

  inline bool DocLangXDocument::can_write(bool allow_stale_annotations, bool allow_stale_sidecars)
  {
    if(annotations_stale() and not allow_stale_annotations)
      {
        doc->set_last_error("DocLang edits may have shifted annotation XPath references; "
                            "pass allow_stale_annotations=True after reviewing them");
        return false;
      }
    if(sidecars_stale() and not allow_stale_sidecars)
      {
        doc->set_last_error("DocLang edits may have invalidated sidecars; "
                            "repair them or pass allow_stale_sidecars=True after review");
        return false;
      }
    if(doc->has_toc())
      {
        std::string error;
        if(not native::validate_toc_targets(*doc, *doc->get_toc().value(), error))
          {
            doc->set_last_error(error);
            return false;
          }
      }
    return true;
  }

  inline bool DocLangXDocument::write(const std::string& path, bool allow_stale_annotations,
                                      bool allow_stale_sidecars)
  {
    if(not can_write(allow_stale_annotations, allow_stale_sidecars))
      {
        return false;
      }
    const bool result = native::writer::write_dclx(path, *doc);
    if(result)
      {
        reset_generations();
      }
    return result;
  }

  inline py::bytes DocLangXDocument::write_bytes(bool allow_stale_annotations,
                                                 bool allow_stale_sidecars)
  {
    if(not can_write(allow_stale_annotations, allow_stale_sidecars))
      {
        throw py::value_error(doc->get_last_error());
      }
    std::vector<std::byte> buffer;
    if(not native::writer::write_dclx_buffer(*doc, buffer))
      {
        throw py::value_error(doc->get_last_error());
      }
    reset_generations();
    return py::bytes(reinterpret_cast<const char*>(buffer.data()), buffer.size());
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

  inline bool DocLangXDocument::protected_part(const std::string& path)
  {
    return path == "document.xml" or path == "[Content_Types].xml" or path == "_rels/.rels"
           or path.rfind("annotations/", 0) == 0;
  }

  inline std::optional<py::bytes> DocLangXDocument::get_part_bytes(const std::string& path) const
  {
    if(not native::archive::valid_path(path))
      {
        throw py::value_error("invalid dclx part path");
      }
    if(not doc->has_archive())
      {
        return std::nullopt;
      }
    const auto part = doc->artifacts().bytes(path);
    if(not part)
      {
        return std::nullopt;
      }
    return py::bytes(reinterpret_cast<const char*>(part->data()), part->size());
  }

  inline std::optional<std::string> DocLangXDocument::get_part_text(const std::string& path) const
  {
    const auto part = get_part_bytes(path);
    if(not part)
      {
        return std::nullopt;
      }
    return part->attr("decode")("utf-8").cast<std::string>();
  }

  inline void DocLangXDocument::set_part_bytes(const std::string& path, py::bytes data,
                                               const std::string& content_type)
  {
    if(not native::archive::valid_path(path) or protected_part(path))
      {
        throw py::value_error("reserved or invalid dclx part path");
      }
    if(not doc->has_archive())
      {
        doc->set_archive(native::archive{});
      }
    const std::string value = data;
    std::string error;
    if(not native::set_part_content_type(doc->artifacts(), path, content_type, error))
      {
        throw py::value_error(error);
      }
    const auto* ptr = reinterpret_cast<const std::byte*>(value.data());
    doc->artifacts().set_bytes(path, std::span<const std::byte>(ptr, value.size()));
  }

  inline void DocLangXDocument::set_part_text(const std::string& path, const std::string& data,
                                              const std::string& content_type)
  {
    set_part_bytes(path, py::bytes(data), content_type);
  }

  inline void DocLangXDocument::remove_part(const std::string& path)
  {
    if(not native::archive::valid_path(path) or protected_part(path))
      {
        throw py::value_error("reserved or invalid dclx part path");
      }
    if(doc->has_archive())
      {
        doc->artifacts().erase(path);
        native::remove_part_content_type(doc->artifacts(), path);
      }
  }

  inline py::dict DocLangXDocument::validate_package() const
  {
    py::list errors;
    auto add_error
        = [&](const std::string& code, const std::string& path, const std::string& message) {
            py::dict issue;
            issue["code"] = code;
            issue["path"] = path;
            issue["message"] = message;
            errors.append(issue);
          };
    if(not valid())
      {
        add_error("invalid_document", "document.xml", "invalid DocLang XML");
      }
    else
      {
        native::validation_options options;
        options.allow_empty_namespace = true;
        const auto report = doc->validate(options);
        if(not report.ok())
          {
            add_error("invalid_document", "document.xml", report.first_error());
          }
      }
    if(doc->has_toc())
      {
        std::string error;
        if(not native::validate_toc_targets(*doc, *doc->get_toc().value(), error))
          {
            add_error("invalid_toc_target", native::TOC_DCLG, error);
          }
      }
    if(annotations_stale())
      {
        add_error("stale_annotations", "annotations/", "annotation XPaths may be stale");
      }
    if(sidecars_stale())
      {
        add_error("stale_sidecars", "annotations/", "sidecars may be stale");
      }
    if(doc->has_archive())
      {
        const auto& zip = doc->artifacts();
        pugi::xml_document types;
        const auto type_text = zip.text("[Content_Types].xml");
        if(not type_text or not types.load_string(std::string(*type_text).c_str())
           or not types.child("Types"))
          {
            add_error("invalid_content_types", "[Content_Types].xml",
                      "missing or invalid content types");
          }
        else
          {
            if(std::string_view(types.child("Types").attribute("xmlns").value())
               != native::OPC_TYPES_NS)
              {
                add_error("invalid_content_types_namespace", "[Content_Types].xml",
                          "unexpected content types namespace");
              }
            bool main_type = false;
            bool rels_type = false;
            for(auto entry : types.child("Types").children("Override"))
              {
                if(std::string_view(entry.attribute("PartName").value()) == "/document.xml"
                   and std::string_view(entry.attribute("ContentType").value())
                           == "application/vnd.doclang.document+xml")
                  {
                    main_type = true;
                  }
              }
            for(auto entry : types.child("Types").children("Default"))
              {
                if(std::string_view(entry.attribute("Extension").value()) == "rels"
                   and std::string_view(entry.attribute("ContentType").value())
                           == "application/vnd.openxmlformats-package.relationships+xml")
                  {
                    rels_type = true;
                  }
              }
            if(not main_type)
              {
                add_error("invalid_document_type", "[Content_Types].xml",
                          "main document type missing");
              }
            if(not rels_type)
              {
                add_error("invalid_relationship_type", "[Content_Types].xml",
                          "relationship type missing");
              }
          }
        pugi::xml_document rels;
        const auto rel_text = zip.text("_rels/.rels");
        if(not rel_text or not rels.load_string(std::string(*rel_text).c_str())
           or not rels.child("Relationships"))
          {
            add_error("invalid_relationships", "_rels/.rels", "missing or invalid relationships");
          }
        else
          {
            if(std::string_view(rels.child("Relationships").attribute("xmlns").value())
               != native::OPC_RELS_NS)
              {
                add_error("invalid_relationships_namespace", "_rels/.rels",
                          "unexpected relationships namespace");
              }
            std::size_t document_relations = 0;
            for(auto relation : rels.child("Relationships").children("Relationship"))
              {
                if(std::string_view(relation.attribute("Type").value()) == native::DOCLANG_REL_TYPE)
                  {
                    document_relations += 1;
                    if(std::string_view(relation.attribute("Target").value()) != "document.xml")
                      {
                        add_error("bad_document_target", "_rels/.rels",
                                  "document target is not document.xml");
                      }
                  }
              }
            if(document_relations != 1)
              {
                add_error("document_relation_count", "_rels/.rels",
                          "exactly one main document relationship is required");
              }
          }
        for(const auto& path : zip.paths())
          {
            if(not native::archive::valid_path(path))
              {
                add_error("invalid_part_path", path, "invalid package part path");
              }
            if(path == "[Content_Types].xml" or path == "_rels/.rels")
              {
                continue;
              }
            bool declared = false;
            for(auto entry : types.child("Types").children("Override"))
              {
                if(std::string_view(entry.attribute("PartName").value()) == "/" + path
                   and not std::string_view(entry.attribute("ContentType").value()).empty())
                  {
                    declared = true;
                  }
              }
            const auto dot = path.find_last_of('.');
            if(dot != std::string::npos)
              {
                for(auto entry : types.child("Types").children("Default"))
                  {
                    if(std::string_view(entry.attribute("Extension").value())
                           == path.substr(dot + 1)
                       and not std::string_view(entry.attribute("ContentType").value()).empty())
                      {
                        declared = true;
                      }
                  }
              }
            if(not declared)
              {
                add_error("undeclared_part", path, "part has no content type override");
              }
          }
        if(valid())
          {
            std::size_t page_count = 1;
            std::size_t track_count = 0;
            std::function<void(pugi::xml_node)> count_structure = [&](pugi::xml_node node) {
              if(std::string_view(node.name()) == "page_break")
                {
                  page_count += 1;
                }
              if(std::string_view(node.name()) == "track")
                {
                  track_count += 1;
                }
              for(auto child : node.children())
                {
                  if(child.type() == pugi::node_element)
                    {
                      count_structure(child);
                    }
                }
            };
            count_structure(doc->root());
            for(const auto& path : zip.paths())
              {
                std::size_t maximum = 0;
                std::string category;
                if(path.rfind("pages/", 0) == 0)
                  {
                    maximum = page_count;
                    category = "page";
                  }
                else if(path.rfind("audio/", 0) == 0 or path.rfind("video/", 0) == 0)
                  {
                    maximum = track_count;
                    category = "track";
                  }
                else
                  {
                    continue;
                  }
                const auto slash = path.find('/');
                const auto dot = path.find('.', slash + 1);
                bool valid_number = dot != std::string::npos and dot > slash + 1
                                    and path.find('/', slash + 1) == std::string::npos;
                std::size_t number = 0;
                if(valid_number)
                  {
                    for(std::size_t i = slash + 1; i < dot; ++i)
                      {
                        if(path[i] < '0' or path[i] > '9' or number > maximum)
                          {
                            valid_number = false;
                            break;
                          }
                        number = number * 10 + static_cast<std::size_t>(path[i] - '0');
                      }
                  }
                if(not valid_number or number == 0 or number > maximum)
                  {
                    add_error("invalid_media_index", path,
                              category + " index exceeds document structure");
                  }
              }
            std::function<void(pugi::xml_node)> check_sources = [&](pugi::xml_node node) {
              if(std::string_view(node.name()) == "src")
                {
                  const std::string uri = node.attribute("uri").value();
                  if(uri.find(':') == std::string::npos and uri.rfind("//", 0) != 0
                     and not zip.has(uri))
                    {
                      add_error("missing_source_part", uri, "relative src URI has no package part");
                    }
                }
              for(auto child : node.children())
                {
                  if(child.type() == pugi::node_element)
                    {
                      check_sources(child);
                    }
                }
            };
            check_sources(doc->root());
          }
      }
    py::dict result;
    result["ok"] = py::len(errors) == 0;
    result["errors"] = errors;
    return result;
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
    const bool result = native::set_summary_dclg(*doc, dclg);
    if(result)
      {
        summary_generation = doc->generation();
      }
    return result;
  }

  inline bool DocLangXDocument::set_toc(const std::string& dclg)
  {
    const bool result = native::set_toc_dclg(*doc, dclg);
    if(result)
      {
        toc_generation = doc->generation();
      }
    return result;
  }

  inline bool DocLangXDocument::set_concepts(const std::string& dclg)
  {
    const bool result = native::set_concepts_dclg(*doc, dclg);
    if(result)
      {
        concepts_generation = doc->generation();
      }
    return result;
  }

  inline bool DocLangXDocument::set_summary_document(const DoclangDocument& value)
  {
    return set_document_summary(value.xml());
  }

  inline bool DocLangXDocument::set_toc_document(const DoclangDocument& value)
  {
    return set_toc(value.xml());
  }

  inline bool DocLangXDocument::set_concepts_document(const DoclangDocument& value)
  {
    return set_concepts(value.xml());
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
