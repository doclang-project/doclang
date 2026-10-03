cmake_minimum_required(VERSION 3.21)
project(doclang LANGUAGES C CXX)

include(FetchContent)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(BUILD_SHARED_LIBS OFF)

find_package(pugixml CONFIG QUIET)
if(NOT TARGET pugixml::pugixml)
  set(PUGIXML_INSTALL OFF CACHE BOOL "" FORCE)
  FetchContent_Declare(
    pugixml
    GIT_REPOSITORY https://github.com/zeux/pugixml.git
    GIT_TAG v1.15
    GIT_SHALLOW TRUE
  )
  FetchContent_MakeAvailable(pugixml)
endif()

find_package(miniz CONFIG QUIET)
if(TARGET miniz::miniz)
  set(DOCLANG_MINIZ_TARGET miniz::miniz)
elseif(TARGET miniz)
  set(DOCLANG_MINIZ_TARGET miniz)
else()
  set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
  set(BUILD_FUZZERS OFF CACHE BOOL "" FORCE)
  set(INSTALL_PROJECT OFF CACHE BOOL "" FORCE)
  # miniz 3.0.2 declares CMake 3.0 and leaves CMP0077 unset.
  set(CMAKE_POLICY_VERSION_MINIMUM 3.10)
  set(CMAKE_POLICY_DEFAULT_CMP0077 NEW)
  FetchContent_Declare(
    miniz
    GIT_REPOSITORY https://github.com/richgel999/miniz.git
    GIT_TAG 3.0.2
    GIT_SHALLOW TRUE
  )
  FetchContent_MakeAvailable(miniz)
  unset(CMAKE_POLICY_DEFAULT_CMP0077)
  unset(CMAKE_POLICY_VERSION_MINIMUM)
  set(DOCLANG_MINIZ_TARGET miniz)
endif()

find_package(LibXml2 REQUIRED)
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/doclang/doclang.xsd" DOCLANG_XSD_TEXT)
file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/generated/doclang/validation")
configure_file(
  "${CMAKE_CURRENT_SOURCE_DIR}/src/doclang/validation/schema_data.h.in"
  "${CMAKE_CURRENT_BINARY_DIR}/generated/doclang/validation/schema_data.h"
  @ONLY)

add_library(doclang_native INTERFACE)
target_compile_features(doclang_native INTERFACE cxx_std_20)
target_include_directories(doclang_native INTERFACE
  ${CMAKE_CURRENT_SOURCE_DIR}/src ${CMAKE_CURRENT_BINARY_DIR}/generated)
target_link_libraries(doclang_native INTERFACE
  pugixml::pugixml ${DOCLANG_MINIZ_TARGET} LibXml2::LibXml2)

set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)
pybind11_add_module(_native src/pybind/doclang_module.cpp)
target_link_libraries(_native PRIVATE doclang_native)
install(TARGETS _native LIBRARY DESTINATION doclang RUNTIME DESTINATION doclang)
