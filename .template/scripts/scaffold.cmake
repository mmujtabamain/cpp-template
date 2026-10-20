# Shared one-time generator for the shell and Batch launchers.
# Render and validate in staging before allowing destructive replacement.

# MARK: Paths and input validation

cmake_minimum_required(VERSION 3.24)
get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
set(TEMPLATE_DIRECTORY "${PROJECT_ROOT}/.template/templates")
set(STAGING_DIRECTORY "${PROJECT_ROOT}/.template/.scaffold-tmp")

# Validate every input before touching generated output or the previous staging tree.
if(NOT DEFINED PROJECT_DISPLAY_NAME OR NOT DEFINED PROJECT_TYPE)
    message(FATAL_ERROR "Supply PROJECT_DISPLAY_NAME and PROJECT_TYPE (exec or library).")
endif()
string(STRIP "${PROJECT_DISPLAY_NAME}" PROJECT_DISPLAY_NAME)
if(NOT PROJECT_DISPLAY_NAME MATCHES "^[A-Za-z][A-Za-z0-9 _-]*$")
    message(
        FATAL_ERROR
            "Project name must start with a letter and contain only ASCII letters, digits, spaces, underscores or hyphens."
    )
endif()
string(TOLOWER "${PROJECT_TYPE}" PROJECT_TYPE)
if(NOT PROJECT_TYPE STREQUAL "exec" AND NOT PROJECT_TYPE STREQUAL "library")
    message(FATAL_ERROR "Project type must be exec or library.")
endif()

# MARK: Project identity normalization

# Split words at separators and CamelCase/acronym boundaries.
string(REGEX REPLACE "([A-Z]+)([A-Z][a-z])" "\\1_\\2" PROJECT_NAME_WORDS "${PROJECT_DISPLAY_NAME}")
string(REGEX REPLACE "([a-z0-9])([A-Z])" "\\1_\\2" PROJECT_NAME_WORDS "${PROJECT_NAME_WORDS}")
string(REGEX REPLACE "[ _-]+" ";" PROJECT_NAME_WORDS "${PROJECT_NAME_WORDS}")

# Preserve this placeholder for the generated library's later CMake configure step.
set(PACKAGE_INIT "@PACKAGE_INIT@")
set(PROJECT_NAME "")
set(PROJECT_NAMESPACE "")
foreach(PROJECT_NAME_WORD IN LISTS PROJECT_NAME_WORDS)
    if(PROJECT_NAME_WORD STREQUAL "")
        continue()
    endif()
    string(SUBSTRING "${PROJECT_NAME_WORD}" 0 1 FIRST_CHARACTER)
    string(TOUPPER "${FIRST_CHARACTER}" FIRST_CHARACTER)
    string(SUBSTRING "${PROJECT_NAME_WORD}" 1 -1 REMAINING_CHARACTERS)
    string(APPEND PROJECT_NAME "${FIRST_CHARACTER}${REMAINING_CHARACTERS}")
    string(TOLOWER "${PROJECT_NAME_WORD}" PROJECT_NAME_WORD)
    if(NOT PROJECT_NAMESPACE STREQUAL "")
        string(APPEND PROJECT_NAMESPACE "_")
    endif()
    string(APPEND PROJECT_NAMESPACE "${PROJECT_NAME_WORD}")
endforeach()
# MARK: Reserved identifiers

set(CPP_KEYWORDS
    alignas
    alignof
    and
    and_eq
    asm
    auto
    bitand
    bitor
    bool
    break
    case
    catch
    char
    char8_t
    char16_t
    char32_t
    class
    compl
    concept
    const
    consteval
    constexpr
    constinit
    const_cast
    continue
    co_await
    co_return
    co_yield
    decltype
    default
    delete
    do
    double
    dynamic_cast
    else
    enum
    explicit
    export
    extern
    false
    float
    for
    friend
    goto
    if
    inline
    int
    long
    mutable
    namespace
    new
    noexcept
    not
    not_eq
    nullptr
    operator
    or
    or_eq
    private
    protected
    public
    register
    reinterpret_cast
    requires
    return
    short
    signed
    sizeof
    static
    static_assert
    static_cast
    struct
    switch
    template
    this
    thread_local
    throw
    true
    try
    typedef
    typeid
    typename
    union
    unsigned
    using
    virtual
    void
    volatile
    wchar_t
    while
    xor
    xor_eq
)
set(RESERVED_TARGETS
    all
    clean
    help
    install
    test
    package
    run
)
if(PROJECT_NAMESPACE IN_LIST CPP_KEYWORDS
   OR PROJECT_NAMESPACE MATCHES "^_[A-Za-z_]"
   OR PROJECT_NAME IN_LIST RESERVED_TARGETS
   OR PROJECT_NAME STREQUAL "Run"
)
    message(
        FATAL_ERROR
            "Project name normalizes to a reserved C++ or build identifier. Choose another name."
    )
endif()
string(TOUPPER "${PROJECT_NAMESPACE}" PROJECT_MACRO)
string(REPLACE "_" "-" PROJECT_MANIFEST_NAME "${PROJECT_NAMESPACE}")

# MARK: Template rendering

# Discard interrupted staging output; existing project files remain untouched here.
file(REMOVE_RECURSE "${STAGING_DIRECTORY}")
file(MAKE_DIRECTORY "${STAGING_DIRECTORY}")

# Render common development tools, then the selected project type.
foreach(TEMPLATE_KIND common "${PROJECT_TYPE}")
    if(TEMPLATE_KIND STREQUAL "exec")
        set(TEMPLATE_KIND executable)
    endif()
    file(
        GLOB_RECURSE TEMPLATE_INPUT_PATHS
        LIST_DIRECTORIES false
        RELATIVE "${TEMPLATE_DIRECTORY}/${TEMPLATE_KIND}"
        "${TEMPLATE_DIRECTORY}/${TEMPLATE_KIND}/*"
    )
    foreach(TEMPLATE_INPUT_PATH IN LISTS TEMPLATE_INPUT_PATHS)
        set(GENERATED_RELATIVE_PATH "${TEMPLATE_INPUT_PATH}")
        # Replace generic library paths with the normalized package and namespace names.
        if(TEMPLATE_KIND STREQUAL "library")
            string(REPLACE "include/project/project.hpp"
                           "include/${PROJECT_NAMESPACE}/${PROJECT_NAMESPACE}.hpp"
                           GENERATED_RELATIVE_PATH "${GENERATED_RELATIVE_PATH}"
            )
            string(REPLACE "src/project.cpp" "src/${PROJECT_NAMESPACE}.cpp" GENERATED_RELATIVE_PATH
                           "${GENERATED_RELATIVE_PATH}"
            )
            string(REPLACE "tests/project_test.cpp" "tests/${PROJECT_NAMESPACE}_test.cpp"
                           GENERATED_RELATIVE_PATH "${GENERATED_RELATIVE_PATH}"
            )
            string(REPLACE "cmake/ProjectConfig.cmake.in" "cmake/${PROJECT_NAME}Config.cmake.in"
                           GENERATED_RELATIVE_PATH "${GENERATED_RELATIVE_PATH}"
            )
        endif()
        # The package config remains a CMake input template after scaffolding.
        if(NOT GENERATED_RELATIVE_PATH MATCHES "Config\\.cmake\\.in$")
            string(REGEX REPLACE "\\.in$" "" GENERATED_RELATIVE_PATH "${GENERATED_RELATIVE_PATH}")
        endif()
        configure_file(
            "${TEMPLATE_DIRECTORY}/${TEMPLATE_KIND}/${TEMPLATE_INPUT_PATH}"
            "${STAGING_DIRECTORY}/${GENERATED_RELATIVE_PATH}" @ONLY
        )
    endforeach()
endforeach()
if(PROJECT_TYPE STREQUAL "exec")
    file(MAKE_DIRECTORY "${STAGING_DIRECTORY}/assets")
endif()
if(PROJECT_TYPE STREQUAL "exec")
    set(TYPE_REQUIRED_PATHS src/main.cpp)
else()
    set(TYPE_REQUIRED_PATHS
        "include/${PROJECT_NAMESPACE}/${PROJECT_NAMESPACE}.hpp" "src/${PROJECT_NAMESPACE}.cpp"
        examples/main.cpp "tests/${PROJECT_NAMESPACE}_test.cpp"
        "cmake/${PROJECT_NAME}Config.cmake.in"
    )
endif()

# MARK: Staged project validation

# Check required files and JSON before asking to replace the existing project.
foreach(
    REQUIRED_PATH
    ${TYPE_REQUIRED_PATHS}
    CMakeLists.txt
    CMakePresets.json
    vcpkg.json
    README.md
    scripts/setup.cmake
    scripts/run.cmake
    scripts/development.cmake
    setup.sh
    setup.bat
    run.sh
    run.bat
)
    if(NOT EXISTS "${STAGING_DIRECTORY}/${REQUIRED_PATH}")
        message(
            FATAL_ERROR
                "Incomplete staged project: missing ${REQUIRED_PATH}. Existing project is untouched."
        )
    endif()
endforeach()
foreach(JSON_FILENAME CMakePresets.json vcpkg.json)
    file(READ "${STAGING_DIRECTORY}/${JSON_FILENAME}" JSON_CONTENT)
    string(JSON JSON_VALUE_TYPE ERROR_VARIABLE JSON_ERROR TYPE "${JSON_CONTENT}")
    if(NOT JSON_ERROR STREQUAL "NOTFOUND" OR NOT JSON_VALUE_TYPE STREQUAL "OBJECT")
        message(
            FATAL_ERROR
                "Invalid staged ${JSON_FILENAME}: ${JSON_ERROR}. Existing project is untouched."
        )
    endif()
endforeach()

# Generated Unix launchers must be executable immediately after scaffolding.
file(
    CHMOD
    "${STAGING_DIRECTORY}/setup.sh"
    "${STAGING_DIRECTORY}/run.sh"
    PERMISSIONS
    OWNER_READ
    OWNER_WRITE
    OWNER_EXECUTE
    GROUP_READ
    GROUP_EXECUTE
    WORLD_READ
    WORLD_EXECUTE
)

# MARK: Generated project detection

# Only these reserved paths may be replaced; Git, tooling, and unrelated files survive.
set(GENERATED_PATHS
    CMakeLists.txt
    CMakePresets.json
    vcpkg.json
    README.md
    src
    include
    assets
    examples
    tests
    cmake
    scripts
    setup.sh
    setup.bat
    run.sh
    run.bat
    build
    vcpkg_installed
    .github/workflows/validate.yml
)
set(HAS_GENERATED_PROJECT false)
foreach(GENERATED_PATH IN LISTS GENERATED_PATHS)
    # The template's README and validation workflow also exist before scaffolding.
    if(NOT GENERATED_PATH STREQUAL "README.md"
       AND NOT GENERATED_PATH STREQUAL ".github/workflows/validate.yml"
       AND (EXISTS "${PROJECT_ROOT}/${GENERATED_PATH}" OR IS_SYMLINK
                                                          "${PROJECT_ROOT}/${GENERATED_PATH}")
    )
        set(HAS_GENERATED_PROJECT true)
    endif()
endforeach()

# MARK: Destructive replacement confirmation

# Ask only after a replacement is ready. EOF and any answer other than yes cancel.
if(HAS_GENERATED_PROJECT AND NOT SCAFFOLD_FORCE)
    message(
        "An existing scaffolded project was detected.\n\nRe-scaffolding will permanently erase the existing generated project,\nincluding source files and changes made after scaffolding.\n\nContinue? [y/N]"
    )
    if(CMAKE_HOST_WIN32)
        execute_process(
            COMMAND powershell -NoProfile -Command "[Console]::ReadLine()"
            OUTPUT_VARIABLE REPLACEMENT_ANSWER RESULT_VARIABLE PROMPT_EXIT_CODE
        )
    else()
        execute_process(
            COMMAND sh -c "IFS= read -r answer; printf '%s' \"$answer\""
            OUTPUT_VARIABLE REPLACEMENT_ANSWER RESULT_VARIABLE PROMPT_EXIT_CODE
        )
    endif()
    string(STRIP "${REPLACEMENT_ANSWER}" REPLACEMENT_ANSWER)
    string(TOLOWER "${REPLACEMENT_ANSWER}" REPLACEMENT_ANSWER)
    if(NOT PROMPT_EXIT_CODE EQUAL 0 OR NOT REPLACEMENT_ANSWER MATCHES "^(y|yes)$")
        file(REMOVE_RECURSE "${STAGING_DIRECTORY}")
        message("Scaffolding cancelled. Existing project is unchanged.")
        return()
    endif()
endif()

# MARK: Replacement and completion

# Only a fully rendered replacement reaches this destructive commit step.
foreach(GENERATED_PATH IN LISTS GENERATED_PATHS)
    file(REMOVE_RECURSE "${PROJECT_ROOT}/${GENERATED_PATH}")
endforeach()

# Move individual files to preserve unrelated content in shared directories such as .github.
file(
    GLOB_RECURSE GENERATED_RELATIVE_PATHS
    LIST_DIRECTORIES true
    RELATIVE "${STAGING_DIRECTORY}"
    "${STAGING_DIRECTORY}/*"
)
foreach(GENERATED_RELATIVE_PATH IN LISTS GENERATED_RELATIVE_PATHS)
    if(IS_DIRECTORY "${STAGING_DIRECTORY}/${GENERATED_RELATIVE_PATH}")
        file(MAKE_DIRECTORY "${PROJECT_ROOT}/${GENERATED_RELATIVE_PATH}")
    else()
        get_filename_component(
            OUTPUT_PARENT_DIRECTORY "${PROJECT_ROOT}/${GENERATED_RELATIVE_PATH}" DIRECTORY
        )
        file(MAKE_DIRECTORY "${OUTPUT_PARENT_DIRECTORY}")
        file(RENAME "${STAGING_DIRECTORY}/${GENERATED_RELATIVE_PATH}"
             "${PROJECT_ROOT}/${GENERATED_RELATIVE_PATH}"
        )
    endif()
endforeach()
file(REMOVE_RECURSE "${STAGING_DIRECTORY}")
message(
    STATUS
        "Generated ${PROJECT_TYPE}: ${PROJECT_DISPLAY_NAME} (${PROJECT_NAME}, ${PROJECT_NAMESPACE}, ${PROJECT_MANIFEST_NAME})"
)
message(STATUS "Next: setup.sh / setup.bat, then run.sh / run.bat")
