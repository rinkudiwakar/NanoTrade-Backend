@echo off
cd build
cmake ..
cmake --build .
echo Running program...
NanoTrade.exe