#!/usr/bin/env bash
# Source from repository scripts. Keep the same defaults as the original debug build.
pipboy_toolchain="${XDG_DATA_HOME:-$HOME/.local/share}/obd-bench-toolchain"
export JAVA_HOME="${JAVA_HOME:-$pipboy_toolchain/jdk}"
export ANDROID_HOME="${ANDROID_HOME:-$pipboy_toolchain/android-sdk}"
export PATH="$JAVA_HOME/bin:$PATH"
pipboy_build_tools="$ANDROID_HOME/build-tools/35.0.0"
