include_guard(GLOBAL)
include("${CMAKE_CURRENT_LIST_DIR}/utils.cmake")

# Validate CLI input without reading templates or resolving version compatibility.
# OUTPUT: request record {destination, display_name, type, copy_git,
#                         cmake_version, cpp_version}.
function(scaffold_validate_inputs)
    cmake_parse_arguments(PARSE_ARGV 0 ARG ""
        "DESTINATION;DISPLAY_NAME;TYPE;COPY_GIT;CMAKE_VERSION;CPP_VERSION;SCAFFOLD_ROOT;OUTPUT" "")

    scaffold_require_value("SCAFFOLD_ROOT" "${ARG_SCAFFOLD_ROOT}")
    scaffold_require_value("OUTPUT" "${ARG_OUTPUT}")

    # require a destination; relative paths use the caller's working directory
    if(NOT DEFINED ARG_DESTINATION OR ARG_DESTINATION STREQUAL "")
        message(FATAL_ERROR "Supply SCAFFOLD_DESTINATION: the directory to scaffold into.")
    endif()

    # validate path
    if(ARG_DESTINATION MATCHES "[;\r\n]")
        message(FATAL_ERROR "Scaffold location cannot contain semicolons or newlines.")
    endif()

    # get absolute path
    get_filename_component(DESTINATION "${ARG_DESTINATION}" ABSOLUTE)
    file(REAL_PATH "${DESTINATION}" DESTINATION)
    file(REAL_PATH "${ARG_SCAFFOLD_ROOT}" SCAFFOLD_ROOT)
    cmake_path(IS_PREFIX SCAFFOLD_ROOT "${DESTINATION}" NORMALIZE DESTINATION_IN_SCAFFOLD)
    get_filename_component(DESTINATION_PARENT "${DESTINATION}" DIRECTORY)

    # validate location
    if(DESTINATION_IN_SCAFFOLD OR DESTINATION STREQUAL DESTINATION_PARENT)
        message(FATAL_ERROR "Choose a project location outside .scaffold and filesystem roots.")
    endif()
    if(EXISTS "${DESTINATION}" AND NOT IS_DIRECTORY "${DESTINATION}")
        message(FATAL_ERROR "Scaffold location must be a directory.")
    endif()

    if(NOT DEFINED ARG_DISPLAY_NAME OR NOT DEFINED ARG_TYPE)
        message(FATAL_ERROR "Supply PROJECT_DISPLAY_NAME and PROJECT_TYPE (exec or library).")
    endif()
    string(STRIP "${ARG_DISPLAY_NAME}" DISPLAY_NAME)
    string(TOLOWER "${ARG_TYPE}" TYPE)
    if(NOT TYPE STREQUAL "exec" AND NOT TYPE STREQUAL "library")
        message(FATAL_ERROR "Project type must be exec or library.")
    endif()

    if(NOT DEFINED ARG_COPY_GIT OR ARG_COPY_GIT STREQUAL "")
        set(ARG_COPY_GIT ON)
    endif()
    string(TOUPPER "${ARG_COPY_GIT}" COPY_GIT)
    if(NOT COPY_GIT MATCHES "^(ON|OFF)$")
        message(FATAL_ERROR "SCAFFOLD_GIT must be ON or OFF.")
    endif()

    scaffold_json_object(REQUEST
        destination "${DESTINATION}" display_name "${DISPLAY_NAME}" type "${TYPE}"
        copy_git "${COPY_GIT}" cmake_version "${ARG_CMAKE_VERSION}" cpp_version "${ARG_CPP_VERSION}")
    set("${ARG_OUTPUT}" "${REQUEST}" PARENT_SCOPE)
endfunction()
