# Shared generator; scaffold validation lives in .github/validate.py.
# Validate input, render and check staging, then confirm and replace output.
cmake_minimum_required(VERSION 3.24)
include("${CMAKE_CURRENT_LIST_DIR}/prompt.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/inputs.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/identity.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/render.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/verify-output.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/replace.cmake")
