cmake_minimum_required(VERSION 3.24)

# ensure vcpkg installed
if(NOT EXISTS "${PROJECT_ROOT}/external/vcpkg/scripts/buildsystems/vcpkg.cmake"
    OR NOT EXISTS "${PROJECT_ROOT}/vcpkg_installed")
    message(FATAL_ERROR "Development dependencies are not set up. Run setup.sh / setup.bat first.")
endif()

# get PROJECT_ROOT
get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)

include("${CMAKE_CURRENT_LIST_DIR}/development.cmake")

# get preset; debug or release
resolve_development_preset("${DEV_PRESET}" DEV_PRESET)

# get arguments; -DVCPKG_TARGET_TRIPLET etc.
make_development_configure_arguments("${DEV_PRESET}" CONFIGURE_ARGUMENTS)

execute_process(
    COMMAND "${CMAKE_COMMAND}" ${CONFIGURE_ARGUMENTS} WORKING_DIRECTORY "${PROJECT_ROOT}"
    COMMAND_ERROR_IS_FATAL ANY
) # set working directory
execute_process(
    COMMAND "${CMAKE_COMMAND}" --build --preset "${DEV_PRESET}" --target run
    WORKING_DIRECTORY "${PROJECT_ROOT}" COMMAND_ERROR_IS_FATAL ANY
) # builds and runs the project
