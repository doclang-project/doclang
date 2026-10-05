# Native C++ tests

These tests link directly to the header-only `doclang_native` target. They do not
build or import the Python extension.

Build and run the core tests:

```sh
cmake -S . -B build/native-tests -DDOCLANG_BUILD_PYTHON=OFF -DDOCLANG_BUILD_CPP_TESTS=ON
cmake --build build/native-tests
ctest --test-dir build/native-tests --output-on-failure
```

The validation suite is optional. To include it, configure with
`-DDOCLANG_BUILD_VALIDATION_TESTS=ON`, rebuild, then run the suites separately:

```sh
ctest --test-dir build/native-tests -L core --output-on-failure
ctest --test-dir build/native-tests -L validation --output-on-failure
```

The validation tests cover all 19 native Schematron assertions, plus XSD,
namespace, local, and contextual validation. Test fixtures are shared with the
Python suite under `tests/data/`.
