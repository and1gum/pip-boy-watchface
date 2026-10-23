#!/usr/bin/env bash
# Cryptographic integration tests using the real Android APK verifier.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/toolchain.sh
pipboy_version=$(sed -n 's/^pipboyVersionName=//p' gradle.properties)
pipboy_test_dir=$(mktemp -d)
trap 'rm -rf "$pipboy_test_dir"' EXIT
pipboy_helper=(java --class-path "$pipboy_build_tools/lib/apksigner.jar" scripts/ApkCompatibility.java)
for pipboy_pair in 'PipBoy' 'PipBoy-Compass'; do
    "${pipboy_helper[@]}" "artifacts/$pipboy_pair-0.2.0-debug.apk" "artifacts/release/$pipboy_pair-$pipboy_version-release.apk" 35
    "${pipboy_helper[@]}" "artifacts/$pipboy_pair-0.2.0-debug.apk" "artifacts/release/$pipboy_pair-$pipboy_version-release.apk" 36
    if "${pipboy_helper[@]}" "artifacts/release/$pipboy_pair-$pipboy_version-release.apk" "artifacts/$pipboy_pair-0.2.0-debug.apk" 35 > "$pipboy_test_dir/reverse.log" 2>&1; then
        echo 'FAIL: release-to-debug transition accepted' >&2; exit 1
    fi
    grep -q 'Incompatible signing certificates' "$pipboy_test_dir/reverse.log"
done
keytool -genkeypair -keystore "$pipboy_test_dir/unrelated.p12" -storepass test-only-password -keypass test-only-password -alias unrelated -keyalg RSA -keysize 2048 -validity 2 -dname 'CN=Unrelated test key' > /dev/null 2>&1
"$pipboy_build_tools/apksigner" sign --ks "$pipboy_test_dir/unrelated.p12" --ks-pass pass:test-only-password --out "$pipboy_test_dir/unrelated.apk" watchface/build/outputs/apk/release/watchface-release-unsigned.apk
if "${pipboy_helper[@]}" "$pipboy_test_dir/unrelated.apk" "artifacts/release/PipBoy-$pipboy_version-release.apk" 35 > "$pipboy_test_dir/unrelated.log" 2>&1; then
    echo 'FAIL: unrelated signing key accepted' >&2; exit 1
fi
grep -q 'Incompatible signing certificates' "$pipboy_test_dir/unrelated.log"
echo 'PASS: debug-to-release rotation on API 35/36; reverse rotation and unrelated signer rejected'
