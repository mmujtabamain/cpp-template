# MARK: Template rendering

# Discard interrupted staging output; existing project files remain untouched here.
file(REMOVE_RECURSE "${STAGING_DIRECTORY}")
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
if(PROJECT_TYPE STREQUAL "exec")
    set(TYPE_REQUIRED_PATHS src/main.cpp)
else()
    set(TYPE_REQUIRED_PATHS
        "include/${PROJECT_NAMESPACE}/${PROJECT_NAMESPACE}.hpp" "src/${PROJECT_NAMESPACE}.cpp"
        examples/main.cpp "tests/${PROJECT_NAMESPACE}_test.cpp"
        "cmake/${PROJECT_NAME}Config.cmake.in"
    )
endif()

