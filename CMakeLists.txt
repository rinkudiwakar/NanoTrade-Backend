cmake_minimum_required(VERSION 3.10)

project(NanoTrade)

set(CMAKE_CXX_STANDARD 17)

# Production and toolchain options
option(PRODUCTION_BUILD "Enable production compiler/linker flags optimised for low latency" ON)
option(ENABLE_SANITIZERS "Enable Address/Undefined sanitizers for Debug builds" OFF)

if (PRODUCTION_BUILD)
	message(STATUS "Configuring production compiler flags")
	if (MSVC)
		# MSVC options
		add_compile_options($<$<CONFIG:Release>:/O2>)
		add_compile_options(/W4)
	else()
		# GCC/Clang options
		add_compile_options($<$<CONFIG:Release>:-O3>)
		add_compile_options($<$<CONFIG:Release>:-march=native>)
		add_compile_options($<$<CONFIG:Release>:-funroll-loops>)
		# Warnings
		add_compile_options(-Wall -Wextra -Wpedantic)
	endif()
endif()

if (ENABLE_SANITIZERS)
	add_compile_options($<$<CONFIG:Debug>:-fsanitize=address,undefined>)
	add_link_options($<$<CONFIG:Debug>:-fsanitize=address,undefined>)
endif()

# Engine module
file(GLOB ENGINE_SRC CONFIGURE_DEPENDS "src/engine/*.cpp")
add_library(engine ${ENGINE_SRC})

# Models module
file(GLOB MODELS_SRC CONFIGURE_DEPENDS "src/models/*.cpp")
add_library(models ${MODELS_SRC})

# Utils module
file(GLOB UTILS_SRC CONFIGURE_DEPENDS "src/utils/*.cpp")
add_library(utils ${UTILS_SRC})

# Main executable
add_executable(NanoTrade src/main_new.cpp)

# Test harness executable for integration testing
add_executable(TestHarness src/test_harness.cpp)

# Include directories
target_include_directories(engine PUBLIC include)
target_include_directories(models PUBLIC include)
target_include_directories(utils PUBLIC include)

# Link modules
find_package(nlohmann_json 3.2.0 QUIET)
if (NOT nlohmann_json_FOUND)
	include(FetchContent)
	FetchContent_Declare(
		nlohmann_json
		GIT_REPOSITORY https://github.com/nlohmann/json.git
		GIT_TAG v3.11.2
	)
	FetchContent_MakeAvailable(nlohmann_json)
endif()

target_link_libraries(engine PUBLIC nlohmann_json::nlohmann_json)
target_link_libraries(models PUBLIC nlohmann_json::nlohmann_json)

target_link_libraries(NanoTrade engine models utils nlohmann_json::nlohmann_json)
target_link_libraries(TestHarness engine models utils nlohmann_json::nlohmann_json)

# pybind11 for Python bindings
find_package(pybind11 CONFIG QUIET)
if (NOT pybind11_FOUND)
	include(FetchContent)
	FetchContent_Declare(
		pybind11
		GIT_REPOSITORY https://github.com/pybind/pybind11.git
		GIT_TAG v2.13.2
	)
	FetchContent_MakeAvailable(pybind11)
endif()

# Python extension module
pybind11_add_module(_nanotrade_ext src/bindings.cpp)
target_link_libraries(_nanotrade_ext PRIVATE engine models utils nlohmann_json::nlohmann_json)
target_include_directories(_nanotrade_ext PRIVATE include)

