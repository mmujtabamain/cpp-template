cmake_minimum_required(VERSION @PROJECT_CMAKE_VERSION@)

# get PROJECT_ROOT
get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)

# ensure vcpkg installed
if(NOT EXISTS "${PROJECT_ROOT}/external/vcpkg/scripts/buildsystems/vcpkg.cmake"
    OR NOT EXISTS "${PROJECT_ROOT}/vcpkg_installed")
    message(FATAL_ERROR "Development dependencies are not set up. Run setup.sh / setup.bat first.")
endif()

include("${CMAKE_CURRENT_LIST_DIR}/development.cmake")

# get preset; debug or release
resolve_development_preset("${DEV_PRESET}" DEV_PRESET)

configure_development_project("${DEV_PRESET}")
execute_process(
    COMMAND "${CMAKE_COMMAND}" --build "${PROJECT_ROOT}/build/${DEV_PRESET}" --target run
    WORKING_DIRECTORY "${PROJECT_ROOT}" RESULT_VARIABLE BUILD_EXIT_CODE
)
if(NOT BUILD_EXIT_CODE EQUAL 0)
    message(FATAL_ERROR "Build/run failed (${BUILD_EXIT_CODE}).")
endif()
