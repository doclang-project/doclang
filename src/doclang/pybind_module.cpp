#include <doclang/reader.h>
#include <doclang/writer.h>
#include <doclang/pybind_document.h>
#include <doclang/pybind_x_document.h>

#include <pybind11/pybind11.h>

PYBIND11_MODULE(_native, module)
{
  namespace py = pybind11;
  using doclang::binding::DoclangDocument;

  module.doc() = "DocLang native backend";
  module.def("_hash", &doclang::native::dclg_document::hash);

  py::class_<DoclangDocument::Iterator>(module, "_DoclangIterator")
    .def("__iter__", [](DoclangDocument::Iterator& iterator)
         -> DoclangDocument::Iterator& { return iterator; },
         py::return_value_policy::reference_internal)
    .def("__next__", &DoclangDocument::Iterator::next);

  py::class_<DoclangDocument>(module, "DoclangDocument")
    .def(py::init<>())
    .def(py::init<const std::string&>(), py::arg("dclg"))
    .def("read_xml", &DoclangDocument::read_xml, py::arg("dclg"))
    .def("valid", &DoclangDocument::valid)
    .def("xml", &DoclangDocument::xml)
    .def("last_error", &DoclangDocument::last_error)
    .def("at", &DoclangDocument::at, py::kw_only(),
         py::arg("xpath"), py::arg("mode") = "auto")
    .def("bounding_box", &DoclangDocument::bounding_box, py::arg("xpath"))
    .def("page_number", &DoclangDocument::page_number, py::arg("xpath"))
    .def("iterate_items", &DoclangDocument::iterate_items,
         py::arg("xpath") = py::none())
    .def("iterate_items_on_page", &DoclangDocument::iterate_items_on_page,
         py::arg("page_no"))
    .def("__iter__", &DoclangDocument::iter);

  using doclang::binding::DocLangXDocument;
  py::class_<DocLangXDocument, DoclangDocument>(module, "DocLangXDocument")
    .def(py::init<>())
    .def_static("hash", &DocLangXDocument::hash, py::arg("text"))
    .def("read", &DocLangXDocument::read, py::arg("path"))
    .def("read_xml", &DocLangXDocument::read_xml, py::arg("xml"))
    .def("write", &DocLangXDocument::write, py::arg("path"))
    .def("has_archive", &DocLangXDocument::has_archive)
    .def("has_annotations", &DocLangXDocument::has_annotations)
    .def("source_path", &DocLangXDocument::source_path)
    .def("archive_paths", &DocLangXDocument::archive_paths)
    .def("annotation_paths", &DocLangXDocument::annotation_paths)
    .def("document_reference", &DocLangXDocument::document_reference)
    .def("references", &DocLangXDocument::references)
    .def("summary", &DocLangXDocument::summary)
    .def("toc", &DocLangXDocument::toc)
    .def("concepts", &DocLangXDocument::concepts)
    .def("set_document_reference", &DocLangXDocument::set_document_reference,
         py::arg("bibtex"))
    .def("set_references", &DocLangXDocument::set_references,
         py::arg("bibtex"))
    .def("set_document_summary", &DocLangXDocument::set_document_summary,
         py::arg("dclg"))
    .def("set_toc", &DocLangXDocument::set_toc, py::arg("dclg"))
    .def("set_concepts", &DocLangXDocument::set_concepts, py::arg("dclg"))
    .def("clear_document_reference", &DocLangXDocument::clear_document_reference)
    .def("clear_references", &DocLangXDocument::clear_references)
    .def("clear_document_summary", &DocLangXDocument::clear_document_summary)
    .def("clear_toc", &DocLangXDocument::clear_toc)
    .def("clear_concepts", &DocLangXDocument::clear_concepts)
    .def("overview", &DocLangXDocument::overview)
    .def("properties", &DocLangXDocument::properties)
    .def("entities", &DocLangXDocument::entities)
    .def("instances", &DocLangXDocument::instances)
    .def("relations", &DocLangXDocument::relations)
    .def("query_properties", &DocLangXDocument::query_properties,
         py::arg("type")="", py::arg("label")="", py::arg("xpath")="",
         py::arg("min_conf")=0.0f)
    .def("query_entities", &DocLangXDocument::query_entities,
         py::arg("type")="", py::arg("subtype")="", py::arg("name")="",
         py::arg("name_contains")="", py::arg("min_count")=0)
    .def("query_instances", &DocLangXDocument::query_instances,
         py::arg("type")="", py::arg("subtype")="", py::arg("name")="",
         py::arg("name_contains")="", py::arg("xpath")="",
         py::arg("min_conf")=0.0f, py::arg("entity_hash")=0)
    .def("query_relations", &DocLangXDocument::query_relations,
         py::arg("name")="", py::arg("name_contains")="",
         py::arg("min_conf")=0.0f, py::arg("hash_i")=0, py::arg("hash_j")=0)
    .def("table_coordinates", &DocLangXDocument::table_coordinates,
         py::arg("xpath"));
}
