@echo off
setlocal enabledelayedexpansion

:: colors
set "GREEN="
set "RED="
set "YELLOW="
set "CYAN="
set "PURPLE="
set "RESET="

for /f "tokens=1,2 delims==" %%a in ('"prompt $H & for %%b in (1) do rem"') do set "BS=%%b"

:: Helper to print colors (Windows 10+ supports ANSI)
for /f "tokens=2 delims==" %%I in ('"echo prompt $E ^| cmd"') do set "ESC=%%I"
set "GREEN=%ESC%[0;32m"
set "RED=%ESC%[0;31m"
set "YELLOW=%ESC%[1;33m"
set "CYAN=%ESC%[0;36m"
set "PURPLE=%ESC%[0;35m"
set "RESET=%ESC%[0m"

:: update submodules
echo %CYAN%Updating git submodules ... %RESET%
git submodule update --init --recursive --depth 1

echo %CYAN%Assuming Platform is Windows ... %RESET%

:: bootstrap it to generate ./external/vcpkg/vcpkg.exe
:: if vcpkg.exe doesn't exist
if not exist "external\vcpkg\vcpkg.exe" (
    echo %YELLOW%Bootstrapping vcpkg ... %RESET%
    call external\vcpkg\bootstrap-vcpkg.bat
) else (
    echo %GREEN%vcpkg already bootstrapped.%RESET%
)

:: install packages
echo %CYAN%Installing packages ... %RESET%
external\vcpkg\vcpkg.exe install sfml
:: CHANGE: ADD YOUR PACKAGES HERE; vcpkg-install <package_name>
echo %CYAN%To install packages run:%RESET%
echo %PURPLE%external\vcpkg\vcpkg.exe install ^<package_name^>%RESET%

:: setup cmake preset; REMOVE after setting up preset
cmake --preset default-configure

echo %PURPLE%In VS Code, open Command Palette and select 'CMake: Select Build Preset' → 'Default'%RESET%
echo %PURPLE%After successful setup, syntax highlighting and other features will activate.%RESET%

echo %CYAN%Run run.bat to build and run the program.%RESET%
echo %GREEN%Setup complete!%RESET%

endlocal
pause
