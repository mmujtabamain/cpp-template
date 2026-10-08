@echo off
rem Prepare dependencies and configure the development environment; implementation lives in scripts/setup.cmake.
rem Keep launcher variables local and disable expansion of exclamation marks.
setlocal DisableDelayedExpansion
rem The optional first argument selects a preset; debug is the default.
set "preset=%~1"
if not defined preset set "preset=debug"
rem Resolve the script relative to this launcher so any working directory works.
cmake "-DDEV_PRESET=%preset%" -P "%~dp0scripts\setup.cmake"
rem Return the CMake exit status to the calling shell.
exit /b %errorlevel%
