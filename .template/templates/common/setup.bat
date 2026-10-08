@echo off
setlocal DisableDelayedExpansion
set "preset=%~1"
if not defined preset set "preset=debug"
cmake "-DDEV_PRESET=%preset%" -P "%~dp0scripts\setup.cmake"
exit /b %errorlevel%
