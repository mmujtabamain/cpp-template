#!/bin/bash

# * variables

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
RESET='\033[0m' # No Color
readonly GREEN RED YELLOW CYAN PURPLE RESET

# * variables end

set -e

# DO NOT CALL; has been called once; given below for reference only
# git submodule add --depth 1 https://github.com/microsoft/vcpkg.git external/vcpkg

# update submodules
echo -e "${CYAN}Updating git submodules ... ${RESET}"
git submodule update --init --recursive --depth 1

# * platform detect
echo -e "${CYAN}Detecting platform ... ${RESET}"

PLATFORM="unknown"

if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
    echo -e "${GREEN}Detected platform: ${PURPLE}$PLATFORM${RESET}"
    if ! command -v pkg-config &> /dev/null; then
        echo -e "${RED}Error: pkg-config is not installed.${RESET}"
        echo -e "${YELLOW}Please run: brew install pkg-config${RESET}"
        exit 1
    fi
elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || "$OSTYPE" == "win"* ]]; then
    PLATFORM="windows"
    echo -e "${GREEN}Detected platform: ${PURPLE}$PLATFORM${RESET}"
else
    echo -e "${RED}Unsupported OS type: $OSTYPE${RESET}"
    exit 1
fi

# * platform detect end

# bootstrap it to generate ./external/vcpkg/vcpkg or ./external/vcpkg/vcpkg.exe
# if any of above don't exist
if [ ! -f "./external/vcpkg/vcpkg" ] && [ ! -f "./external/vcpkg/vcpkg.exe" ]; then
    echo -e "${YELLOW}Bootstrapping vcpkg ... ${RESET}"
    if [ "$PLATFORM" == "windows" ]; then
        ./external/vcpkg/bootstrap-vcpkg.bat
    elif [ "$PLATFORM" == "macos" ]; then
        ./external/vcpkg/bootstrap-vcpkg.sh
    fi
else
    echo -e "${GREEN}vcpkg already bootstrapped. ${RESET}"
fi

# * utility: add packages in project, setup.sh only
vcpkg-install() {
    if [ -z "$1" ]; then
        echo -e "${RED}Please add package name ... ${RESET}"
        exit 1
    fi

    PACKAGE="$1"
    echo -e "${CYAN}Installing package: $PACKAGE ... ${RESET}"

    if [ "$PLATFORM" == "windows" ]; then
        ./external/vcpkg/vcpkg.exe install "$PACKAGE"
    elif [ "$PLATFORM" == "macos" ]; then
        ./external/vcpkg/vcpkg install "$PACKAGE"
    else
        echo -e "${RED}Unsupported platform for installing package: $PLATFORM${RESET}"
        exit 1
    fi
}
# * utility end

# install packages
echo -e "${CYAN}Installing packages ... ${RESET}"
# > CHANGE: ADD YOUR PACKAGES HERE; vcpkg-install <package_name>
vcpkg-install sfml
echo -e "${CYAN}To install packages run ./external/vcpkg/vcpkg install <package_name>${RESET}"

# clean build directory if exists
if [ -d "build" ]; then
    echo -e "${YELLOW}Cleaning existing build directory...${RESET}"
    rm -rf build
fi

# setup cmake preset; REMOVE after setting up preset
cmake --preset default-configure
echo -e "${PURPLE}In VS Code, open Command Palette and search for 'CMake: Select Build Preset' select 'Default' ${RESET}"
echo -e "${PURPLE}After succesfully setting up preset, syntax highlighting along with other features should be active. You can safely remove the preset section from "setup.sh" ${RESET}"

echo -e "${CYAN}Run ./run.sh for running the program ${RESET}"
