# Repeatable machine setup shared by the shell and Batch launchers.
# Reuse local tooling and build output; dependencies come exclusively from the manifest.

# MARK: Project paths and development preset

cmake_minimum_required(VERSION 3.24)

# get PROJECT_ROOT
get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)

# Explicit recovery only: ordinary setup always reuses local dependencies.
# Also allow: cmake -P scripts/setup.cmake --clean
foreach(ARGUMENT_INDEX RANGE 0 ${CMAKE_ARGC})
    if("${CMAKE_ARGV${ARGUMENT_INDEX}}" STREQUAL "--clean")
        set(SETUP_CLEAN ON)
    endif()
endforeach()
set(VCPKG_ROOT "${PROJECT_ROOT}/external/vcpkg")
if(SETUP_CLEAN)
    message(WARNING "Clean setup deletes external/vcpkg, vcpkg_installed, and build, including local changes in those directories.")
    foreach(CLEAN_PATH "${VCPKG_ROOT}" "${PROJECT_ROOT}/vcpkg_installed" "${PROJECT_ROOT}/build")
        if(IS_SYMLINK "${CLEAN_PATH}")
            file(REMOVE "${CLEAN_PATH}")
        else()
            file(REMOVE_RECURSE "${CLEAN_PATH}")
        endif()
    endforeach()
endif()
set(SETUP_RECOVERY "Run setup.sh --clean (Windows: setup.bat --clean) to clone and set up again. Warning: this deletes external/vcpkg, vcpkg_installed, and build, including local changes.")

# MARK: Prerequisites

# Fail early when required tools or generated project metadata are missing.
find_program(GIT_EXECUTABLE git REQUIRED)
find_program(NINJA_EXECUTABLE ninja REQUIRED)

if(NOT EXISTS "${PROJECT_ROOT}/vcpkg.json" OR NOT EXISTS "${PROJECT_ROOT}/CMakePresets.json")
    message(FATAL_ERROR "Missing generated project files. Run scaffold first.")
endif()

include("${CMAKE_CURRENT_LIST_DIR}/development.cmake")

# get preset; debug or release
resolve_development_preset("${DEV_PRESET}" DEV_PRESET)

# MARK: Setup "vcpkg"

# CLONE
if(NOT EXISTS "${VCPKG_ROOT}")
    file(MAKE_DIRECTORY "${PROJECT_ROOT}/external")
    execute_process(
        COMMAND "${GIT_EXECUTABLE}" clone --depth 1 https://github.com/microsoft/vcpkg.git
        "${VCPKG_ROOT}" RESULT_VARIABLE CLONE_EXIT_CODE
    )

    if(NOT CLONE_EXIT_CODE EQUAL 0)
        message(FATAL_ERROR "vcpkg clone failed. ${SETUP_RECOVERY}")
    endif()
    # Preserve .git: vcpkg uses Git for versioning and registry operations.
    # Repository metadata cleanup belongs to the user; --clean replaces the whole dependency.
endif()

# BOOTSTRAP
if(CMAKE_HOST_WIN32)
    set(VCPKG_EXECUTABLE "${VCPKG_ROOT}/vcpkg.exe")
    set(VCPKG_BOOTSTRAP_SCRIPT "${VCPKG_ROOT}/bootstrap-vcpkg.bat")
else()
    set(VCPKG_EXECUTABLE "${VCPKG_ROOT}/vcpkg")
    set(VCPKG_BOOTSTRAP_SCRIPT "${VCPKG_ROOT}/bootstrap-vcpkg.sh")
endif()

if(NOT EXISTS "${VCPKG_EXECUTABLE}")
    # corrupted clone; no bootstrap script exists
    if(NOT EXISTS "${VCPKG_BOOTSTRAP_SCRIPT}")
        message(
            FATAL_ERROR
            "Malformed vcpkg tree at ${VCPKG_ROOT}: missing bootstrap script. ${SETUP_RECOVERY}"
        )
    endif()

    # bootstrap on windows
    if(CMAKE_HOST_WIN32)
        execute_process(
            COMMAND cmd /c call "${VCPKG_BOOTSTRAP_SCRIPT}" -disableMetrics
            WORKING_DIRECTORY "${VCPKG_ROOT}" RESULT_VARIABLE BOOTSTRAP_EXIT_CODE
        )
    else() # bash bootstrap
        execute_process(
            COMMAND sh "${VCPKG_BOOTSTRAP_SCRIPT}" -disableMetrics WORKING_DIRECTORY "${VCPKG_ROOT}"
            RESULT_VARIABLE BOOTSTRAP_EXIT_CODE
        )
    endif()

    # bootstrap failed
    if(NOT BOOTSTRAP_EXIT_CODE EQUAL 0 OR NOT EXISTS "${VCPKG_EXECUTABLE}")
        message(
            FATAL_ERROR
            "vcpkg bootstrap failed at ${VCPKG_ROOT}. Check its output. ${SETUP_RECOVERY}"
        )
    endif()
endif()

# TEST
execute_process(COMMAND "${VCPKG_EXECUTABLE}" version RESULT_VARIABLE VCPKG_VERSION_EXIT_CODE)

# check if TEST success or fail
if(NOT VCPKG_VERSION_EXIT_CODE EQUAL 0 OR NOT EXISTS
    "${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
)
    message(
        FATAL_ERROR
        "Malformed vcpkg installation at ${VCPKG_ROOT}. ${SETUP_RECOVERY}"
    )
endif()

# MARK: Install Packages

# set install arguments
set(VCPKG_INSTALL_ARGUMENTS install "--x-install-root=${PROJECT_ROOT}/vcpkg_installed")

# add triplet if not in args
if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT "$ENV{VCPKG_DEFAULT_TRIPLET}" STREQUAL "")
    list(APPEND VCPKG_INSTALL_ARGUMENTS "--triplet=$ENV{VCPKG_DEFAULT_TRIPLET}")
endif()

# INSTALL PACKAGES
execute_process(
    COMMAND "${VCPKG_EXECUTABLE}" ${VCPKG_INSTALL_ARGUMENTS} WORKING_DIRECTORY "${PROJECT_ROOT}"
    RESULT_VARIABLE INSTALL_EXIT_CODE
)
if(NOT INSTALL_EXIT_CODE EQUAL 0)
    message(FATAL_ERROR "vcpkg installation failed. ${SETUP_RECOVERY}")
endif()

# MARK: Configure CMake

# make configure args; -DVCPKG_TARGET_TRIPLET etc.
make_development_configure_arguments("${DEV_PRESET}" CONFIGURE_ARGUMENTS)
execute_process(
    COMMAND "${CMAKE_COMMAND}" ${CONFIGURE_ARGUMENTS} WORKING_DIRECTORY "${PROJECT_ROOT}"
    COMMAND_ERROR_IS_FATAL ANY
) # configure cmake project
