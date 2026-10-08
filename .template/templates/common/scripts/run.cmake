# Shared development shortcut: configure, then build CMake's run target.
# Dependency acquisition and installation remain setup responsibilities.
cmake_minimum_required(VERSION 3.24)
# Resolve the project independently of the caller's working directory.
get_filename_component(ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
# Default to debug and reject unsupported preset names before invoking CMake.
if(NOT DEFINED DEV_PRESET)
    set(DEV_PRESET debug)
endif()
if(NOT DEV_PRESET MATCHES "^(debug|release)$")
    message(FATAL_ERROR "Choose the debug or release development preset.")
endif()
# Require prior setup instead of cloning or installing dependencies here.
if(NOT EXISTS "${ROOT}/external/vcpkg/scripts/buildsystems/vcpkg.cmake" OR NOT EXISTS "${ROOT}/vcpkg_installed")
    message(FATAL_ERROR "Development dependencies are not set up. Run setup.sh / setup.bat first.")
endif()
# Match setup's explicit triplet override so both commands use the same dependencies.
set(CONFIGURE_ARGS --preset "${DEV_PRESET}")
if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT "$ENV{VCPKG_DEFAULT_TRIPLET}" STREQUAL "")
    list(APPEND CONFIGURE_ARGS "-DVCPKG_TARGET_TRIPLET=$ENV{VCPKG_DEFAULT_TRIPLET}")
endif()
# Reconfigure to pick up source and CMake changes; propagate command failures.
execute_process(COMMAND "${CMAKE_COMMAND}" ${CONFIGURE_ARGS} WORKING_DIRECTORY "${ROOT}" COMMAND_ERROR_IS_FATAL ANY)
# CMake selects the application/example path, configuration directory, and executable suffix.
execute_process(COMMAND "${CMAKE_COMMAND}" --build --preset "${DEV_PRESET}" --target run WORKING_DIRECTORY "${ROOT}" COMMAND_ERROR_IS_FATAL ANY)
