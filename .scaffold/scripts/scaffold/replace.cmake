include_guard(GLOBAL)
include("${CMAKE_CURRENT_LIST_DIR}/utils.cmake")

# Confirm and install an already verified staging tree.
# OUTPUT is ON when installed, OFF when replacement is declined.
function(scaffold_replace_project)
    cmake_parse_arguments(PARSE_ARGV 0 ARG ""
        "DESTINATION;STAGING_DIRECTORY;FORCE;OUTPUT" "")
    scaffold_require_directory("DESTINATION" "${ARG_DESTINATION}")
    scaffold_require_directory("STAGING_DIRECTORY" "${ARG_STAGING_DIRECTORY}")
    scaffold_require_value("OUTPUT" "${ARG_OUTPUT}")
    if(NOT IS_DIRECTORY "${ARG_STAGING_DIRECTORY}")
        message(FATAL_ERROR "The verified staging directory is missing.")
    endif()
    file(REAL_PATH "${ARG_DESTINATION}" DESTINATION_PATH)
    file(REAL_PATH "${ARG_STAGING_DIRECTORY}" STAGING_PATH)
    cmake_path(IS_PREFIX STAGING_PATH "${DESTINATION_PATH}" NORMALIZE STAGING_CONTAINS_DESTINATION)
    if(STAGING_CONTAINS_DESTINATION)
        message(FATAL_ERROR "Staging must not contain the destination.")
    endif()
    set(PROJECT_ROOT "${ARG_DESTINATION}")
    set(STAGING_DIRECTORY "${ARG_STAGING_DIRECTORY}")
    set(SCAFFOLD_FORCE "${ARG_FORCE}")
    # MARK: Generated project detection

    # generated project files are replaced; scaffold sources and unrelated files stay
    set(GENERATED_PATHS
        CMakeLists.txt
        CMakePresets.json
        vcpkg.json
        README.md
        src
        include
        assets
        examples
        tests
        cmake
        scripts
        setup.sh
        setup.bat
        run.sh
        run.bat
        build
        vcpkg_installed
    )
    # A generated path is removed during replacement; staging cannot live there.
    foreach(GENERATED_PATH IN LISTS GENERATED_PATHS)
        file(REAL_PATH "${PROJECT_ROOT}/${GENERATED_PATH}" GENERATED_ABSOLUTE_PATH)
        cmake_path(IS_PREFIX GENERATED_ABSOLUTE_PATH "${STAGING_PATH}" NORMALIZE STAGING_IN_GENERATED_PATH)
        if(STAGING_IN_GENERATED_PATH)
            message(FATAL_ERROR "Staging must be outside generated paths: ${GENERATED_PATH}.")
        endif()
    endforeach()
    set(HAS_GENERATED_PROJECT false)
    foreach(GENERATED_PATH IN LISTS GENERATED_PATHS)
        # the template README also exists before scaffolding
        if(NOT GENERATED_PATH STREQUAL "README.md"
           AND (EXISTS "${PROJECT_ROOT}/${GENERATED_PATH}" OR IS_SYMLINK
                                                              "${PROJECT_ROOT}/${GENERATED_PATH}")
        )
            set(HAS_GENERATED_PROJECT true)
        endif()
    endforeach()

    # MARK: Destructive replacement confirmation

    # Ask only after a replacement is ready. EOF and any answer other than yes cancel.
    if(HAS_GENERATED_PROJECT AND NOT SCAFFOLD_FORCE)
        scaffold_ask_yes_no(
            "An existing scaffolded project was detected.\n\nRe-scaffolding will permanently erase the existing generated project,\nincluding source files and changes made after scaffolding.\n\nContinue?"
            REPLACE_PROJECT
        )
        if(NOT REPLACE_PROJECT)
            scaffold_remove_path("${STAGING_DIRECTORY}")
            message("Scaffolding cancelled. Existing project is unchanged.")
            set("${ARG_OUTPUT}" OFF PARENT_SCOPE)
            return()
        endif()
    endif()

    # MARK: Replacement and completion

    # Generated Unix launchers must be executable immediately after scaffolding.
    file(
        CHMOD
        "${STAGING_DIRECTORY}/setup.sh"
        "${STAGING_DIRECTORY}/run.sh"
        PERMISSIONS
        OWNER_READ
        OWNER_WRITE
        OWNER_EXECUTE
        GROUP_READ
        GROUP_EXECUTE
        WORLD_READ
        WORLD_EXECUTE
    )

    # Only a fully rendered replacement reaches this destructive commit step.
    foreach(GENERATED_PATH IN LISTS GENERATED_PATHS)
        scaffold_remove_path("${PROJECT_ROOT}/${GENERATED_PATH}")
    endforeach()

    # install staged files while leaving unrelated destination files alone
    file(
        GLOB_RECURSE GENERATED_RELATIVE_PATHS
        LIST_DIRECTORIES true
        RELATIVE "${STAGING_DIRECTORY}"
        "${STAGING_DIRECTORY}/*"
    )
    foreach(GENERATED_RELATIVE_PATH IN LISTS GENERATED_RELATIVE_PATHS)
        if(IS_DIRECTORY "${STAGING_DIRECTORY}/${GENERATED_RELATIVE_PATH}")
            file(MAKE_DIRECTORY "${PROJECT_ROOT}/${GENERATED_RELATIVE_PATH}")
        else()
            get_filename_component(
                OUTPUT_PARENT_DIRECTORY "${PROJECT_ROOT}/${GENERATED_RELATIVE_PATH}" DIRECTORY
            )
            file(MAKE_DIRECTORY "${OUTPUT_PARENT_DIRECTORY}")
            file(RENAME "${STAGING_DIRECTORY}/${GENERATED_RELATIVE_PATH}"
                 "${PROJECT_ROOT}/${GENERATED_RELATIVE_PATH}"
            )
        endif()
    endforeach()
    scaffold_remove_path("${STAGING_DIRECTORY}")

    set("${ARG_OUTPUT}" ON PARENT_SCOPE)
endfunction()
