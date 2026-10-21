@echo off

setlocal DisableDelayedExpansion

rem optional first argument for preset; default debug
set "development_preset=%~1"
if not defined development_preset set "development_preset=debug"

rem execute setup.cmake from project root
cmake "-DDEV_PRESET=%development_preset%" -P "%~dp0scripts\setup.cmake"

rem return the CMake exit status to the calling shell
exit /b %errorlevel%
