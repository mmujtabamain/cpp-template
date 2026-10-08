# Repeatable machine setup shared by the shell and Batch launchers.
# Reuse local tooling and build output; dependencies come exclusively from the manifest.
cmake_minimum_required(VERSION 3.24)
# Resolve paths from this script rather than the caller's working directory.
get_filename_component(ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
# Keep setup and run on the same supported development presets.
if(NOT DEFINED DEV_PRESET)
    set(DEV_PRESET debug)
endif()
if(NOT DEV_PRESET MATCHES "^(debug|release)$")
    message(FATAL_ERROR "Choose the debug or release development preset.")
endif()
# Fail early when required tools or generated project metadata are missing.
find_program(GIT_EXECUTABLE git REQUIRED)
find_program(NINJA_EXECUTABLE ninja REQUIRED)
if(NOT EXISTS "${ROOT}/vcpkg.json" OR NOT EXISTS "${ROOT}/CMakePresets.json")
    message(FATAL_ERROR "Missing generated project files. Run scaffold first.")
endif()
set(VCPKG_ROOT "${ROOT}/external/vcpkg")
# Clone current upstream only when absent; history is unnecessary for disposable tooling.
if(NOT EXISTS "${VCPKG_ROOT}")
    file(MAKE_DIRECTORY "${ROOT}/external")
    execute_process(COMMAND "${GIT_EXECUTABLE}" clone --depth 1 https://github.com/microsoft/vcpkg.git "${VCPKG_ROOT}" COMMAND_ERROR_IS_FATAL ANY)
endif()
# Also recover a first setup interrupted between clone and Git metadata removal.
file(REMOVE_RECURSE "${VCPKG_ROOT}/.git")
# Select the host platform's bootstrap script and executable name.
if(CMAKE_HOST_WIN32)
    set(VCPKG "${VCPKG_ROOT}/vcpkg.exe")
    set(BOOTSTRAP "${VCPKG_ROOT}/bootstrap-vcpkg.bat")
else()
    set(VCPKG "${VCPKG_ROOT}/vcpkg")
    set(BOOTSTRAP "${VCPKG_ROOT}/bootstrap-vcpkg.sh")
endif()
# An existing source tree may just need bootstrapping; never delete it on failure.
if(NOT EXISTS "${VCPKG}")
    if(NOT EXISTS "${BOOTSTRAP}")
        message(FATAL_ERROR "Malformed vcpkg tree at ${VCPKG_ROOT}: missing bootstrap script. Remove that directory manually and rerun setup to obtain a fresh copy.")
    endif()
    if(CMAKE_HOST_WIN32)
        execute_process(COMMAND cmd /c call "${BOOTSTRAP}" -disableMetrics WORKING_DIRECTORY "${VCPKG_ROOT}" RESULT_VARIABLE BOOTSTRAP_RESULT)
    else()
        execute_process(COMMAND sh "${BOOTSTRAP}" -disableMetrics WORKING_DIRECTORY "${VCPKG_ROOT}" RESULT_VARIABLE BOOTSTRAP_RESULT)
    endif()
    if(NOT BOOTSTRAP_RESULT EQUAL 0 OR NOT EXISTS "${VCPKG}")
        message(FATAL_ERROR "vcpkg bootstrap failed at ${VCPKG_ROOT}. Check its output; remove the directory manually and rerun setup if a fresh copy is needed.")
    endif()
endif()
# Confirm the reused or newly bootstrapped installation is usable before installing packages.
execute_process(COMMAND "${VCPKG}" version RESULT_VARIABLE VERSION_RESULT)
if(NOT VERSION_RESULT EQUAL 0 OR NOT EXISTS "${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake")
    message(FATAL_ERROR "Malformed vcpkg installation at ${VCPKG_ROOT}. Remove it manually and rerun setup for a fresh copy.")
endif()
# vcpkg's manifest is the sole dependency list. Use the same install root as presets.
set(INSTALL_ARGS install "--x-install-root=${ROOT}/vcpkg_installed")
if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT "$ENV{VCPKG_DEFAULT_TRIPLET}" STREQUAL "")
    list(APPEND INSTALL_ARGS "--triplet=$ENV{VCPKG_DEFAULT_TRIPLET}")
endif()
execute_process(COMMAND "${VCPKG}" ${INSTALL_ARGS} WORKING_DIRECTORY "${ROOT}" COMMAND_ERROR_IS_FATAL ANY)
# Forward the same triplet override to CMake that was used for manifest installation.
# Configure in place without removing previous build output.
set(CONFIGURE_ARGS --preset "${DEV_PRESET}")
if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT "$ENV{VCPKG_DEFAULT_TRIPLET}" STREQUAL "")
    list(APPEND CONFIGURE_ARGS "-DVCPKG_TARGET_TRIPLET=$ENV{VCPKG_DEFAULT_TRIPLET}")
endif()
execute_process(COMMAND "${CMAKE_COMMAND}" ${CONFIGURE_ARGS} WORKING_DIRECTORY "${ROOT}" COMMAND_ERROR_IS_FATAL ANY)
