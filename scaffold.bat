@echo off
setlocal DisableDelayedExpansion
set "project_name=%~1"
set "project_type=%~2"
if not defined project_name set /p "project_name=Project name: "
if not defined project_type set /p "project_type=Project type [exec/library]: "
set "force=OFF"
if "%~3"=="--force" set "force=ON"
if not "%~3"=="" if not "%~3"=="--force" exit /b 1
cmake "-DPROJECT_DISPLAY_NAME=%project_name%" "-DPROJECT_TYPE=%project_type%" "-DSCAFFOLD_FORCE=%force%" -P "%~dp0.template\scripts\scaffold.cmake"
exit /b %errorlevel%
