#ifndef DOCLANG_NATIVE_OPC_H_
#define DOCLANG_NATIVE_OPC_H_

#include <string>
#include <string_view>
#include <pugixml.hpp>
#include <doclang/archive.h>
#include <doclang/content.h>

namespace doclang::native
{
  inline constexpr const char* OPC_TYPES_NS
      = "http://schemas.openxmlformats.org/package/2006/content-types";
  inline constexpr const char* OPC_RELS_NS
      = "http://schemas.openxmlformats.org/package/2006/relationships";
  inline constexpr const char* DOCLANG_REL_TYPE
      = "http://doclang.ai/ns/package/2026/relationships/document";

  inline std::string default_part_type(std::string_view path)
  {
    if(path == "document.xml" or (path.size() >= 5 and path.substr(path.size() - 5) == ".dclg"))
      {
        return "application/vnd.doclang.document+xml";
      }
    if(path.size() >= 4 and path.substr(path.size() - 4) == ".csv")
      {
        return "text/csv";
      }
    if(path.size() >= 4 and path.substr(path.size() - 4) == ".bib")
      {
        return "application/x-bibtex";
      }
    if(path.size() >= 4 and path.substr(path.size() - 4) == ".png")
      {
        return "image/png";
      }
    if(path.size() >= 4 and path.substr(path.size() - 4) == ".jpg")
      {
        return "image/jpeg";
      }
    if(path.size() >= 5 and path.substr(path.size() - 5) == ".jpeg")
      {
        return "image/jpeg";
      }
    if(path.size() >= 4 and path.substr(path.size() - 4) == ".xml")
      {
        return "application/xml";
      }
    return "application/octet-stream";
  }

  inline bool set_part_content_type(archive& zip, std::string_view path,
                                    std::string_view content_type, std::string& error)
  {
    if(not archive::valid_path(path) or content_type.empty()
       or content_type.find_first_of("\r\n") != content_type.npos)
      {
        error = "invalid part path or content type";
        return false;
      }
    pugi::xml_document types;
    if(const auto existing = zip.text("[Content_Types].xml"))
      {
        if(not types.load_string(std::string(*existing).c_str()))
          {
            error = "invalid [Content_Types].xml";
            return false;
          }
      }
    auto root = types.child("Types");
    if(not root)
      {
        root = types.append_child("Types");
      }
    if(not root.attribute("xmlns"))
      {
        root.append_attribute("xmlns");
      }
    root.attribute("xmlns").set_value(OPC_TYPES_NS);
    const std::string part_name = "/" + std::string(path);
    pugi::xml_node entry;
    for(auto candidate : root.children("Override"))
      {
        if(std::string_view(candidate.attribute("PartName").value()) == part_name)
          {
            entry = candidate;
            break;
          }
      }
    if(not entry)
      {
        entry = root.append_child("Override");
      }
    if(not entry.attribute("PartName"))
      {
        entry.append_attribute("PartName");
      }
    if(not entry.attribute("ContentType"))
      {
        entry.append_attribute("ContentType");
      }
    entry.attribute("PartName").set_value(part_name.c_str());
    entry.attribute("ContentType").set_value(std::string(content_type).c_str());
    zip.set_text("[Content_Types].xml", serialize_xml(types));
    return true;
  }

  inline bool prepare_opc(archive& zip, std::string& error)
  {
    for(const auto& path : zip.paths())
      {
        if(path == "[Content_Types].xml" or path == "_rels/.rels")
          {
            continue;
          }
        pugi::xml_document types;
        const auto existing = zip.text("[Content_Types].xml");
        if(existing and not types.load_string(std::string(*existing).c_str()))
          {
            error = "invalid [Content_Types].xml";
            return false;
          }
        bool declared = false;
        for(auto node : types.child("Types").children("Override"))
          {
            if(std::string_view(node.attribute("PartName").value()) == "/" + path)
              {
                declared = true;
                break;
              }
          }
        if((not declared or path == "document.xml")
           and not set_part_content_type(zip, path, default_part_type(path), error))
          {
            return false;
          }
      }
    pugi::xml_document types;
    const auto type_text = zip.text("[Content_Types].xml");
    if(not type_text or not types.load_string(std::string(*type_text).c_str()))
      {
        error = "invalid [Content_Types].xml";
        return false;
      }
    auto type_root = types.child("Types");
    for(auto entry = type_root.child("Override"); entry;)
      {
        auto next = entry.next_sibling("Override");
        const std::string part_name = entry.attribute("PartName").value();
        if(part_name.empty() or part_name.front() != '/' or not zip.has(part_name.substr(1)))
          {
            type_root.remove_child(entry);
          }
        entry = next;
      }
    bool rels_type = false;
    for(auto entry : type_root.children("Default"))
      {
        if(std::string_view(entry.attribute("Extension").value()) == "rels")
          {
            if(not entry.attribute("ContentType"))
              {
                entry.append_attribute("ContentType");
              }
            entry.attribute("ContentType")
                .set_value("application/vnd.openxmlformats-package.relationships+xml");
            rels_type = true;
          }
      }
    if(not rels_type)
      {
        auto entry = type_root.append_child("Default");
        entry.append_attribute("Extension").set_value("rels");
        entry.append_attribute("ContentType")
            .set_value("application/vnd.openxmlformats-package.relationships+xml");
      }
    zip.set_text("[Content_Types].xml", serialize_xml(types));
    pugi::xml_document rels;
    if(const auto existing = zip.text("_rels/.rels"))
      {
        if(not rels.load_string(std::string(*existing).c_str()))
          {
            error = "invalid _rels/.rels";
            return false;
          }
      }
    auto root = rels.child("Relationships");
    if(not root)
      {
        root = rels.append_child("Relationships");
      }
    if(not root.attribute("xmlns"))
      {
        root.append_attribute("xmlns");
      }
    root.attribute("xmlns").set_value(OPC_RELS_NS);
    bool document_relation = false;
    for(auto relation = root.child("Relationship"); relation;)
      {
        auto next = relation.next_sibling("Relationship");
        if(std::string_view(relation.attribute("Type").value()) == DOCLANG_REL_TYPE)
          {
            if(document_relation)
              {
                root.remove_child(relation);
              }
            else
              {
                if(not relation.attribute("Target"))
                  {
                    relation.append_attribute("Target");
                  }
                relation.attribute("Target").set_value("document.xml");
                document_relation = true;
              }
          }
        relation = next;
      }
    if(not document_relation)
      {
        auto relation = root.append_child("Relationship");
        relation.append_attribute("Id").set_value("rIdDoclangDocument");
        relation.append_attribute("Type").set_value(DOCLANG_REL_TYPE);
        relation.append_attribute("Target").set_value("document.xml");
      }
    zip.set_text("_rels/.rels", serialize_xml(rels));
    return true;
  }

  inline void remove_part_content_type(archive& zip, std::string_view path)
  {
    const auto existing = zip.text("[Content_Types].xml");
    if(not existing)
      {
        return;
      }
    pugi::xml_document types;
    if(not types.load_string(std::string(*existing).c_str()))
      {
        return;
      }
    const std::string part_name = "/" + std::string(path);
    auto root = types.child("Types");
    for(auto node = root.child("Override"); node;)
      {
        auto next = node.next_sibling("Override");
        if(std::string_view(node.attribute("PartName").value()) == part_name)
          {
            root.remove_child(node);
          }
        node = next;
      }
    zip.set_text("[Content_Types].xml", serialize_xml(types));
  }
}
#endif
