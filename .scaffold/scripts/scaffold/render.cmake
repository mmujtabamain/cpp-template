include_guard(GLOBAL)
include("${CMAKE_CURRENT_LIST_DIR}/utils.cmake")

# Render into staging only. REQUEST, IDENTITY and VERSIONS are value records;
# template substitution variables exist only inside this function.
function(scaffold_render_project)
    cmake_parse_arguments(PARSE_ARGV 0 ARG ""
        "TEMPLATE_DIRECTORY;STAGING_DIRECTORY;REQUEST;IDENTITY;VERSIONS" "")
    scaffold_require_directory("TEMPLATE_DIRECTORY" "${ARG_TEMPLATE_DIRECTORY}")
    scaffold_require_directory("STAGING_DIRECTORY" "${ARG_STAGING_DIRECTORY}")
    scaffold_require_value("REQUEST" "${ARG_REQUEST}")
    scaffold_require_value("IDENTITY" "${ARG_IDENTITY}")
    scaffold_require_value("VERSIONS" "${ARG_VERSIONS}")
    file(REAL_PATH "${ARG_TEMPLATE_DIRECTORY}" TEMPLATE_PATH)
    file(REAL_PATH "${ARG_STAGING_DIRECTORY}" STAGING_PATH)
    cmake_path(IS_PREFIX STAGING_PATH "${TEMPLATE_PATH}" NORMALIZE STAGING_CONTAINS_TEMPLATES)
    if(STAGING_CONTAINS_TEMPLATES)
        message(FATAL_ERROR "Staging must not contain the template directory.")
    endif()
    set(TEMPLATE_DIRECTORY "${ARG_TEMPLATE_DIRECTORY}")
    set(STAGING_DIRECTORY "${ARG_STAGING_DIRECTORY}")
    string(JSON PROJECT_DISPLAY_NAME GET "${ARG_REQUEST}" display_name)
    string(JSON PROJECT_TYPE GET "${ARG_REQUEST}" type)
    string(JSON SCAFFOLD_GIT GET "${ARG_REQUEST}" copy_git)
    string(JSON PROJECT_NAME GET "${ARG_IDENTITY}" name)
    string(JSON PROJECT_NAMESPACE GET "${ARG_IDENTITY}" namespace)
    string(JSON PROJECT_MACRO GET "${ARG_IDENTITY}" macro)
    string(JSON PROJECT_MANIFEST_NAME GET "${ARG_IDENTITY}" manifest_name)
    string(JSON PROJECT_CMAKE_VERSION GET "${ARG_VERSIONS}" cmake_version)
    string(JSON PROJECT_CMAKE_MAJOR GET "${ARG_VERSIONS}" cmake_major)
    string(JSON PROJECT_CMAKE_MINOR GET "${ARG_VERSIONS}" cmake_minor)
    string(JSON PROJECT_CMAKE_PATCH GET "${ARG_VERSIONS}" cmake_patch)
    string(JSON PROJECT_CPP_VERSION GET "${ARG_VERSIONS}" cpp_version)
    string(JSON PROJECT_CPP_FEATURE GET "${ARG_VERSIONS}" cpp_feature)
    string(JSON PROJECT_USE_PRESETS GET "${ARG_VERSIONS}" use_presets)
    string(JSON PROJECT_PRESET_SCHEMA GET "${ARG_VERSIONS}" preset_schema)

    # Preserve the package-config placeholder for the generated configure step.
    set(PACKAGE_INIT "@PACKAGE_INIT@")
    if(SCAFFOLD_GIT)
        file(READ "${TEMPLATE_DIRECTORY}/fragments/git-enabled.md" PROJECT_GIT_GUIDE)
    else()
        file(READ "${TEMPLATE_DIRECTORY}/fragments/git-disabled.md" PROJECT_GIT_GUIDE)
    endif()
    if(PROJECT_USE_PRESETS)
        file(READ "${TEMPLATE_DIRECTORY}/fragments/build-presets.md" PROJECT_BUILD_GUIDE)
    else()
        file(READ "${TEMPLATE_DIRECTORY}/fragments/build-cmake-legacy.md" PROJECT_BUILD_GUIDE)
    endif()

    # Specialize the generated files once; the new project needs no version branches.
    if(PROJECT_USE_PRESETS)
        set(PROJECT_CONFIGURE_ARGUMENTS "set(CONFIGURE_ARGUMENTS --preset \"\${PRESET}\")")
        set(PROJECT_CONFIGURE_DIRECTORY "\${PROJECT_ROOT}")
    else()
        file(READ "${TEMPLATE_DIRECTORY}/fragments/configure-direct.cmake.in" PROJECT_CONFIGURE_ARGUMENTS)
        set(PROJECT_CONFIGURE_DIRECTORY "\${PROJECT_ROOT}/build/\${PRESET}")
    endif()
    set(PROJECT_SOURCE_DISCOVERY_OPTION "CONFIGURE_DEPENDS ")
    set(PROJECT_SOURCE_DISCOVERY_GUIDE "New source files are discovered automatically during builds.")
    if(PROJECT_CMAKE_VERSION VERSION_LESS "3.12")
        set(PROJECT_SOURCE_DISCOVERY_OPTION "")
        set(PROJECT_SOURCE_DISCOVERY_GUIDE "Rerun setup after adding or removing source files.")
    endif()

    set(PROJECT_EXECUTABLE_RUN_DIRECTORY "$<TARGET_FILE_DIR:\${PROJECT_NAME}>")
    set(PROJECT_LIBRARY_RUN_DIRECTORY "$<TARGET_FILE_DIR:\${PROJECT_NAME}_example>")
    if(PROJECT_CMAKE_VERSION VERSION_LESS "3.13")
        set(PROJECT_EXECUTABLE_RUN_DIRECTORY "\${CMAKE_CURRENT_BINARY_DIR}/\${CMAKE_CFG_INTDIR}")
        set(PROJECT_LIBRARY_RUN_DIRECTORY "\${CMAKE_CURRENT_BINARY_DIR}/bin/\${CMAKE_CFG_INTDIR}")
    endif()

    # MARK: Template rendering

    # Discard interrupted staging output; existing project files remain untouched here.
    scaffold_remove_path("${STAGING_DIRECTORY}")
    file(MAKE_DIRECTORY "${STAGING_DIRECTORY}")

    # Render common development tools, then the selected project type.
    set(TEMPLATE_KINDS common "${PROJECT_TYPE}")
    if(SCAFFOLD_GIT)
        list(APPEND TEMPLATE_KINDS git)
    endif()
    foreach(TEMPLATE_KIND IN LISTS TEMPLATE_KINDS)
        if(TEMPLATE_KIND STREQUAL "exec")
            set(TEMPLATE_KIND executable)
        endif()
        file(
            GLOB_RECURSE TEMPLATE_INPUT_PATHS
            LIST_DIRECTORIES false
            RELATIVE "${TEMPLATE_DIRECTORY}/${TEMPLATE_KIND}"
            "${TEMPLATE_DIRECTORY}/${TEMPLATE_KIND}/*"
        )
        foreach(TEMPLATE_INPUT_PATH IN LISTS TEMPLATE_INPUT_PATHS)
            if(NOT SCAFFOLD_GIT AND TEMPLATE_INPUT_PATH MATCHES "(^|/)\\.gitkeep$")
                continue()
            endif()
            if(NOT PROJECT_USE_PRESETS AND TEMPLATE_INPUT_PATH STREQUAL "CMakePresets.json.in")
                continue()
            endif()
            set(GENERATED_RELATIVE_PATH "${TEMPLATE_INPUT_PATH}")
            # Replace generic library paths with the normalized package and namespace names.
            if(TEMPLATE_KIND STREQUAL "library")
                string(REPLACE "include/project/project.hpp"
                               "include/${PROJECT_NAMESPACE}/${PROJECT_NAMESPACE}.hpp"
                               GENERATED_RELATIVE_PATH "${GENERATED_RELATIVE_PATH}"
                )
                string(REPLACE "src/project.cpp" "src/${PROJECT_NAMESPACE}.cpp" GENERATED_RELATIVE_PATH
                               "${GENERATED_RELATIVE_PATH}"
                )
                string(REPLACE "tests/project_test.cpp" "tests/${PROJECT_NAMESPACE}_test.cpp"
                               GENERATED_RELATIVE_PATH "${GENERATED_RELATIVE_PATH}"
                )
                string(REPLACE "cmake/ProjectConfig.cmake.in" "cmake/${PROJECT_NAME}Config.cmake.in"
                               GENERATED_RELATIVE_PATH "${GENERATED_RELATIVE_PATH}"
                )
            endif()
            # The package config remains a CMake input template after scaffolding.
            if(NOT GENERATED_RELATIVE_PATH MATCHES "Config\\.cmake\\.in$")
                string(REGEX REPLACE "\\.in$" "" GENERATED_RELATIVE_PATH "${GENERATED_RELATIVE_PATH}")
            endif()
            configure_file(
                "${TEMPLATE_DIRECTORY}/${TEMPLATE_KIND}/${TEMPLATE_INPUT_PATH}"
                "${STAGING_DIRECTORY}/${GENERATED_RELATIVE_PATH}" @ONLY
            )
        endforeach()
    endforeach()
    if(PROJECT_TYPE STREQUAL "exec")
        file(MAKE_DIRECTORY "${STAGING_DIRECTORY}/assets")
    endif()
endfunction()
