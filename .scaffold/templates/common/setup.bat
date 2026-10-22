@echo off

setlocal DisableDelayedExpansion

set "development_preset=debug"
set "clean_setup=OFF"
:read_option
if "%~1"=="" goto arguments_done
if "%~1"=="--clean" (
    set "clean_setup=ON"
) else if "%~1"=="debug" (
    set "development_preset=debug"
) else if "%~1"=="release" (
    set "development_preset=release"
) else (
    echo Usage: setup.bat [debug^|release] [--clean] 1>&2
    exit /b 1
)
shift
goto read_option
:arguments_done

rem execute setup.cmake from project root
cmake "-DSETUP_CLEAN=%clean_setup%" "-DDEV_PRESET=%development_preset%" -P "%~dp0scripts\setup.cmake"

rem return the CMake exit status to the calling shell
exit /b %errorlevel%
