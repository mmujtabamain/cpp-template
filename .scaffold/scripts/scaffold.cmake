# CLI orchestration only; imported modules define functions without executing work.
cmake_minimum_required(VERSION 3.24)
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/inputs.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/identity.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/compatibility.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/render.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/verify-output.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/replace.cmake")

# get absolute path; scaffold root
get_filename_component(scaffold_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(template_directory "${scaffold_root}/templates")
set(staging_directory "${scaffold_root}/.scaffold-tmp")

scaffold_validate_inputs(
    DESTINATION "${SCAFFOLD_DESTINATION}" DISPLAY_NAME "${PROJECT_DISPLAY_NAME}"
    TYPE "${PROJECT_TYPE}" COPY_GIT "${SCAFFOLD_GIT}"
    CMAKE_VERSION "${PROJECT_CMAKE_VERSION}" CPP_VERSION "${PROJECT_CPP_VERSION}"
    SCAFFOLD_ROOT "${scaffold_root}" OUTPUT request)
string(JSON destination GET "${request}" destination)
string(JSON display_name GET "${request}" display_name)
string(JSON project_type GET "${request}" type)
string(JSON copy_git GET "${request}" copy_git)
string(JSON requested_cmake GET "${request}" cmake_version)
string(JSON requested_cpp GET "${request}" cpp_version)

scaffold_project_identity("${display_name}" identity)
scaffold_resolve_compatibility(
    MANIFEST "${scaffold_root}/compatibility.json"
    CMAKE_VERSION "${requested_cmake}" CPP_VERSION "${requested_cpp}"
    RUNNING_CMAKE_VERSION "${CMAKE_VERSION}" OUTPUT versions)
string(JSON project_name GET "${identity}" name)
string(JSON project_namespace GET "${identity}" namespace)
string(JSON manifest_name GET "${identity}" manifest_name)
string(JSON use_presets GET "${versions}" use_presets)

scaffold_render_project(
    TEMPLATE_DIRECTORY "${template_directory}" STAGING_DIRECTORY "${staging_directory}"
    REQUEST "${request}" IDENTITY "${identity}" VERSIONS "${versions}")
scaffold_verify_output(
    STAGING_DIRECTORY "${staging_directory}" TYPE "${project_type}"
    NAME "${project_name}" NAMESPACE "${project_namespace}"
    COPY_GIT "${copy_git}" USE_PRESETS "${use_presets}")
scaffold_replace_project(
    DESTINATION "${destination}" STAGING_DIRECTORY "${staging_directory}"
    FORCE "${SCAFFOLD_FORCE}" OUTPUT installed)

if(installed)
    message(STATUS "Generated ${project_type}: ${display_name} (${project_name}, ${project_namespace}, ${manifest_name})")
    message(STATUS "Next: setup.sh / setup.bat, then run.sh / run.bat")
endif()
