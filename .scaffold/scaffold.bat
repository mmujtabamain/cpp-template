@echo off

setlocal DisableDelayedExpansion

if "%~1"=="" (
    echo Usage: scaffold.bat ^<location^> [project-name] [exec^|library] [--force] [--no-git] [--cmake-version VERSION] [--cpp-version STANDARD] 1>&2
    exit /b 1
)

rem * ARGUMENTS START * ----------------------------------------------- %

rem get destination
set "scaffold_destination=%~1"
shift

rem get project name
set "project_name=%~1"
shift

rem get project type
set "project_type=%~1"
shift

rem get --force and --no-git flags
set "force_replacement=OFF"
set "generate_git=ON"
set "project_cmake_version="
set "project_cpp_version="

rem = loop over all arguments
:read_option

rem - end loop if all arguments passed
if "%~1"=="" goto arguments_done

if "%~1"=="--force" (
    set "force_replacement=ON"
) else if "%~1"=="--no-git" (
    set "generate_git=OFF"
) else if "%~1"=="--cpp-version" (
    if "%~2"=="" (
        echo --cpp-version requires a standard 1>&2
        exit /b 1
    )
    set "project_cpp_version=%~2"
    shift
) else if "%~1"=="--cmake-version" (
    if "%~2"=="" (
        echo --cmake-version requires a version 1>&2
        exit /b 1
    )
    set "project_cmake_version=%~2"
    shift
) else (
    echo Unknown scaffold option: %~1 1>&2
    exit /b 1
)
shift

rem + read next argument
goto read_option

rem if not in args; then prompt user
:arguments_done
if not defined project_name set /p "project_name=Project name: "
if not defined project_type set /p "project_type=Project type [exec|library]: "

rem * ARGUMENTS END * ------------------------------------------------- %

rem Resolve the CMake script relative to this launcher.
cmake ^
    "-DSCAFFOLD_DESTINATION=%scaffold_destination%" ^
    "-DPROJECT_DISPLAY_NAME=%project_name%" ^
    "-DPROJECT_TYPE=%project_type%" ^
    "-DSCAFFOLD_FORCE=%force_replacement%" ^
    "-DSCAFFOLD_GIT=%generate_git%" ^
    "-DPROJECT_CMAKE_VERSION=%project_cmake_version%" ^
    "-DPROJECT_CPP_VERSION=%project_cpp_version%" ^
    -P "%~dp0scripts\scaffold.cmake"

exit /b %errorlevel%
