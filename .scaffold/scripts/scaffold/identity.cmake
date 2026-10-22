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

