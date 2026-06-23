import sys

with open(r'd:\coding\NanoTrade\CMakeLists.txt', 'a') as f:
    f.write('\n# pybind11 for Python bindings\n')
    f.write('find_package(pybind11 CONFIG QUIET)\n')
    f.write('if (NOT pybind11_FOUND)\n')
    f.write('	include(FetchContent)\n')
    f.write('	FetchContent_Declare(\n')
    f.write('		pybind11\n')
    f.write('		GIT_REPOSITORY https://github.com/pybind/pybind11.git\n')
    f.write('		GIT_TAG v2.13.2\n')
    f.write('	)\n')
    f.write('	FetchContent_MakeAvailable(pybind11)\n')
    f.write('endif()\n')
    f.write('\n# Python extension module\n')
    f.write('pybind11_add_module(_nanotrade_ext src/bindings.cpp)\n')
    f.write('target_link_libraries(_nanotrade_ext PRIVATE engine models utils nlohmann_json::nlohmann_json)\n')
    f.write('target_include_directories(_nanotrade_ext PRIVATE include)\n')
