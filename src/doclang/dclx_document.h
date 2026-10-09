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

namespace doclang::native
{

  class dclx_document : public dclg_document
  {
  public:

    // summary, ToC and concepts are DCLG sidecars: parsed, never raw strings
    typedef std::optional<std::shared_ptr<dclg_document>> sidecar_type;

    dclx_document() = default;

    void clear();

    void set_source_path(std::filesystem::path path)
    {
      source_path = std::move(path);
    }
    const std::filesystem::path& get_source_path() const
    {
      return source_path;
    }

    bool has_archive() const
    {
      return artifact_archive.has_value();
    }

    archive& artifacts()
    {
      return artifact_archive.value();
    }
    const archive& artifacts() const
    {
      return artifact_archive.value();
    }

    void set_archive(archive value)
    {
      artifact_archive = std::move(value);
    }
    void clear_archive()
    {
      artifact_archive.reset();
    }

    std::shared_ptr<std::vector<base_property>> shared_properties()
    {
      return properties;
    }
    std::shared_ptr<std::vector<base_instance>> shared_instances()
    {
      return instances;
    }
    std::shared_ptr<std::vector<base_entity>> shared_entities()
    {
      return entities;
    }
    std::shared_ptr<std::vector<base_relation>> shared_relations()
    {
      return relations;
    }

    std::vector<base_property>& mutable_properties()
    {
      return *properties;
    }
    std::vector<base_instance>& mutable_instances()
    {
      return *instances;
    }
    std::vector<base_entity>& mutable_entities()
    {
      return *entities;
    }
    std::vector<base_relation>& mutable_relations()
    {
      return *relations;
    }

    const std::vector<base_property>& get_properties() const
    {
      return *properties;
    }
    const std::vector<base_instance>& get_instances() const
    {
      return *instances;
    }
    const std::vector<base_entity>& get_entities() const
    {
      return *entities;
    }
    const std::vector<base_relation>& get_relations() const
    {
      return *relations;
    }

    bool has_annotations() const;
    void clear_annotations();
    void compute_entities();

    bool has_document_reference() const
    {
      return document_reference.has_value();
    }
    bool has_references() const
    {
      return references.has_value();
    }
    bool has_summary() const
    {
      return summary.has_value();
    }
    bool has_toc() const
    {
      return toc.has_value();
    }
    bool has_concepts() const
    {
      return concepts.has_value();
    }

    const std::optional<std::string>& get_document_reference() const
    {
      return document_reference;
    }
    const std::optional<std::string>& get_references() const
    {
      return references;
    }
    const sidecar_type& get_summary() const
    {
      return summary;
    }
    const sidecar_type& get_toc() const
    {
      return toc;
    }
    const sidecar_type& get_concepts() const
    {
      return concepts;
    }

    void set_document_reference(std::string value)
    {
      document_reference = std::move(value);
    }
    void set_references(std::string value)
    {
      references = std::move(value);
    }
    void set_summary(std::shared_ptr<dclg_document> value)
    {
      summary = std::move(value);
    }
    void set_toc(std::shared_ptr<dclg_document> value)
    {
      toc = std::move(value);
    }
    void set_concepts(std::shared_ptr<dclg_document> value)
    {
      concepts = std::move(value);
    }

    void clear_document_reference()
    {
      document_reference.reset();
    }
    void clear_references()
    {
      references.reset();
    }
    void clear_summary()
    {
      summary.reset();
    }
    void clear_toc()
    {
      toc.reset();
    }
    void clear_concepts()
    {
      concepts.reset();
    }

  private:

    std::shared_ptr<std::vector<base_property>> properties
        = std::make_shared<std::vector<base_property>>();
    std::shared_ptr<std::vector<base_instance>> instances
        = std::make_shared<std::vector<base_instance>>();
    std::shared_ptr<std::vector<base_entity>> entities
        = std::make_shared<std::vector<base_entity>>();
    std::shared_ptr<std::vector<base_relation>> relations
        = std::make_shared<std::vector<base_relation>>();

    std::optional<std::string> document_reference;
    std::optional<std::string> references;
    sidecar_type summary;
    sidecar_type toc;
    sidecar_type concepts;

    std::optional<archive> artifact_archive;
    std::filesystem::path source_path;
  };

  inline void dclx_document::clear()
  {
    dclg_document::clear();

    clear_annotations();
    clear_document_reference();
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
           or (not relations->empty()) or has_document_reference() or has_references()
           or has_summary() or has_toc() or has_concepts();
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
