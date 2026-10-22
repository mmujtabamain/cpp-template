# Shared generator; scaffold validation lives in .github/validate.py.
# Validate input, render and check staging, then confirm and replace output.
cmake_minimum_required(VERSION 3.24)
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/prompt.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/inputs.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/identity.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/render.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/verify-output.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/scaffold/replace.cmake")
