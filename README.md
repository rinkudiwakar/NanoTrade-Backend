# NanoTrade

A tiny matching engine prototype designed for experimentation and integration.

Production hygiene added:

- Compiler production flags and sanitizers toggles in `CMakeLists.txt`.
- Formatting config `.clang-format`.
- CI workflow at `.github/workflows/ci.yml` (build + run harness).
- `TestHarness` executable for integration smoke tests.

Quick build (Release):

```powershell
cmake -S . -B build -D CMAKE_BUILD_TYPE=Release
cmake --build build --config Release
.
build\\TestHarness.exe
```

