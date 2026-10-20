# Repeatable machine setup shared by the shell and Batch launchers.
# Reuse local tooling and build output; dependencies come exclusively from the manifest.

# MARK: Project paths and development preset

cmake_minimum_required(VERSION 3.24)

# Resolve paths from this script rather than the caller's working directory.
get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)

# Keep setup and run on the same supported development presets.
include("${CMAKE_CURRENT_LIST_DIR}/development.cmake")
resolve_development_preset("${DEV_PRESET}" DEV_PRESET)

# MARK: Prerequisites

# Fail early when required tools or generated project metadata are missing.
find_program(GIT_EXECUTABLE git REQUIRED)
find_program(NINJA_EXECUTABLE ninja REQUIRED)
if(NOT EXISTS "${PROJECT_ROOT}/vcpkg.json" OR NOT EXISTS "${PROJECT_ROOT}/CMakePresets.json")
    message(FATAL_ERROR "Missing generated project files. Run scaffold first.")
endif()
set(VCPKG_ROOT "${PROJECT_ROOT}/external/vcpkg")

# MARK: Local vcpkg acquisition

# Clone current upstream only when absent; history is unnecessary for disposable tooling.
if(NOT EXISTS "${VCPKG_ROOT}")
    file(MAKE_DIRECTORY "${PROJECT_ROOT}/external")
    execute_process(
        COMMAND "${GIT_EXECUTABLE}" clone --depth 1 https://github.com/microsoft/vcpkg.git
                "${VCPKG_ROOT}" COMMAND_ERROR_IS_FATAL ANY
    )
endif()

# Also recover a first setup interrupted between clone and Git metadata removal.
file(REMOVE_RECURSE "${VCPKG_ROOT}/.git")

# Select the host platform's bootstrap script and executable name.
if(CMAKE_HOST_WIN32)
    set(VCPKG_EXECUTABLE "${VCPKG_ROOT}/vcpkg.exe")
    set(VCPKG_BOOTSTRAP_SCRIPT "${VCPKG_ROOT}/bootstrap-vcpkg.bat")
else()
    set(VCPKG_EXECUTABLE "${VCPKG_ROOT}/vcpkg")
    set(VCPKG_BOOTSTRAP_SCRIPT "${VCPKG_ROOT}/bootstrap-vcpkg.sh")
endif()

# MARK: Bootstrap and installation validation

# An existing source tree may just need bootstrapping; never delete it on failure.
if(NOT EXISTS "${VCPKG_EXECUTABLE}")
    if(NOT EXISTS "${VCPKG_BOOTSTRAP_SCRIPT}")
        message(
            FATAL_ERROR
                "Malformed vcpkg tree at ${VCPKG_ROOT}: missing bootstrap script. Remove that directory manually and rerun setup to obtain a fresh copy."
        )
    endif()
    if(CMAKE_HOST_WIN32)
        execute_process(
            COMMAND cmd /c call "${VCPKG_BOOTSTRAP_SCRIPT}" -disableMetrics
            WORKING_DIRECTORY "${VCPKG_ROOT}" RESULT_VARIABLE BOOTSTRAP_EXIT_CODE
        )
    else()
        execute_process(
            COMMAND sh "${VCPKG_BOOTSTRAP_SCRIPT}" -disableMetrics WORKING_DIRECTORY "${VCPKG_ROOT}"
            RESULT_VARIABLE BOOTSTRAP_EXIT_CODE
        )
    endif()
    if(NOT BOOTSTRAP_EXIT_CODE EQUAL 0 OR NOT EXISTS "${VCPKG_EXECUTABLE}")
        message(
            FATAL_ERROR
                "vcpkg bootstrap failed at ${VCPKG_ROOT}. Check its output; remove the directory manually and rerun setup if a fresh copy is needed."
        )
    endif()
endif()

# Confirm the reused or newly bootstrapped installation is usable before installing packages.
execute_process(COMMAND "${VCPKG_EXECUTABLE}" version RESULT_VARIABLE VCPKG_VERSION_EXIT_CODE)
if(NOT VCPKG_VERSION_EXIT_CODE EQUAL 0 OR NOT EXISTS
                                          "${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
)
    message(
        FATAL_ERROR
            "Malformed vcpkg installation at ${VCPKG_ROOT}. Remove it manually and rerun setup for a fresh copy."
    )
endif()

# MARK: Manifest dependencies

# vcpkg's manifest is the sole dependency list. Use the same install root as presets.
set(VCPKG_INSTALL_ARGUMENTS install "--x-install-root=${PROJECT_ROOT}/vcpkg_installed")
if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT "$ENV{VCPKG_DEFAULT_TRIPLET}" STREQUAL "")
    list(APPEND VCPKG_INSTALL_ARGUMENTS "--triplet=$ENV{VCPKG_DEFAULT_TRIPLET}")
endif()
execute_process(
    COMMAND "${VCPKG_EXECUTABLE}" ${VCPKG_INSTALL_ARGUMENTS} WORKING_DIRECTORY "${PROJECT_ROOT}"
    COMMAND_ERROR_IS_FATAL ANY
)

# MARK: Development configuration

# Forward the same triplet override to CMake that was used for manifest installation.
# Configure in place without removing previous build output.
make_development_configure_arguments("${DEV_PRESET}" CONFIGURE_ARGUMENTS)
execute_process(
    COMMAND "${CMAKE_COMMAND}" ${CONFIGURE_ARGUMENTS} WORKING_DIRECTORY "${PROJECT_ROOT}"
    COMMAND_ERROR_IS_FATAL ANY
)
