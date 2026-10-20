# MARK: Template Hooks
function(clear_template_hooks PROJECT_DIRECTORY)
    # linked worktrees can share configuration outside this destination
    if(NOT IS_DIRECTORY "${PROJECT_DIRECTORY}/.git" OR IS_SYMLINK "${PROJECT_DIRECTORY}/.git")
        return()
    endif()

    find_program(GIT_EXECUTABLE git REQUIRED)
    execute_process(
        COMMAND "${GIT_EXECUTABLE}" -C "${PROJECT_DIRECTORY}" config --local --get core.hooksPath
        OUTPUT_VARIABLE HOOKS_PATH OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET
        RESULT_VARIABLE CONFIG_EXIT_CODE
    )

    # remove only the template's hook setting; preserve custom hook configuration
    if(CONFIG_EXIT_CODE EQUAL 0 AND (HOOKS_PATH STREQUAL ".github/hooks"
                                     OR HOOKS_PATH STREQUAL "${PROJECT_DIRECTORY}/.github/hooks")
    )
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" -C "${PROJECT_DIRECTORY}" config --local --unset-all
                    core.hooksPath COMMAND_ERROR_IS_FATAL ANY
        )
    endif()
endfunction()

# MARK: Git Metadata
function(finish_scaffold_git PROJECT_DIRECTORY REMOVE_GIT GENERATE_GIT)
    set(GIT_METADATA "${PROJECT_DIRECTORY}/.git")
    if(EXISTS "${GIT_METADATA}" OR IS_SYMLINK "${GIT_METADATA}")
        if(REMOVE_GIT STREQUAL "ASK")
            ask_yes_no(
                "Remove ${GIT_METADATA}?\nThis removes this destination's Git metadata and local history. Linked worktree history elsewhere is left alone.\nRemove Git metadata?"
                REMOVE_GIT
            )
        endif()

        # remove a link or worktree pointer itself, never its external target
        if(REMOVE_GIT STREQUAL "ON")
            if(IS_SYMLINK "${GIT_METADATA}" OR NOT IS_DIRECTORY "${GIT_METADATA}")
                file(REMOVE "${GIT_METADATA}")
            else()
                file(REMOVE_RECURSE "${GIT_METADATA}")
            endif()
            message(STATUS "Removed destination Git metadata.")
        else()
            message(STATUS "Kept destination Git metadata.")
        endif()
    endif()

    # print setup commands; do not initialize a repository or change remotes
    if(NOT GENERATE_GIT)
        message(STATUS "Git files disabled. You can initialize Git later if needed.")
    endif()
    message(STATUS "Run Git commands inside: ${PROJECT_DIRECTORY}")
    if(EXISTS "${GIT_METADATA}" OR IS_SYMLINK "${GIT_METADATA}")
        message(STATUS "Existing Git history was kept. Check the remote with: git remote -v")
        message(STATUS "For a different repository: git remote set-url origin <repository-url>")
        message(STATUS "If no origin exists: git remote add origin <repository-url>")
    else()
        message(STATUS "To set up Git: git init -b main")
    endif()
    message(STATUS "If identity is not configured: git config user.name \"Your Name\"")
    message(STATUS "And: git config user.email \"you@example.com\"")
    message(STATUS "Then: git add .")
    message(STATUS "Then: git commit -m \"Initial commit\"")
    if(NOT EXISTS "${GIT_METADATA}")
        message(STATUS "To connect a remote: git remote add origin <repository-url>")
    endif()
endfunction()
