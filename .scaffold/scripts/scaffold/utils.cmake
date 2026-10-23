# Shared helpers; importing this file performs no project work.
include_guard(GLOBAL)

# Public module arguments must be explicit, including output variable names.
function(scaffold_require_value LABEL VALUE)
    if("${VALUE}" STREQUAL "")
        message(FATAL_ERROR "${LABEL} is required.")
    endif()
endfunction()

# Guard destructive operations even when a module is called without the CLI.
function(scaffold_require_directory LABEL PATH)
    scaffold_require_value("${LABEL}" "${PATH}")
    if(PATH MATCHES "[;\r\n]")
        message(FATAL_ERROR "${LABEL} cannot contain semicolons or newlines.")
    endif()
    get_filename_component(ABSOLUTE_PATH "${PATH}" ABSOLUTE)
    file(REAL_PATH "${ABSOLUTE_PATH}" RESOLVED_PATH)
    get_filename_component(PARENT_PATH "${RESOLVED_PATH}" DIRECTORY)
    if(RESOLVED_PATH STREQUAL PARENT_PATH)
        message(FATAL_ERROR "${LABEL} cannot be a filesystem root.")
    endif()
    if(EXISTS "${PATH}" AND NOT IS_DIRECTORY "${PATH}")
        message(FATAL_ERROR "${LABEL} must be a directory.")
    endif()
endfunction()

# Encode an explicit set of key/value pairs as a JSON record.
# JSON keeps multiline strings and semicolons intact across module boundaries.
function(scaffold_json_object OUTPUT)
    scaffold_require_value("JSON output variable" "${OUTPUT}")
    math(EXPR PAIR_REMAINDER "(${ARGC} - 1) % 2")
    if(PAIR_REMAINDER)
        message(FATAL_ERROR "scaffold_json_object expects key/value pairs.")
    endif()
    set(OBJECT "{}")
    set(INDEX 1)
    while(INDEX LESS ARGC)
        set(KEY "${ARGV${INDEX}}")
        math(EXPR INDEX "${INDEX} + 1")
        set(VALUE "${ARGV${INDEX}}")
        string(REPLACE "\\" "\\\\" VALUE "${VALUE}")
        string(REPLACE "\"" "\\\"" VALUE "${VALUE}")
        string(REPLACE "\n" "\\n" VALUE "${VALUE}")
        string(REPLACE "\r" "\\r" VALUE "${VALUE}")
        string(REPLACE "\t" "\\t" VALUE "${VALUE}")
        string(JSON OBJECT SET "${OBJECT}" "${KEY}" "\"${VALUE}\"")
        math(EXPR INDEX "${INDEX} + 1")
    endwhile()
    set("${OUTPUT}" "${OBJECT}" PARENT_SCOPE)
endfunction()

# Remove the requested path, never the target of a directory symlink.
function(scaffold_remove_path PATH)
    if(IS_SYMLINK "${PATH}")
        file(REMOVE "${PATH}")
    else()
        file(REMOVE_RECURSE "${PATH}")
    endif()
endfunction()

# Cross Platform function for asking yes or no
function(scaffold_ask_yes_no PROMPT_TEXT OUTPUT_VARIABLE)
    message("${PROMPT_TEXT} [y/N]")

    # read one answer; EOF and anything other than yes mean no
    if(CMAKE_HOST_WIN32)
        execute_process(
            COMMAND powershell -NoProfile -Command "[Console]::ReadLine()" OUTPUT_VARIABLE ANSWER
            RESULT_VARIABLE PROMPT_EXIT_CODE
        )
    else()
        execute_process(
            COMMAND sh -c "IFS= read -r answer; printf '%s' \"$answer\"" OUTPUT_VARIABLE ANSWER
            RESULT_VARIABLE PROMPT_EXIT_CODE
        )
    endif()

    string(STRIP "${ANSWER}" ANSWER)
    string(TOLOWER "${ANSWER}" ANSWER)

    if(PROMPT_EXIT_CODE EQUAL 0 AND ANSWER MATCHES "^(y|yes)$")
        set(${OUTPUT_VARIABLE} ON PARENT_SCOPE)
    else()
        set(${OUTPUT_VARIABLE} OFF PARENT_SCOPE)
    endif()
endfunction()
