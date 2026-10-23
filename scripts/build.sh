#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/toolchain.sh
python3 scripts/generate.py
python3 -m unittest discover -s tests -v
./gradlew :watchface:lintDebug :watchface:assembleDebug :compass:testDebugUnitTest :compass:lintDebug :compass:assembleDebug --console=plain
pipboy_version=$(sed -n 's/^pipboyVersionName=//p' gradle.properties)
mkdir -p artifacts
cp watchface/build/outputs/apk/debug/watchface-debug.apk "artifacts/PipBoy-$pipboy_version-debug.apk"
cp compass/build/outputs/apk/debug/compass-debug.apk "artifacts/PipBoy-Compass-$pipboy_version-debug.apk"
(cd artifacts && sha256sum "PipBoy-$pipboy_version-debug.apk" "PipBoy-Compass-$pipboy_version-debug.apk" > SHA256SUMS)
