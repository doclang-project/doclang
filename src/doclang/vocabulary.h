#ifndef DOCLANG_NATIVE_VOCABULARY_H_
#define DOCLANG_NATIVE_VOCABULARY_H_

#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace doclang::native
{
  // Every element declared by doclang.xsd.
  enum class element_tag
  {
    audio,
    bdiv,
    bold,
    caption,
    chapter,
    checkbox,
    ched,
    code,
    content,
    corn,
    cover,
    custom,
    default_resolution,
    description,
    doclang,
    ecel,
    fcel,
    field_heading,
    field_item,
    field_region,
    footnote,
    formula,
    frame,
    group,
    handwriting,
    head,
    heading,
    hint,
    href,
    hours,
    index,
    italic,
    key,
    label,
    layer,
    lcel,
    ldiv,
    list,
    location,
    marker,
    meta,
    minutes,
    msecs,
    nl,
    page_break,
    page_footer,
    page_header,
    picture,
    rhed,
    rtl,
    seconds,
    src,
    srow,
    strikethrough,
    subscript,
    summary,
    superscript,
    table,
    tabular,
    text,
    thread,
    track,
    ucel,
    underline,
    value,
    voice,
    xcel,
    xref
  };

  // The schema's attribute names, plus the root namespace declaration.
  enum class attribute_name
  {
    class_,
    height,
    level,
    resolution,
    thread_id,
    uri,
    value,
    version,
    width,
    xmlns
  };

  // Short OTSL names map to the XML element names used by the schema.
  enum class otsl_token
  {
    fc,
    ec,
    ch,
    rh,
    co,
    sr,
    lc,
    uc,
    xc,
    nl
  };

  inline constexpr std::pair<element_tag, std::string_view> element_tag_names[]
      = { { element_tag::audio, "audio" },
          { element_tag::bdiv, "bdiv" },
          { element_tag::bold, "bold" },
          { element_tag::caption, "caption" },
          { element_tag::chapter, "chapter" },
          { element_tag::checkbox, "checkbox" },
          { element_tag::ched, "ched" },
          { element_tag::code, "code" },
          { element_tag::content, "content" },
          { element_tag::corn, "corn" },
          { element_tag::cover, "cover" },
          { element_tag::custom, "custom" },
          { element_tag::default_resolution, "default_resolution" },
          { element_tag::description, "description" },
          { element_tag::doclang, "doclang" },
          { element_tag::ecel, "ecel" },
          { element_tag::fcel, "fcel" },
          { element_tag::field_heading, "field_heading" },
          { element_tag::field_item, "field_item" },
          { element_tag::field_region, "field_region" },
          { element_tag::footnote, "footnote" },
          { element_tag::formula, "formula" },
          { element_tag::frame, "frame" },
          { element_tag::group, "group" },
          { element_tag::handwriting, "handwriting" },
          { element_tag::head, "head" },
          { element_tag::heading, "heading" },
          { element_tag::hint, "hint" },
          { element_tag::href, "href" },
          { element_tag::hours, "hours" },
          { element_tag::index, "index" },
          { element_tag::italic, "italic" },
          { element_tag::key, "key" },
          { element_tag::label, "label" },
          { element_tag::layer, "layer" },
          { element_tag::lcel, "lcel" },
          { element_tag::ldiv, "ldiv" },
          { element_tag::list, "list" },
          { element_tag::location, "location" },
          { element_tag::marker, "marker" },
          { element_tag::meta, "meta" },
          { element_tag::minutes, "minutes" },
          { element_tag::msecs, "msecs" },
          { element_tag::nl, "nl" },
          { element_tag::page_break, "page_break" },
          { element_tag::page_footer, "page_footer" },
          { element_tag::page_header, "page_header" },
          { element_tag::picture, "picture" },
          { element_tag::rhed, "rhed" },
          { element_tag::rtl, "rtl" },
          { element_tag::seconds, "seconds" },
          { element_tag::src, "src" },
          { element_tag::srow, "srow" },
          { element_tag::strikethrough, "strikethrough" },
          { element_tag::subscript, "subscript" },
          { element_tag::summary, "summary" },
          { element_tag::superscript, "superscript" },
          { element_tag::table, "table" },
          { element_tag::tabular, "tabular" },
          { element_tag::text, "text" },
          { element_tag::thread, "thread" },
          { element_tag::track, "track" },
          { element_tag::ucel, "ucel" },
          { element_tag::underline, "underline" },
          { element_tag::value, "value" },
          { element_tag::voice, "voice" },
          { element_tag::xcel, "xcel" },
          { element_tag::xref, "xref" } };

  inline constexpr std::pair<attribute_name, std::string_view> attribute_names[]
      = { { attribute_name::class_, "class" },        { attribute_name::height, "height" },
          { attribute_name::level, "level" },         { attribute_name::resolution, "resolution" },
          { attribute_name::thread_id, "thread_id" }, { attribute_name::uri, "uri" },
          { attribute_name::value, "value" },         { attribute_name::version, "version" },
          { attribute_name::width, "width" },         { attribute_name::xmlns, "xmlns" } };

  inline constexpr std::pair<otsl_token, std::string_view> otsl_short_names[]
      = { { otsl_token::fc, "fc" }, { otsl_token::ec, "ec" }, { otsl_token::ch, "ch" },
          { otsl_token::rh, "rh" }, { otsl_token::co, "co" }, { otsl_token::sr, "sr" },
          { otsl_token::lc, "lc" }, { otsl_token::uc, "uc" }, { otsl_token::xc, "xc" },
          { otsl_token::nl, "nl" } };

  inline constexpr std::string_view to_string_view(element_tag value)
  {
    for(const auto& [tag, name] : element_tag_names)
      {
        if(tag == value)
          {
            return name;
          }
      }
    throw std::invalid_argument("unknown DocLang element tag");
  }

  inline constexpr std::string_view to_string_view(attribute_name value)
  {
    for(const auto& [attribute, name] : attribute_names)
      {
        if(attribute == value)
          {
            return name;
          }
      }
    throw std::invalid_argument("unknown DocLang attribute name");
  }

  inline constexpr element_tag to_element_tag(otsl_token value)
  {
    switch(value)
      {
      case otsl_token::fc:
        return element_tag::fcel;
      case otsl_token::ec:
        return element_tag::ecel;
      case otsl_token::ch:
        return element_tag::ched;
      case otsl_token::rh:
        return element_tag::rhed;
      case otsl_token::co:
        return element_tag::corn;
      case otsl_token::sr:
        return element_tag::srow;
      case otsl_token::lc:
        return element_tag::lcel;
      case otsl_token::uc:
        return element_tag::ucel;
      case otsl_token::xc:
        return element_tag::xcel;
      case otsl_token::nl:
        return element_tag::nl;
      }
    throw std::invalid_argument("unknown DocLang OTSL token");
  }

  inline constexpr std::string_view to_string_view(otsl_token value)
  {
    return to_string_view(to_element_tag(value));
  }

  inline std::string to_string(element_tag value)
  {
    return std::string(to_string_view(value));
  }

  inline std::string to_string(attribute_name value)
  {
    return std::string(to_string_view(value));
  }

  inline std::string to_string(otsl_token value)
  {
    return std::string(to_string_view(value));
  }

  inline constexpr const char* xml_name(element_tag value)
  {
    return to_string_view(value).data();
  }

  inline constexpr const char* xml_name(attribute_name value)
  {
    return to_string_view(value).data();
  }

  inline constexpr const char* xml_name(otsl_token value)
  {
    return to_string_view(value).data();
  }

  inline constexpr std::optional<element_tag> element_tag_from_string(std::string_view value)
  {
    for(const auto& [tag, name] : element_tag_names)
      {
        if(name == value)
          {
            return tag;
          }
      }
    return std::nullopt;
  }

  inline constexpr std::optional<attribute_name> attribute_name_from_string(std::string_view value)
  {
    for(const auto& [attribute, name] : attribute_names)
      {
        if(name == value)
          {
            return attribute;
          }
      }
    return std::nullopt;
  }

  inline constexpr std::optional<otsl_token> otsl_token_from_string(std::string_view value)
  {
    for(const auto& [token, name] : otsl_short_names)
      {
        if(name == value or to_string_view(token) == value)
          {
            return token;
          }
      }
    return std::nullopt;
  }
}

#endif
