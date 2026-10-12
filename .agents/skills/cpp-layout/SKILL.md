---
name: cpp-layout
description: Maintain the DocLang C++ class layout in src/doclang and src/pybind when adding or changing classes and methods.
---

# DocLang C++ class layout

Keep a class declaration easy to scan. Order access sections as `public`, then `protected` when needed, then `private` methods, then a separate `private` data section. Omit empty sections. Group related methods within each section using short `/* reading */`, `/* writing */`, or similarly concrete comments.

Declare methods inside the class and place their definitions after the closing `};`. In these header-only components, mark non-template definitions `inline` to preserve the one-definition rule. Put nested-class definitions after their enclosing class declaration when possible. Keep constructors, overloads, access levels, default arguments, and behavior intact when reorganizing an existing class.

Example:

```cpp
class archive
{
public:
  /* reading */
  bool has(std::string_view path) const;

protected:
  /* extension points */
  void on_change();

private:
  /* helpers */
  void set_error(std::string message);

private:
  /* state */
  std::string last_error;
};

inline void archive::set_error(std::string message)
{
  last_error = std::move(message);
}
```

Prefer a short exception only when an in-class body is required by the language (for example, a local class), and explain it in a comment. Run the relevant C++ build and tests after moving definitions.

Follow the repository's `.clang-format` settings for edited C++ files. The pre-commit hook uses clang-format 19.1.7 in check mode; compiling and passing tests do not establish formatting compliance. Format changed files, then run `uv run pre-commit run clang-format --all-files` before finishing.
