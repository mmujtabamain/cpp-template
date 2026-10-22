# MARK: Paths and input validation

get_filename_component(SCAFFOLD_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
set(TEMPLATE_DIRECTORY "${SCAFFOLD_ROOT}/templates")
set(STAGING_DIRECTORY "${SCAFFOLD_ROOT}/.scaffold-tmp")

# require a destination; relative paths use the caller's working directory
if(NOT DEFINED SCAFFOLD_DESTINATION OR SCAFFOLD_DESTINATION STREQUAL "")
    message(FATAL_ERROR "Supply SCAFFOLD_DESTINATION: the directory to scaffold into.")
endif()
if(SCAFFOLD_DESTINATION MATCHES "[;\r\n]")
    message(FATAL_ERROR "Scaffold location cannot contain semicolons or newlines.")
endif()
get_filename_component(PROJECT_ROOT "${SCAFFOLD_DESTINATION}" ABSOLUTE)
file(REAL_PATH "${PROJECT_ROOT}" PROJECT_ROOT)
file(REAL_PATH "${SCAFFOLD_ROOT}" SCAFFOLD_ROOT)
cmake_path(IS_PREFIX SCAFFOLD_ROOT "${PROJECT_ROOT}" NORMALIZE DESTINATION_IN_SCAFFOLD)
get_filename_component(DESTINATION_PARENT "${PROJECT_ROOT}" DIRECTORY)
if(DESTINATION_IN_SCAFFOLD OR PROJECT_ROOT STREQUAL DESTINATION_PARENT)
    message(FATAL_ERROR "Choose a project location outside .scaffold and filesystem roots.")
endif()
if(EXISTS "${PROJECT_ROOT}" AND NOT IS_DIRECTORY "${PROJECT_ROOT}")
    message(FATAL_ERROR "Scaffold location must be a directory.")
endif()

# CMAKE_VERSION is the version of the executable running this scaffold.
if(NOT DEFINED PROJECT_CMAKE_VERSION OR PROJECT_CMAKE_VERSION STREQUAL "")
    set(PROJECT_CMAKE_VERSION "${CMAKE_VERSION}")
endif()
if(NOT PROJECT_CMAKE_VERSION MATCHES "^[1-9][0-9]*\\.(0|[1-9][0-9]*)(\\.(0|[1-9][0-9]*))?$")
    message(FATAL_ERROR "CMake version must be major.minor or major.minor.patch.")
endif()
if(PROJECT_CMAKE_VERSION VERSION_GREATER CMAKE_VERSION)
    message(FATAL_ERROR "Requested CMake ${PROJECT_CMAKE_VERSION} exceeds running CMake ${CMAKE_VERSION}; install it before scaffolding.")
endif()
string(REPLACE "." ";" PROJECT_CMAKE_PARTS "${PROJECT_CMAKE_VERSION}")
list(GET PROJECT_CMAKE_PARTS 0 PROJECT_CMAKE_MAJOR)
list(GET PROJECT_CMAKE_PARTS 1 PROJECT_CMAKE_MINOR)
list(LENGTH PROJECT_CMAKE_PARTS PROJECT_CMAKE_PART_COUNT)
set(PROJECT_CMAKE_PATCH 0)
if(PROJECT_CMAKE_PART_COUNT EQUAL 3)
    list(GET PROJECT_CMAKE_PARTS 2 PROJECT_CMAKE_PATCH)
endif()
set(PROJECT_CMAKE_VERSION "${PROJECT_CMAKE_MAJOR}.${PROJECT_CMAKE_MINOR}.${PROJECT_CMAKE_PATCH}")

include("${CMAKE_CURRENT_LIST_DIR}/compatibility.cmake")

# optionally copy template Git files; repository management belongs to the user
if(NOT DEFINED SCAFFOLD_GIT)
    set(SCAFFOLD_GIT ON)
endif()
string(TOUPPER "${SCAFFOLD_GIT}" SCAFFOLD_GIT)
if(NOT SCAFFOLD_GIT MATCHES "^(ON|OFF)$")
    message(FATAL_ERROR "SCAFFOLD_GIT must be ON or OFF.")
endif()

if(SCAFFOLD_GIT)
    file(READ "${TEMPLATE_DIRECTORY}/fragments/git-enabled.md" PROJECT_GIT_GUIDE)
else()
    file(READ "${TEMPLATE_DIRECTORY}/fragments/git-disabled.md" PROJECT_GIT_GUIDE)
endif()

# Validate every input before touching generated output or the previous staging tree.
if(NOT DEFINED PROJECT_DISPLAY_NAME OR NOT DEFINED PROJECT_TYPE)
    message(FATAL_ERROR "Supply PROJECT_DISPLAY_NAME and PROJECT_TYPE (exec or library).")
endif()
string(STRIP "${PROJECT_DISPLAY_NAME}" PROJECT_DISPLAY_NAME)
if(NOT PROJECT_DISPLAY_NAME MATCHES "^[A-Za-z][A-Za-z0-9 _-]*$")
    message(
        FATAL_ERROR
            "Project name must start with a letter and contain only ASCII letters, digits, spaces, underscores or hyphens."
    )
endif()
string(TOLOWER "${PROJECT_TYPE}" PROJECT_TYPE)
if(NOT PROJECT_TYPE STREQUAL "exec" AND NOT PROJECT_TYPE STREQUAL "library")
    message(FATAL_ERROR "Project type must be exec or library.")
endif()

