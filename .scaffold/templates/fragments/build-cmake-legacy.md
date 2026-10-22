Setup/run configure `build/debug` or `build/release` directly. After setup,
build manually with:

```sh
cmake --build build/debug --config Debug
cmake --build build/release --config Release
```

Run library tests from `build/debug` with `ctest --output-on-failure -C Debug`.
