@echo off
setlocal DisableDelayedExpansion

rem Use the repository root even when called from another directory.
call "%~dp0.scaffold\scaffold.bat" "%~dp0." %*
exit /b %errorlevel%
