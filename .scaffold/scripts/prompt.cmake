# MARK: Confirmation
function(ask_yes_no PROMPT_TEXT OUTPUT_VARIABLE)
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
