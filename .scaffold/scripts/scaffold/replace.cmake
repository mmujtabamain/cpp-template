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
    ask_yes_no(
        "An existing scaffolded project was detected.\n\nRe-scaffolding will permanently erase the existing generated project,\nincluding source files and changes made after scaffolding.\n\nContinue?"
        REPLACE_PROJECT
    )
    if(NOT REPLACE_PROJECT)
        file(REMOVE_RECURSE "${STAGING_DIRECTORY}")
        message("Scaffolding cancelled. Existing project is unchanged.")
        return()
    endif()
endif()

# MARK: Replacement and completion

# Only a fully rendered replacement reaches this destructive commit step.
foreach(GENERATED_PATH IN LISTS GENERATED_PATHS)
    if(IS_SYMLINK "${PROJECT_ROOT}/${GENERATED_PATH}")
        file(REMOVE "${PROJECT_ROOT}/${GENERATED_PATH}")
    else()
        file(REMOVE_RECURSE "${PROJECT_ROOT}/${GENERATED_PATH}")
    endif()
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
file(REMOVE_RECURSE "${STAGING_DIRECTORY}")
message(
    STATUS
        "Generated ${PROJECT_TYPE}: ${PROJECT_DISPLAY_NAME} (${PROJECT_NAME}, ${PROJECT_NAMESPACE}, ${PROJECT_MANIFEST_NAME})"
)
message(STATUS "Next: setup.sh / setup.bat, then run.sh / run.bat")
