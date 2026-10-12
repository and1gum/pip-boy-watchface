#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
pipboy_toolchain="${XDG_DATA_HOME:-$HOME/.local/share}/obd-bench-toolchain"
export JAVA_HOME="${JAVA_HOME:-$pipboy_toolchain/jdk}"
export ANDROID_HOME="${ANDROID_HOME:-$pipboy_toolchain/android-sdk}"
python3 scripts/generate.py
python3 -m unittest discover -s tests -v
./gradlew :watchface:lintDebug :watchface:assembleDebug :compass:testDebugUnitTest :compass:lintDebug :compass:assembleDebug --console=plain
mkdir -p artifacts
cp watchface/build/outputs/apk/debug/watchface-debug.apk artifacts/PipBoy-0.2.0-debug.apk
cp compass/build/outputs/apk/debug/compass-debug.apk artifacts/PipBoy-Compass-0.2.0-debug.apk
(cd artifacts && sha256sum PipBoy-*.apk > SHA256SUMS)
