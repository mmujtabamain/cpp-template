# Shared development shortcut: configure, then build CMake's run target.
# Dependency acquisition and installation remain setup responsibilities.

# MARK: Project paths and development preset

cmake_minimum_required(VERSION 3.24)

# Resolve the project independently of the caller's working directory.
get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)

# Default to debug and reject unsupported preset names before invoking CMake.
include("${CMAKE_CURRENT_LIST_DIR}/development.cmake")
resolve_development_preset("${DEV_PRESET}" DEV_PRESET)

# MARK: Dependency preflight

# Require prior setup instead of cloning or installing dependencies here.
if(NOT EXISTS "${PROJECT_ROOT}/external/vcpkg/scripts/buildsystems/vcpkg.cmake"
   OR NOT EXISTS "${PROJECT_ROOT}/vcpkg_installed"
)
    message(FATAL_ERROR "Development dependencies are not set up. Run setup.sh / setup.bat first.")
endif()

# MARK: Configure and run

# Match setup's explicit triplet override so both commands use the same dependencies.
make_development_configure_arguments("${DEV_PRESET}" CONFIGURE_ARGUMENTS)

# Reconfigure to pick up source and CMake changes; propagate command failures.
execute_process(
    COMMAND "${CMAKE_COMMAND}" ${CONFIGURE_ARGUMENTS} WORKING_DIRECTORY "${PROJECT_ROOT}"
    COMMAND_ERROR_IS_FATAL ANY
)

# CMake selects the application/example path, configuration directory, and executable suffix.
execute_process(
    COMMAND "${CMAKE_COMMAND}" --build --preset "${DEV_PRESET}" --target run
    WORKING_DIRECTORY "${PROJECT_ROOT}" COMMAND_ERROR_IS_FATAL ANY
)
