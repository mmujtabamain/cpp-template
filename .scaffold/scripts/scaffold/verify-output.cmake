include_guard(GLOBAL)
include("${CMAKE_CURRENT_LIST_DIR}/utils.cmake")

# Inspect an existing staging tree without rendering or changing files.
function(scaffold_verify_output)
    cmake_parse_arguments(PARSE_ARGV 0 ARG ""
        "STAGING_DIRECTORY;TYPE;NAME;NAMESPACE;COPY_GIT;USE_PRESETS" "")
    scaffold_require_directory("STAGING_DIRECTORY" "${ARG_STAGING_DIRECTORY}")
    scaffold_require_value("TYPE" "${ARG_TYPE}")
    scaffold_require_value("NAME" "${ARG_NAME}")
    scaffold_require_value("NAMESPACE" "${ARG_NAMESPACE}")
    scaffold_require_value("COPY_GIT" "${ARG_COPY_GIT}")
    scaffold_require_value("USE_PRESETS" "${ARG_USE_PRESETS}")
    set(STAGING_DIRECTORY "${ARG_STAGING_DIRECTORY}")
    set(PROJECT_TYPE "${ARG_TYPE}")
    set(PROJECT_NAME "${ARG_NAME}")
    set(PROJECT_NAMESPACE "${ARG_NAMESPACE}")
    set(SCAFFOLD_GIT "${ARG_COPY_GIT}")
    set(PROJECT_USE_PRESETS "${ARG_USE_PRESETS}")
    if(PROJECT_TYPE STREQUAL "exec")
        set(TYPE_REQUIRED_PATHS src/main.cpp)
    else()
        set(TYPE_REQUIRED_PATHS
            "include/${PROJECT_NAMESPACE}/${PROJECT_NAMESPACE}.hpp" "src/${PROJECT_NAMESPACE}.cpp"
            examples/main.cpp "tests/${PROJECT_NAMESPACE}_test.cpp"
            "cmake/${PROJECT_NAME}Config.cmake.in"
        )
    endif()

    # MARK: Staged project validation

    # Check required files and JSON before asking to replace the existing project.
    foreach(
        REQUIRED_PATH
        ${TYPE_REQUIRED_PATHS}
        CMakeLists.txt
        vcpkg.json
        README.md
        scripts/setup.cmake
        scripts/run.cmake
        scripts/development.cmake
        setup.sh
        setup.bat
        run.sh
        run.bat
    )
        if(NOT EXISTS "${STAGING_DIRECTORY}/${REQUIRED_PATH}")
            message(
                FATAL_ERROR
                    "Incomplete staged project: missing ${REQUIRED_PATH}. Existing project is untouched."
            )
        endif()
    endforeach()
    if(SCAFFOLD_GIT)
        foreach(GIT_REQUIRED_PATH .github/workflows/validate.yml .github/rulesets/protect-main.json
                                  .gitignore .gitattributes
        )
            if(NOT EXISTS "${STAGING_DIRECTORY}/${GIT_REQUIRED_PATH}")
                message(
                    FATAL_ERROR
                        "Incomplete staged project: missing ${GIT_REQUIRED_PATH}. Existing project is untouched."
                )
            endif()
        endforeach()
    endif()
    set(JSON_FILENAMES vcpkg.json)
    if(PROJECT_USE_PRESETS)
        list(APPEND JSON_FILENAMES CMakePresets.json)
        if(NOT EXISTS "${STAGING_DIRECTORY}/CMakePresets.json")
            message(FATAL_ERROR "Incomplete staged project: missing CMakePresets.json. Existing project is untouched.")
        endif()
    endif()
    foreach(JSON_FILENAME IN LISTS JSON_FILENAMES)
        file(READ "${STAGING_DIRECTORY}/${JSON_FILENAME}" JSON_CONTENT)
        string(JSON JSON_VALUE_TYPE ERROR_VARIABLE JSON_ERROR TYPE "${JSON_CONTENT}")
        if(NOT JSON_ERROR STREQUAL "NOTFOUND" OR NOT JSON_VALUE_TYPE STREQUAL "OBJECT")
            message(
                FATAL_ERROR
                    "Invalid staged ${JSON_FILENAME}: ${JSON_ERROR}. Existing project is untouched."
            )
        endif()
    endforeach()

endfunction()
