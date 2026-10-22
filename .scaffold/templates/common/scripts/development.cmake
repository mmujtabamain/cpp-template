# MARK: Build Preset detection
function(resolve_development_preset REQUESTED_PRESET OUTPUT_VARIABLE)
    # empty string = debug
    if(REQUESTED_PRESET STREQUAL "")
        set(REQUESTED_PRESET debug)
    endif()

    # give error on invalid preset
    if(NOT REQUESTED_PRESET MATCHES "^(debug|release)$")
        message(FATAL_ERROR "Choose the debug or release development preset.")
    endif()

    # set mode; default debug
    set(${OUTPUT_VARIABLE} "${REQUESTED_PRESET}" PARENT_SCOPE)
endfunction()

# MARK: Configure arguments
function(make_development_configure_arguments PRESET OUTPUT_VARIABLE)
    @PROJECT_CONFIGURE_ARGUMENTS@

    # Use the same triplet for manifest installation and CMake builds
    if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT "$ENV{VCPKG_DEFAULT_TRIPLET}" STREQUAL "")
        list(APPEND CONFIGURE_ARGUMENTS "-DVCPKG_TARGET_TRIPLET=$ENV{VCPKG_DEFAULT_TRIPLET}")
    endif()

    set(${OUTPUT_VARIABLE} "${CONFIGURE_ARGUMENTS}" PARENT_SCOPE)
endfunction()

# Configure the generated project in its selected build directory.
function(configure_development_project PRESET)
    make_development_configure_arguments("${PRESET}" CONFIGURE_ARGUMENTS)
    set(CONFIGURE_DIRECTORY "@PROJECT_CONFIGURE_DIRECTORY@")
    file(MAKE_DIRECTORY "${CONFIGURE_DIRECTORY}")
    execute_process(
        COMMAND "${CMAKE_COMMAND}" ${CONFIGURE_ARGUMENTS}
        WORKING_DIRECTORY "${CONFIGURE_DIRECTORY}" RESULT_VARIABLE CONFIGURE_EXIT_CODE
    )
    if(NOT CONFIGURE_EXIT_CODE EQUAL 0)
        message(FATAL_ERROR "CMake configuration failed (${CONFIGURE_EXIT_CODE}).")
    endif()
endfunction()
