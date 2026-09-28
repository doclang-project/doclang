//-*-C++-*-

#ifndef DOCLANG_NATIVE_WRITER_H_
#define DOCLANG_NATIVE_WRITER_H_

#include <filesystem>
#include <fstream>
#include <span>
#include <string>
#include <vector>

#include <doclang/annotations.h>
#include <doclang/content.h>
#include <doclang/dclx_document.h>

namespace doclang::native
{

  struct writer_options
  {
    bool include_annotations = true;
  };

  class writer
  {
  public:

    static bool write_dclx(const std::filesystem::path& path,
                           dclx_document& doc,
                           const writer_options& options = writer_options());

    static bool write_dclx_buffer(dclx_document& doc,
                                  std::vector<std::byte>& out,
                                  const writer_options& options = writer_options());
  };

  inline bool writer::write_dclx(const std::filesystem::path& path,
                          dclx_document& doc,
                          const writer_options& options)
  {
    std::vector<std::byte> data;
    if(not write_dclx_buffer(doc, data, options))
      {
        return false;
      }

    std::ofstream ofs(path, std::ios::binary);
    if(not ofs)
      {
        doc.set_last_error("could not open file for writing: " + path.string());
        return false;
      }

    ofs.write(reinterpret_cast<const char*>(data.data()),
              static_cast<std::streamsize>(data.size()));
    if(not ofs)
      {
        doc.set_last_error("could not write file: " + path.string());
        return false;
      }

    return true;
  }

  inline bool writer::write_dclx_buffer(dclx_document& doc,
                                 std::vector<std::byte>& out,
                                 const writer_options& options)
  {
    archive zip;
    if(doc.has_archive())
      {
        zip = doc.artifacts();
      }
    else
      {
        zip.set_text("[Content_Types].xml", "<Types></Types>");
        zip.set_text("_rels/.rels", "<Relationships></Relationships>");
      }

    zip.set_text("document.xml", serialize_xml(doc.xml()));
    zip.erase("annotations/edges.csv");

    if(options.include_annotations)
      {
        if(doc.mutable_entities().empty() and not doc.mutable_instances().empty())
          {
            doc.compute_entities();
          }

        zip.set_text(PROPERTIES_CSV, to_properties_csv(doc.mutable_properties()));
        zip.set_text(INSTANCES_CSV, to_instances_csv(doc.mutable_instances()));
        zip.set_text(ENTITIES_CSV, to_entities_csv(doc.mutable_entities()));
        zip.set_text(RELATIONS_CSV, to_relations_csv(doc.mutable_relations()));

        if(doc.has_document_reference())
          {
            zip.set_text(DOCUMENT_REFERENCE_BIB, doc.get_document_reference().value());
          }
        else
          {
            zip.erase(DOCUMENT_REFERENCE_BIB);
          }
        if(doc.has_references())
          {
            zip.set_text(REFERENCES_BIB, doc.get_references().value());
          }
        else
          {
            zip.erase(REFERENCES_BIB);
          }
        if(doc.has_summary())
          {
            zip.set_text(SUMMARY_DCLG, doc.get_summary().value()->raw());
          }
        else
          {
            zip.erase(SUMMARY_DCLG);
          }
        if(doc.has_toc())
          {
            zip.set_text(TOC_DCLG, doc.get_toc().value()->raw());
          }
        else
          {
            zip.erase(TOC_DCLG);
          }
        if(doc.has_concepts())
          {
            zip.set_text(CONCEPTS_DCLG, doc.get_concepts().value()->raw());
          }
        else
          {
            zip.erase(CONCEPTS_DCLG);
          }
      }
    else
      {
        zip.erase(PROPERTIES_CSV);
        zip.erase(INSTANCES_CSV);
        zip.erase(ENTITIES_CSV);
        zip.erase(RELATIONS_CSV);
        zip.erase(DOCUMENT_REFERENCE_BIB);
        zip.erase(REFERENCES_BIB);
        zip.erase(SUMMARY_DCLG);
        zip.erase(TOC_DCLG);
        zip.erase(CONCEPTS_DCLG);
      }

    if(not zip.write_to_memory(out))
      {
        doc.set_last_error("could not write DocLang archive");
        return false;
      }

    return true;
  }

}

#endif
