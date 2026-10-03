#include <doclang/io/reader.h>
#include <doclang/io/writer.h>
#include <pybind/doclang_document.h>
#include <pybind/doclang_x_document.h>
#include <doclang/validation/rules.h>
#include <doclang/dclg_node/dclg_text.h>
#include <doclang/dclg_node/dclg_formula.h>
#include <doclang/dclg_node/dclg_heading.h>
#include <doclang/dclg_node/dclg_footnote.h>
#include <doclang/dclg_node/dclg_field_region.h>
#include <doclang/dclg_node/dclg_field_item.h>
#include <doclang/dclg_node/dclg_picture.h>
#include <doclang/dclg_node/dclg_list.h>
#include <doclang/dclg_node/dclg_table.h>

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>

namespace
{
  template <typename Element>
  void bind_element_validation(
      pybind11::class_<Element, doclang::native::dclg_node, std::shared_ptr<Element>>& binding)
  {
    using doclang::binding::DoclangDocument;
    using doclang::native::insertion_site;
    namespace py = pybind11;
    binding.def("validate_local", &Element::validate_local)
        .def("is_valid", &Element::is_valid)
        .def(
            "validate_in",
            [](const Element& node, const DoclangDocument& doc, const insertion_site& site) {
              return node.validate_in(doc.native_document(), site);
            },
            py::arg("document"), py::arg("site"))
        .def(
            "is_valid_in",
            [](const Element& node, const DoclangDocument& doc, const insertion_site& site) {
              return node.is_valid_in(doc.native_document(), site);
            },
            py::arg("document"), py::arg("site"));
  }

  pybind11::list issues_to_python(const std::vector<doclang::native::validation_issue>& issues)
  {
    pybind11::list result;
    for(const auto& issue : issues)
      {
        pybind11::dict row;
        row["assertion"] = issue.assertion;
        row["location"] = issue.location;
        row["message"] = issue.message;
        result.append(std::move(row));
      }
    return result;
  }

  pybind11::list xsd_issues_to_python(const std::vector<doclang::native::xsd_issue>& issues)
  {
    pybind11::list result;
    for(const auto& issue : issues)
      {
        pybind11::dict row;
        row["line"] = issue.line;
        row["message"] = issue.message;
        result.append(std::move(row));
      }
    return result;
  }
}

PYBIND11_MODULE(_native, module)
{
  namespace py = pybind11;
  using doclang::binding::DoclangDocument;

  module.doc() = "DocLang native backend";
  module.def("_hash", &doclang::native::dclg_document::hash);

  using doclang::native::doclang_version;
  py::class_<doclang_version>(module, "DoclangVersion")
      .def(py::init([](std::uint32_t major, std::uint32_t minor) {
             return doclang_version{ major, minor };
           }),
           py::arg("major"), py::arg("minor"))
      .def_static("parse", &doclang_version::parse, py::arg("value"))
      .def_readonly("major", &doclang_version::major)
      .def_readonly("minor", &doclang_version::minor)
      .def("__str__", &doclang_version::to_string)
      .def("__repr__",
           [](const doclang_version& value) {
             return "DoclangVersion('" + value.to_string() + "')";
           })
      .def(py::self == py::self)
      .def(py::self != py::self)
      .def(py::self < py::self)
      .def(py::self <= py::self)
      .def(py::self > py::self)
      .def(py::self >= py::self);

  namespace native = doclang::native;
  auto element_tags = py::enum_<native::element_tag>(module, "ElementTag");
  for(const auto& [tag, name] : native::element_tag_names)
    {
      element_tags.value(name.data(), tag);
    }
  auto attribute_names = py::enum_<native::attribute_name>(module, "AttributeName");
  for(const auto& [attribute, name] : native::attribute_names)
    {
      attribute_names.value(name == "class" ? "class_" : name.data(), attribute);
    }
  auto otsl_tokens = py::enum_<native::otsl_token>(module, "OtslToken");
  for(const auto& [token, name] : native::otsl_short_names)
    {
      otsl_tokens.value(name.data(), token);
    }
  module.def("xml_name", [](native::element_tag value) { return native::to_string(value); });
  module.def("xml_name", [](native::attribute_name value) { return native::to_string(value); });
  module.def("xml_name", [](native::otsl_token value) { return native::to_string(value); });
  module.def("element_tag_from_string", &native::element_tag_from_string);
  module.def("attribute_name_from_string", &native::attribute_name_from_string);
  module.def("otsl_token_from_string", &native::otsl_token_from_string);
  module.def(
      "_schematron_errors_xml",
      [](const std::string& xml, bool allow_empty_namespace) {
        return issues_to_python(
            doclang::native::validate_schematron_xml(xml, allow_empty_namespace));
      },
      py::arg("xml"), py::arg("allow_empty_namespace") = false);

  py::class_<doclang::native::validation_report>(module, "ValidationReport")
      .def_property_readonly(
          "scope", [](const doclang::native::validation_report& report) { return report.scope; })
      .def_property_readonly("xsd_errors",
                             [](const doclang::native::validation_report& report) {
                               return xsd_issues_to_python(report.xsd_errors);
                             })
      .def_property_readonly("schematron_errors",
                             [](const doclang::native::validation_report& report) {
                               return issues_to_python(report.schematron_errors);
                             })
      .def("ok", &doclang::native::validation_report::ok)
      .def("first_error", &doclang::native::validation_report::first_error);

  using doclang::native::insertion_site;
  py::class_<insertion_site>(module, "InsertionSite")
      .def_static("append_child", &insertion_site::append_child, py::arg("parent_xpath"))
      .def_static("prepend_child", &insertion_site::prepend_child, py::arg("parent_xpath"))
      .def_static("before", &insertion_site::before, py::arg("sibling_xpath"))
      .def_static("after", &insertion_site::after, py::arg("sibling_xpath"));

  using doclang::native::dclg_node;
  py::class_<dclg_node, std::shared_ptr<dclg_node>>(module, "DoclangNode")
      .def_static("element", py::overload_cast<std::string_view>(&dclg_node::element),
                  py::arg("name"))
      .def_static("element", py::overload_cast<native::element_tag>(&dclg_node::element),
                  py::arg("tag"))
      .def_static("from_xml", &dclg_node::from_xml, py::arg("fragment"))
      .def("name", &dclg_node::name)
      .def("to_xml", &dclg_node::to_xml)
      .def("set_attribute",
           py::overload_cast<std::string_view, std::string_view>(&dclg_node::set_attribute),
           py::arg("name"), py::arg("value"))
      .def("set_attribute",
           py::overload_cast<native::attribute_name, std::string_view>(&dclg_node::set_attribute),
           py::arg("name"), py::arg("value"))
      .def("remove_attribute", py::overload_cast<std::string_view>(&dclg_node::remove_attribute),
           py::arg("name"))
      .def("remove_attribute",
           py::overload_cast<native::attribute_name>(&dclg_node::remove_attribute), py::arg("name"))
      .def("append_text", &dclg_node::append_text, py::arg("text"))
      .def("append_child", &dclg_node::append_child, py::arg("child"))
      .def("prepend_child", &dclg_node::prepend_child, py::arg("child"))
      .def("insert_before", &dclg_node::insert_before, py::arg("child_xpath"), py::arg("sibling"))
      .def("insert_after", &dclg_node::insert_after, py::arg("child_xpath"), py::arg("sibling"));

  auto text_binding
      = py::class_<doclang::native::dclg_text, dclg_node,
                   std::shared_ptr<doclang::native::dclg_text>>(module, "DoclangTextNode");
  text_binding.def(py::init<const std::string&>(), py::arg("text") = "");
  bind_element_validation(text_binding);
  auto formula_binding
      = py::class_<doclang::native::dclg_formula, dclg_node,
                   std::shared_ptr<doclang::native::dclg_formula>>(module, "DoclangFormulaNode");
  formula_binding.def(py::init<const std::string&>(), py::arg("text") = "");
  bind_element_validation(formula_binding);
  auto heading_binding
      = py::class_<doclang::native::dclg_heading, dclg_node,
                   std::shared_ptr<doclang::native::dclg_heading>>(module, "DoclangHeadingNode");
  heading_binding.def(py::init<const std::string&, std::size_t>(), py::arg("text") = "",
                      py::arg("level") = 1);
  bind_element_validation(heading_binding);
  auto footnote_binding
      = py::class_<doclang::native::dclg_footnote, dclg_node,
                   std::shared_ptr<doclang::native::dclg_footnote>>(module, "DoclangFootnoteNode");
  footnote_binding.def(py::init<const std::string&>(), py::arg("text") = "");
  bind_element_validation(footnote_binding);
  auto field_region_binding = py::class_<doclang::native::dclg_field_region, dclg_node,
                                         std::shared_ptr<doclang::native::dclg_field_region>>(
      module, "DoclangFieldRegionNode");
  field_region_binding.def(py::init<>());
  bind_element_validation(field_region_binding);
  auto field_item_binding = py::class_<doclang::native::dclg_field_item, dclg_node,
                                       std::shared_ptr<doclang::native::dclg_field_item>>(
      module, "DoclangFieldItemNode");
  field_item_binding.def(py::init<>());
  bind_element_validation(field_item_binding);
  auto picture_binding
      = py::class_<doclang::native::dclg_picture, dclg_node,
                   std::shared_ptr<doclang::native::dclg_picture>>(module, "DoclangPictureNode");
  picture_binding.def(py::init<const std::string&>(), py::arg("src") = "")
      .def("set_src", &doclang::native::dclg_picture::set_src, py::arg("uri"))
      .def("set_caption", &doclang::native::dclg_picture::set_caption, py::arg("text"))
      .def("set_tabular", &doclang::native::dclg_picture::set_tabular, py::arg("table"));
  bind_element_validation(picture_binding);
  auto list_binding
      = py::class_<doclang::native::dclg_list, dclg_node,
                   std::shared_ptr<doclang::native::dclg_list>>(module, "DoclangListNode");
  list_binding.def(py::init<const std::string&>(), py::arg("kind") = "unordered")
      .def("item_count", &doclang::native::dclg_list::item_count)
      .def("append_item", &doclang::native::dclg_list::append_item, py::arg("content"))
      .def("insert_item", &doclang::native::dclg_list::insert_item, py::arg("index"),
           py::arg("content"))
      .def("append_item_text", &doclang::native::dclg_list::append_item_text, py::arg("text"))
      .def("insert_item_text", &doclang::native::dclg_list::insert_item_text, py::arg("index"),
           py::arg("text"))
      .def("append_to_item", &doclang::native::dclg_list::append_to_item, py::arg("index"),
           py::arg("content"))
      .def("delete_item", &doclang::native::dclg_list::delete_item, py::arg("index"));
  bind_element_validation(list_binding);
  auto table_binding
      = py::class_<doclang::native::dclg_table, dclg_node,
                   std::shared_ptr<doclang::native::dclg_table>>(module, "DoclangTableNode");
  table_binding.def(py::init<std::size_t, std::size_t>(), py::arg("rows"), py::arg("columns"))
      .def("set_caption", &doclang::native::dclg_table::set_caption, py::arg("text"))
      .def("row_count", &doclang::native::dclg_table::row_count)
      .def("column_count", &doclang::native::dclg_table::column_count)
      .def("insert_row", &doclang::native::dclg_table::insert_row, py::arg("index"))
      .def("delete_row", &doclang::native::dclg_table::delete_row, py::arg("index"))
      .def("insert_column", &doclang::native::dclg_table::insert_column, py::arg("index"))
      .def("delete_column", &doclang::native::dclg_table::delete_column, py::arg("index"))
      .def("append_to_cell", &doclang::native::dclg_table::append_to_cell, py::arg("row"),
           py::arg("column"), py::arg("content"))
      .def("set_cell", &doclang::native::dclg_table::set_cell, py::arg("row"), py::arg("column"),
           py::arg("content"))
      .def("clear_cell", &doclang::native::dclg_table::clear_cell, py::arg("row"),
           py::arg("column"));
  bind_element_validation(table_binding);

  py::class_<DoclangDocument::Iterator>(module, "_DoclangIterator")
      .def(
          "__iter__",
          [](DoclangDocument::Iterator& iterator) -> DoclangDocument::Iterator& {
            return iterator;
          },
          py::return_value_policy::reference_internal)
      .def("__next__", &DoclangDocument::Iterator::next);

  py::class_<DoclangDocument>(module, "DoclangDocument")
      .def(py::init<>())
      .def(py::init<const std::string&>(), py::arg("dclg"))
      .def_static("empty", &DoclangDocument::empty)
      .def("read_xml", &DoclangDocument::read_xml, py::arg("dclg"))
      .def("append_child", &DoclangDocument::append_child, py::arg("parent_xpath"), py::arg("node"))
      .def("prepend_child", &DoclangDocument::prepend_child, py::arg("parent_xpath"),
           py::arg("node"))
      .def("insert_before", &DoclangDocument::insert_before, py::arg("sibling_xpath"),
           py::arg("node"))
      .def("insert_after", &DoclangDocument::insert_after, py::arg("sibling_xpath"),
           py::arg("node"))
      .def("delete", &DoclangDocument::delete_at, py::arg("xpath"))
      .def("validate", &DoclangDocument::validate, py::arg("allow_empty_namespace") = false,
           py::arg("xsd_only") = false, py::arg("schematron_only") = false)
      .def("is_valid", &DoclangDocument::is_valid, py::arg("allow_empty_namespace") = false,
           py::arg("xsd_only") = false, py::arg("schematron_only") = false)
      .def("valid", &DoclangDocument::valid)
      .def("version", &DoclangDocument::version)
      .def("xml", &DoclangDocument::xml)
      .def("last_error", &DoclangDocument::last_error)
      .def("at", &DoclangDocument::at, py::kw_only(), py::arg("xpath"), py::arg("mode") = "auto")
      .def("bounding_box", &DoclangDocument::bounding_box, py::arg("xpath"))
      .def("page_number", &DoclangDocument::page_number, py::arg("xpath"))
      .def("iterate_items", &DoclangDocument::iterate_items, py::arg("xpath") = py::none())
      .def("iterate_items_on_page", &DoclangDocument::iterate_items_on_page, py::arg("page_no"))
      .def("__iter__", &DoclangDocument::iter)
      .def(
          "schematron_errors",
          [](const DoclangDocument& doc, bool allow_empty_namespace) {
            if(not doc.valid())
              {
                throw py::value_error("cannot validate an invalid DocLang document");
              }
            return issues_to_python(
                doclang::native::validate_schematron_xml(doc.xml(), allow_empty_namespace));
          },
          py::arg("allow_empty_namespace") = false);

  using doclang::binding::DocLangXDocument;
  py::class_<DocLangXDocument, DoclangDocument>(module, "DocLangXDocument")
      .def(py::init<>())
      .def_static("hash", &DocLangXDocument::hash, py::arg("text"))
      .def("read", &DocLangXDocument::read, py::arg("path"))
      .def("read_xml", &DocLangXDocument::read_xml, py::arg("xml"))
      .def("write", &DocLangXDocument::write, py::arg("path"),
           py::arg("allow_stale_annotations") = false)
      .def("annotations_stale", &DocLangXDocument::annotations_stale)
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
      .def("set_document_reference", &DocLangXDocument::set_document_reference, py::arg("bibtex"))
      .def("set_references", &DocLangXDocument::set_references, py::arg("bibtex"))
      .def("set_document_summary", &DocLangXDocument::set_document_summary, py::arg("dclg"))
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
      .def("query_properties", &DocLangXDocument::query_properties, py::arg("type") = "",
           py::arg("label") = "", py::arg("xpath") = "", py::arg("min_conf") = 0.0f)
      .def("query_entities", &DocLangXDocument::query_entities, py::arg("type") = "",
           py::arg("subtype") = "", py::arg("name") = "", py::arg("name_contains") = "",
           py::arg("min_count") = 0)
      .def("query_instances", &DocLangXDocument::query_instances, py::arg("type") = "",
           py::arg("subtype") = "", py::arg("name") = "", py::arg("name_contains") = "",
           py::arg("xpath") = "", py::arg("min_conf") = 0.0f, py::arg("entity_hash") = 0)
      .def("query_relations", &DocLangXDocument::query_relations, py::arg("name") = "",
           py::arg("name_contains") = "", py::arg("min_conf") = 0.0f, py::arg("hash_i") = 0,
           py::arg("hash_j") = 0)
      .def("table_coordinates", &DocLangXDocument::table_coordinates, py::arg("xpath"));
}
