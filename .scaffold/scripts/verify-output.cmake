# MARK: Staged project validation

# Check required files and JSON before asking to replace the existing project.
foreach(
    REQUIRED_PATH
    ${TYPE_REQUIRED_PATHS}
    CMakeLists.txt
    CMakePresets.json
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
foreach(JSON_FILENAME CMakePresets.json vcpkg.json)
    file(READ "${STAGING_DIRECTORY}/${JSON_FILENAME}" JSON_CONTENT)
    string(JSON JSON_VALUE_TYPE ERROR_VARIABLE JSON_ERROR TYPE "${JSON_CONTENT}")
    if(NOT JSON_ERROR STREQUAL "NOTFOUND" OR NOT JSON_VALUE_TYPE STREQUAL "OBJECT")
        message(
            FATAL_ERROR
                "Invalid staged ${JSON_FILENAME}: ${JSON_ERROR}. Existing project is untouched."
        )
    endif()
endforeach()

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

