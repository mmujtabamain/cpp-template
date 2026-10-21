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
    set(CONFIGURE_ARGUMENTS --preset "${PRESET}")

    # Use the same triplet for manifest installation and CMake builds
    if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT "$ENV{VCPKG_DEFAULT_TRIPLET}" STREQUAL "")
        list(APPEND CONFIGURE_ARGUMENTS "-DVCPKG_TARGET_TRIPLET=$ENV{VCPKG_DEFAULT_TRIPLET}")
    endif()

    set(${OUTPUT_VARIABLE} "${CONFIGURE_ARGUMENTS}" PARENT_SCOPE)
endfunction()
