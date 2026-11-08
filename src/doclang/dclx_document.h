//-*-C++-*-

#ifndef DOCLANG_NATIVE_DCLX_DOCUMENT_H_
#define DOCLANG_NATIVE_DCLX_DOCUMENT_H_

#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <pugixml.hpp>

#include <doclang/records.h>
#include <doclang/archive.h>
#include <doclang/content.h>
#include <doclang/dclg_document.h>
#include <doclang/opc.h>
#include <doclang/source.h>

namespace doclang::native
{

  class dclx_document : public dclg_document
  {
  public:

    // Named companion documents are parsed DCLG, never raw strings.
    typedef std::optional<std::shared_ptr<dclg_document>> sidecar_type;

    dclx_document();

    /* state */
    void clear();

    void set_source_path(std::filesystem::path path);
    const std::filesystem::path& get_source_path() const;

    /* archive parts */
    bool has_archive() const;

    archive& artifacts();
    const archive& artifacts() const;

    void set_archive(archive value);
    void clear_archive();

    /* original source */
    bool has_source() const;
    std::optional<std::pair<std::span<const std::byte>, std::string>> get_source() const;
    bool set_source(std::span<const std::byte> data, std::string_view mimetype);
    void clear_source();

    /* graph annotations */
    std::shared_ptr<std::vector<base_property>> shared_properties();
    std::shared_ptr<std::vector<base_instance>> shared_instances();
    std::shared_ptr<std::vector<base_entity>> shared_entities();
    std::shared_ptr<std::vector<base_relation>> shared_relations();

    /* graph annotations: writing */
    std::vector<base_property>& mutable_properties();
    std::vector<base_instance>& mutable_instances();
    std::vector<base_entity>& mutable_entities();
    std::vector<base_relation>& mutable_relations();

    /* graph annotations: reading */
    const std::vector<base_property>& get_properties() const;
    const std::vector<base_instance>& get_instances() const;
    const std::vector<base_entity>& get_entities() const;
    const std::vector<base_relation>& get_relations() const;

    /* graph annotations: maintenance */
    bool has_annotations() const;
    void clear_annotations();
    void compute_entities();

    /* companion documents: reading */
    bool has_references() const;
    bool has_summary() const;
    bool has_toc() const;
    bool has_concepts() const;

    const sidecar_type& get_references() const;
    const sidecar_type& get_summary() const;
    const sidecar_type& get_toc() const;
    const sidecar_type& get_concepts() const;

    /* companion documents: writing */
    void set_references(std::shared_ptr<dclg_document> value);
    void set_summary(std::shared_ptr<dclg_document> value);
    void set_toc(std::shared_ptr<dclg_document> value);
    void set_concepts(std::shared_ptr<dclg_document> value);

    void clear_references();
    void clear_summary();
    void clear_toc();
    void clear_concepts();

  private:

    /* state */
    std::shared_ptr<std::vector<base_property>> properties
        = std::make_shared<std::vector<base_property>>();
    std::shared_ptr<std::vector<base_instance>> instances
        = std::make_shared<std::vector<base_instance>>();
    std::shared_ptr<std::vector<base_entity>> entities
        = std::make_shared<std::vector<base_entity>>();
    std::shared_ptr<std::vector<base_relation>> relations
        = std::make_shared<std::vector<base_relation>>();

    sidecar_type references;
    sidecar_type summary;
    sidecar_type toc;
    sidecar_type concepts;

    std::optional<archive> artifact_archive;
    std::filesystem::path source_path;
  };

  inline dclx_document::dclx_document() = default;

  inline bool dclx_document::has_source() const
  {
    return has_archive() and artifacts().has(SOURCE_MIMETYPE) and artifacts().has(SOURCE_DOCUMENT);
  }

  inline std::optional<std::pair<std::span<const std::byte>, std::string>>
  dclx_document::get_source() const
  {
    if(not has_archive())
      {
        return std::nullopt;
      }
    std::string error;
    if(not validate_source_parts(artifacts(), error))
      {
        throw std::runtime_error(error);
      }
    if(not has_source())
      {
        return std::nullopt;
      }
    const auto data = artifacts().bytes(SOURCE_DOCUMENT);
    if(not data)
      {
        throw std::runtime_error("could not read source/document");
      }
    return std::make_pair(*data, source_mimetype(artifacts()));
  }

  inline bool dclx_document::set_source(std::span<const std::byte> data, std::string_view mimetype)
  {
    if(not valid_source_mimetype(mimetype))
      {
        set_last_error("invalid source MIME type; expected type/subtype");
        return false;
      }
    archive updated = has_archive() ? artifacts() : archive{};
    std::string error;
    if(not set_part_content_type(updated, SOURCE_MIMETYPE, "text/plain", error)
       or not set_part_content_type(updated, SOURCE_DOCUMENT, mimetype, error))
      {
        set_last_error(error);
        return false;
      }
    updated.set_text(SOURCE_MIMETYPE, mimetype);
    updated.set_bytes(SOURCE_DOCUMENT, data);
    set_archive(std::move(updated));
    set_last_error("");
    return true;
  }

  inline void dclx_document::clear_source()
  {
    if(has_archive())
      {
        artifacts().erase(SOURCE_MIMETYPE);
        artifacts().erase(SOURCE_DOCUMENT);
        remove_part_content_type(artifacts(), SOURCE_MIMETYPE);
        remove_part_content_type(artifacts(), SOURCE_DOCUMENT);
      }
  }

  inline void dclx_document::set_source_path(std::filesystem::path path)
  {
    source_path = std::move(path);
  }
  inline const std::filesystem::path& dclx_document::get_source_path() const
  {
    return source_path;
  }
  inline bool dclx_document::has_archive() const
  {
    return artifact_archive.has_value();
  }
  inline archive& dclx_document::artifacts()
  {
    return artifact_archive.value();
  }
  inline const archive& dclx_document::artifacts() const
  {
    return artifact_archive.value();
  }
  inline void dclx_document::set_archive(archive value)
  {
    artifact_archive = std::move(value);
  }
  inline void dclx_document::clear_archive()
  {
    artifact_archive.reset();
  }
  inline std::shared_ptr<std::vector<base_property>> dclx_document::shared_properties()
  {
    return properties;
  }
  inline std::shared_ptr<std::vector<base_instance>> dclx_document::shared_instances()
  {
    return instances;
  }
  inline std::shared_ptr<std::vector<base_entity>> dclx_document::shared_entities()
  {
    return entities;
  }
  inline std::shared_ptr<std::vector<base_relation>> dclx_document::shared_relations()
  {
    return relations;
  }
  inline std::vector<base_property>& dclx_document::mutable_properties()
  {
    return *properties;
  }
  inline std::vector<base_instance>& dclx_document::mutable_instances()
  {
    return *instances;
  }
  inline std::vector<base_entity>& dclx_document::mutable_entities()
  {
    return *entities;
  }
  inline std::vector<base_relation>& dclx_document::mutable_relations()
  {
    return *relations;
  }
  inline const std::vector<base_property>& dclx_document::get_properties() const
  {
    return *properties;
  }
  inline const std::vector<base_instance>& dclx_document::get_instances() const
  {
    return *instances;
  }
  inline const std::vector<base_entity>& dclx_document::get_entities() const
  {
    return *entities;
  }
  inline const std::vector<base_relation>& dclx_document::get_relations() const
  {
    return *relations;
  }
  inline bool dclx_document::has_references() const
  {
    return references.has_value();
  }
  inline bool dclx_document::has_summary() const
  {
    return summary.has_value();
  }
  inline bool dclx_document::has_toc() const
  {
    return toc.has_value();
  }
  inline bool dclx_document::has_concepts() const
  {
    return concepts.has_value();
  }
  inline const dclx_document::sidecar_type& dclx_document::get_references() const
  {
    return references;
  }
  inline const dclx_document::sidecar_type& dclx_document::get_summary() const
  {
    return summary;
  }
  inline const dclx_document::sidecar_type& dclx_document::get_toc() const
  {
    return toc;
  }
  inline const dclx_document::sidecar_type& dclx_document::get_concepts() const
  {
    return concepts;
  }
  inline void dclx_document::set_references(std::shared_ptr<dclg_document> value)
  {
    references = std::move(value);
  }
  inline void dclx_document::set_summary(std::shared_ptr<dclg_document> value)
  {
    summary = std::move(value);
  }
  inline void dclx_document::set_toc(std::shared_ptr<dclg_document> value)
  {
    toc = std::move(value);
  }
  inline void dclx_document::set_concepts(std::shared_ptr<dclg_document> value)
  {
    concepts = std::move(value);
  }
  inline void dclx_document::clear_references()
  {
    references.reset();
  }
  inline void dclx_document::clear_summary()
  {
    summary.reset();
  }
  inline void dclx_document::clear_toc()
  {
    toc.reset();
  }
  inline void dclx_document::clear_concepts()
  {
    concepts.reset();
  }

  inline void dclx_document::clear()
  {
    dclg_document::clear();

    clear_annotations();
    clear_references();
    clear_summary();
    clear_toc();
    clear_concepts();
    artifact_archive.reset();
    source_path.clear();
  }

  inline bool dclx_document::has_annotations() const
  {
    return (not properties->empty()) or (not instances->empty()) or (not entities->empty())
           or (not relations->empty()) or has_references() or has_summary() or has_toc()
           or has_concepts();
  }

  inline void dclx_document::clear_annotations()
  {
    properties->clear();
    instances->clear();
    entities->clear();
    relations->clear();
  }

  inline void dclx_document::compute_entities()
  {
    *entities = compute_entities_from_instances(*instances);
  }

}

#endif
