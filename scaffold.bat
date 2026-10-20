@echo off
rem Keep variables local and preserve literal exclamation marks in input.
setlocal DisableDelayedExpansion

if not "%~4"=="" (
    echo Usage: scaffold.bat [project-name] [exec^|library] [--force] 1>&2
    exit /b 1
)

rem * ARGUMENTS START * ----------------------------------------------- %

rem Capture exact user input.
set "project_name=%~1"
if not defined project_name set /p "project_name=Project name: "

rem Capture exact user input.
set "project_type=%~2"
if not defined project_type set /p "project_type=Project type [exec/library]: "

rem Make sure third arg is --force or nothing as third argument.
set "force_replacement=OFF"
if "%~3"=="--force" set "force_replacement=ON"
if not "%~3"=="" if not "%~3"=="--force" exit /b 1

rem * ARGUMENTS END * ------------------------------------------------- %

rem Resolve the CMake script relative to this launcher, not the working directory.
cmake ^
    "-DPROJECT_DISPLAY_NAME=%project_name%" ^
    "-DPROJECT_TYPE=%project_type%" ^
    "-DSCAFFOLD_FORCE=%force_replacement%" ^
    -P "%~dp0.template\scripts\scaffold.cmake"

rem Return the CMake exit status to the calling shell.
exit /b %errorlevel%
