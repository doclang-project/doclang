//-*-C++-*-

#ifndef DOCLANG_NATIVE_ARCHIVE_H_
#define DOCLANG_NATIVE_ARCHIVE_H_

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <algorithm>
#include <stdexcept>
#include <filesystem>
#include <fstream>
#include <map>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

#include <miniz.h>

namespace doclang::native
{

  class archive
  {
  public:

    typedef std::vector<std::byte> bytes_type;
    struct limits
    {
      std::size_t max_archive_bytes = 256ULL * 1024 * 1024;
      std::size_t max_entries = 10000;
      std::size_t max_entry_bytes = 256ULL * 1024 * 1024;
      std::size_t max_total_bytes = 1024ULL * 1024 * 1024;
      std::size_t max_compression_ratio = 200;
    };

  public:

    archive() = default;

    void clear();

    bool load_from_memory(std::span<const std::byte> data);
    bool load_from_memory(std::span<const std::byte> data, const limits& bounds);
    bool write_to_memory(bytes_type& data) const;
    bool write_to_file(const std::filesystem::path& path) const;

    bool has(std::string_view path) const;

    std::optional<std::string_view> text(std::string_view path) const;
    std::optional<std::span<const std::byte>> bytes(std::string_view path) const;

    void set_text(std::string_view path, std::string_view text);
    void set_bytes(std::string_view path, std::span<const std::byte> data);
    void erase(std::string_view path);

    std::vector<std::string> paths() const;
    static bool valid_path(std::string_view path);

    const std::string& get_last_error() const
    {
      return last_error;
    }

  private:

    void set_error(std::string msg);
    std::optional<bytes_type> extract(std::string_view path) const;

  private:

    mutable std::map<std::string, bytes_type> entries;
    std::map<std::string, mz_uint> source_entries;
    bytes_type source_data;
    limits active_limits;
    std::string last_error;
  };

  inline void archive::clear()
  {
    entries.clear();
    source_entries.clear();
    source_data.clear();
    last_error.clear();
  }

  inline void archive::set_error(std::string msg)
  {
    last_error = std::move(msg);
  }

  inline bool archive::valid_path(std::string_view path)
  {
    if(path.empty() or path.front() == '/' or path.back() == '/' or path.find('\\') != path.npos
       or path.find(':') != path.npos or path.find('\0') != path.npos)
      {
        return false;
      }
    while(not path.empty())
      {
        const auto slash = path.find('/');
        const auto part = path.substr(0, slash);
        if(part.empty() or part == "." or part == "..")
          {
            return false;
          }
        if(slash == path.npos)
          {
            break;
          }
        path.remove_prefix(slash + 1);
      }
    return true;
  }

  inline bool archive::load_from_memory(std::span<const std::byte> data)
  {
    return load_from_memory(data, limits{});
  }

  inline bool archive::load_from_memory(std::span<const std::byte> data, const limits& bounds)
  {
    clear();
    active_limits = bounds;
    if(data.size() > bounds.max_archive_bytes)
      {
        set_error("dclx archive exceeds size limit");
        return false;
      }
    source_data.assign(data.begin(), data.end());

    mz_zip_archive zip;
    std::memset(&zip, 0, sizeof(zip));

    const void* ptr = static_cast<const void*>(source_data.data());
    if(!mz_zip_reader_init_mem(&zip, ptr, source_data.size(), 0))
      {
        set_error("could not initialise zip reader from memory");
        return false;
      }

    bool success = true;
    const mz_uint num_files = mz_zip_reader_get_num_files(&zip);
    std::size_t total_bytes = 0;
    if(num_files > bounds.max_entries)
      {
        mz_zip_reader_end(&zip);
        clear();
        set_error("dclx archive exceeds entry count limit");
        return false;
      }

    for(mz_uint i = 0; i < num_files; i++)
      {
        mz_zip_archive_file_stat stat;
        std::memset(&stat, 0, sizeof(stat));

        if(!mz_zip_reader_file_stat(&zip, i, &stat))
          {
            set_error("could not read zip file metadata");
            success = false;
            break;
          }

        if(std::strlen(stat.m_filename) >= sizeof(stat.m_filename) - 1)
          {
            set_error("dclx part path exceeds supported length");
            success = false;
            break;
          }

        if(mz_zip_reader_is_file_a_directory(&zip, i))
          {
            const std::string directory(stat.m_filename);
            if(directory.empty() or not valid_path(directory.substr(0, directory.size() - 1)))
              {
                set_error("invalid dclx directory path: " + directory);
                success = false;
                break;
              }
            continue;
          }

        const std::string path(stat.m_filename);
        if(not valid_path(path) or source_entries.count(path) != 0)
          {
            set_error("invalid or duplicate dclx part path: " + path);
            success = false;
            break;
          }
        const std::size_t expanded = static_cast<std::size_t>(stat.m_uncomp_size);
        const std::size_t compressed = static_cast<std::size_t>(stat.m_comp_size);
        if(expanded > bounds.max_entry_bytes or expanded > bounds.max_total_bytes - total_bytes
           or (expanded > 0
               and (compressed == 0 or expanded / compressed > bounds.max_compression_ratio)))
          {
            set_error("dclx part exceeds size or compression limit: " + path);
            success = false;
            break;
          }
        total_bytes += expanded;
        source_entries.emplace(path, i);
      }

    mz_zip_reader_end(&zip);

    if(success and not has("document.xml"))
      {
        set_error("dclx archive does not contain document.xml");
        return false;
      }

    if(not success)
      {
        const auto error = last_error;
        clear();
        set_error(error);
      }
    return success;
  }

  inline std::optional<archive::bytes_type> archive::extract(std::string_view path) const
  {
    const auto itr = source_entries.find(std::string(path));
    if(itr == source_entries.end())
      {
        return std::nullopt;
      }
    mz_zip_archive zip{};
    if(not mz_zip_reader_init_mem(&zip, source_data.data(), source_data.size(), 0))
      {
        return std::nullopt;
      }
    size_t size = 0;
    void* raw = mz_zip_reader_extract_to_heap(&zip, itr->second, &size, 0);
    if(raw == nullptr or size > active_limits.max_entry_bytes)
      {
        if(raw)
          {
            mz_free(raw);
          }
        mz_zip_reader_end(&zip);
        return std::nullopt;
      }
    bytes_type value(size);
    if(size > 0)
      {
        std::memcpy(value.data(), raw, size);
      }
    mz_free(raw);
    mz_zip_reader_end(&zip);
    return value;
  }

  inline bool archive::write_to_memory(bytes_type& data) const
  {
    data.clear();

    mz_zip_archive zip;
    std::memset(&zip, 0, sizeof(zip));

    if(!mz_zip_writer_init_heap(&zip, 0, 0))
      {
        return false;
      }

    bool success = true;
    for(const auto& path : paths())
      {
        const auto part = bytes(path);
        if(not part)
          {
            success = false;
            break;
          }
        const void* ptr = static_cast<const void*>(part->data());

        success = success and mz_zip_writer_add_mem(&zip, path.c_str(), ptr, part->size(), 0);
        if(not success)
          {
            break;
          }
      }

    void* raw = nullptr;
    size_t size = 0;

    if(success)
      {
        success = mz_zip_writer_finalize_heap_archive(&zip, &raw, &size);
      }

    mz_zip_writer_end(&zip);

    if(not success or raw == nullptr)
      {
        if(raw != nullptr)
          {
            mz_free(raw);
          }
        return false;
      }

    data.resize(size);
    std::memcpy(data.data(), raw, size);
    mz_free(raw);

    return true;
  }

  inline bool archive::write_to_file(const std::filesystem::path& path) const
  {
    bytes_type data;
    if(not write_to_memory(data))
      {
        return false;
      }

    std::ofstream ofs(path, std::ios::binary);
    if(not ofs)
      {
        return false;
      }

    ofs.write(reinterpret_cast<const char*>(data.data()),
              static_cast<std::streamsize>(data.size()));

    return static_cast<bool>(ofs);
  }

  inline bool archive::has(std::string_view path) const
  {
    return entries.count(std::string(path)) == 1 or source_entries.count(std::string(path)) == 1;
  }

  inline std::optional<std::string_view> archive::text(std::string_view path) const
  {
    const auto value = bytes(path);
    if(not value)
      {
        return std::nullopt;
      }
    return std::string_view(reinterpret_cast<const char*>(value->data()), value->size());
  }

  inline std::optional<std::span<const std::byte>> archive::bytes(std::string_view path) const
  {
    auto itr = entries.find(std::string(path));
    if(itr == entries.end())
      {
        auto value = extract(path);
        if(not value)
          {
            return std::nullopt;
          }
        itr = entries.emplace(std::string(path), std::move(*value)).first;
      }

    return std::span<const std::byte>(itr->second.data(), itr->second.size());
  }

  inline void archive::set_text(std::string_view path, std::string_view text)
  {
    if(not valid_path(path))
      {
        throw std::invalid_argument("invalid dclx part path");
      }
    const auto* ptr = reinterpret_cast<const std::byte*>(text.data());
    entries[std::string(path)] = bytes_type(ptr, ptr + text.size());
    source_entries.erase(std::string(path));
  }

  inline void archive::set_bytes(std::string_view path, std::span<const std::byte> data)
  {
    if(not valid_path(path))
      {
        throw std::invalid_argument("invalid dclx part path");
      }
    entries[std::string(path)] = bytes_type(data.begin(), data.end());
    source_entries.erase(std::string(path));
  }

  inline void archive::erase(std::string_view path)
  {
    entries.erase(std::string(path));
    source_entries.erase(std::string(path));
  }

  inline std::vector<std::string> archive::paths() const
  {
    std::vector<std::string> result;
    result.reserve(entries.size() + source_entries.size());

    for(const auto& item : entries)
      {
        result.push_back(item.first);
      }
    for(const auto& item : source_entries)
      {
        if(entries.count(item.first) == 0)
          {
            result.push_back(item.first);
          }
      }
    std::sort(result.begin(), result.end());

    return result;
  }

}

#endif
