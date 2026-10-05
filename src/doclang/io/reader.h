//-*-C++-*-

#ifndef DOCLANG_NATIVE_READER_H_
#define DOCLANG_NATIVE_READER_H_

#include <cstddef>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <span>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

#include <doclang/dclx_document.h>
#include <doclang/annotations.h>

namespace doclang::native
{

  enum class format
  {
    dclg,
    dclx,
    unknown
  };

  class reader
  {
  public:

    static format detect_format(const std::filesystem::path& path);

    static bool read(const std::filesystem::path& path, dclx_document& out,
                     const archive::limits& bounds = archive::limits());

    static bool read_dclg_buffer(std::string_view xml, dclg_document& out);
    static bool read_dclx_buffer(std::span<const std::byte> bytes, dclx_document& out,
                                 const archive::limits& bounds = archive::limits());

  private:

    static bool read_file(const std::filesystem::path& path, std::vector<std::byte>& data,
                          std::string& error);
  };

  inline format reader::detect_format(const std::filesystem::path& path)
  {
    std::string ext = path.extension().string();

    for(char& c : ext)
      {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
      }

    if(ext == ".dclg")
      {
        return format::dclg;
      }

    if(ext == ".dclx")
      {
        return format::dclx;
      }

    return format::unknown;
  }

  inline bool reader::read(const std::filesystem::path& path, dclx_document& out,
                           const archive::limits& bounds)
  {
    out.clear();

    bool success = false;

    std::vector<std::byte> data;
    std::string error;
    if(std::filesystem::is_regular_file(path) and detect_format(path) == format::dclx
       and std::filesystem::file_size(path) > bounds.max_archive_bytes)
      {
        out.set_last_error("dclx archive exceeds size limit");
      }
    else if(not read_file(path, data, error))
      {
        out.set_last_error(error);
      }
    else
      {
        switch(detect_format(path))
          {
          case format::dclg:
            {
              const char* ptr = reinterpret_cast<const char*>(data.data());
              success = read_dclg_buffer(std::string_view(ptr, data.size()), out);
              break;
            }

          case format::dclx:
            {
              success = read_dclx_buffer(std::span<const std::byte>(data.data(), data.size()), out,
                                         bounds);
              break;
            }

          case format::unknown:
          default:
            {
              out.set_last_error("unsupported DocLang file extension: "
                                 + path.extension().string());
              break;
            }
          }
      }

    // set last: read_dclx_buffer clears the whole document, source path included
    out.set_source_path(path);
    return success;
  }

  inline bool reader::read_dclg_buffer(std::string_view xml, dclg_document& out)
  {
    return out.read(xml);
  }

  inline bool reader::read_dclx_buffer(std::span<const std::byte> bytes, dclx_document& out,
                                       const archive::limits& bounds)
  {
    out.clear();

    archive zip;
    if(not zip.load_from_memory(bytes, bounds))
      {
        out.set_last_error(zip.get_last_error());
        return false;
      }

    auto xml = zip.text("document.xml");
    if(not xml.has_value())
      {
        out.set_last_error("dclx archive does not contain document.xml");
        return false;
      }

    if(not out.read(xml.value()))
      {
        return false;
      }

    out.set_archive(std::move(zip));
    return load_annotations(out);
  }

  inline bool reader::read_file(const std::filesystem::path& path, std::vector<std::byte>& data,
                                std::string& error)
  {
    std::ifstream ifs(path, std::ios::binary);
    if(not ifs)
      {
        error = "could not open file: " + path.string();
        return false;
      }

    ifs.seekg(0, std::ios::end);
    std::streamoff size = ifs.tellg();
    if(size < 0)
      {
        error = "could not determine file size: " + path.string();
        return false;
      }

    ifs.seekg(0, std::ios::beg);
    data.resize(static_cast<std::size_t>(size));

    if(size > 0)
      {
        ifs.read(reinterpret_cast<char*>(data.data()), size);
        if(not ifs)
          {
            error = "could not read file: " + path.string();
            return false;
          }
      }

    return true;
  }

}

#endif
