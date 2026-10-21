@echo off
rem Keep variables local and preserve literal exclamation marks in input.
setlocal DisableDelayedExpansion

if "%~1"=="" (
    echo Usage: scaffold.bat ^<location^> [project-name] [exec^|library] [--force] [--no-git] 1>&2
    exit /b 1
)

rem * ARGUMENTS START * ----------------------------------------------- %

rem Capture the destination and exact user input.
set "scaffold_destination=%~1"
shift
set "project_name=%~1"
shift
set "project_type=%~1"
shift

rem Optionally omit template Git files.
set "force_replacement=OFF"
set "generate_git=ON"

:read_option
if "%~1"=="" goto arguments_done
if "%~1"=="--force" (
    set "force_replacement=ON"
) else if "%~1"=="--no-git" (
    set "generate_git=OFF"
) else (
    echo Unknown scaffold option: %~1 1>&2
    exit /b 1
)
shift
goto read_option

:arguments_done
if not defined project_name set /p "project_name=Project name: "
if not defined project_type set /p "project_type=Project type [exec/library]: "

rem * ARGUMENTS END * ------------------------------------------------- %

rem Resolve the CMake script relative to this launcher.
cmake ^
    "-DSCAFFOLD_DESTINATION=%scaffold_destination%" ^
    "-DPROJECT_DISPLAY_NAME=%project_name%" ^
    "-DPROJECT_TYPE=%project_type%" ^
    "-DSCAFFOLD_FORCE=%force_replacement%" ^
    "-DSCAFFOLD_GIT=%generate_git%" ^
    -P "%~dp0scripts\scaffold.cmake"

exit /b %errorlevel%
