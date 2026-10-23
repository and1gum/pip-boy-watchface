#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/toolchain.sh
pipboy_signing_dir="${PIPBOY_SIGNING_DIR:-$HOME/.local/share/pip-boy-signing}"
for pipboy_file in release.p12 password debug-to-release.lineage; do
    test -f "$pipboy_signing_dir/$pipboy_file" || { echo "Missing signing file: $pipboy_signing_dir/$pipboy_file. Run scripts/init-release-key.sh first." >&2; exit 1; }
done
python3 scripts/generate.py
python3 -m unittest discover -s tests -v
./gradlew :watchface:lintRelease :watchface:assembleRelease :compass:testReleaseUnitTest :compass:lintRelease :compass:assembleRelease --console=plain
pipboy_version=$(sed -n 's/^pipboyVersionName=//p' gradle.properties)
mkdir -p artifacts/release
python3 scripts/sign-release.py sign watchface/build/outputs/apk/release/watchface-release-unsigned.apk "artifacts/release/PipBoy-$pipboy_version-release.apk"
python3 scripts/sign-release.py sign compass/build/outputs/apk/release/compass-release-unsigned.apk "artifacts/release/PipBoy-Compass-$pipboy_version-release.apk"
cp compass/build/outputs/mapping/release/mapping.txt "artifacts/release/PipBoy-Compass-$pipboy_version-mapping.txt"
cp "$pipboy_signing_dir/release-certificate.pem" artifacts/release/
(cd artifacts/release && sha256sum "PipBoy-$pipboy_version-release.apk" "PipBoy-Compass-$pipboy_version-release.apk" > SHA256SUMS)
