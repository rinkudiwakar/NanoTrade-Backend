cmake_minimum_required(VERSION 3.10)

project(NanoTrade)

set(CMAKE_CXX_STANDARD 17)

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
add_executable(NanoTrade src/main.cpp)

# Include directories
target_include_directories(engine PUBLIC include)
target_include_directories(models PUBLIC include)
target_include_directories(utils PUBLIC include)

# Link everything
target_link_libraries(NanoTrade engine models utils)