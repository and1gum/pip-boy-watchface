# Pip-Boy watch face

A Fallout-inspired Pip-Boy style watch face for Wear OS. Large digital time is the focus, with hour, minute and second hands layered over it. The face also shows weather, date, the next calendar event, heart rate, steps, watch and phone battery, compass, barometric pressure, sunrise and sunset.

**Status:** experimental source project, version 0.3.0. Earlier debug builds were tested on a Samsung Galaxy Watch Ultra2 (2026; model SM-L715F) running Wear OS 7 (Android 17), 498 × 498 display. It has not been packaged for the Play Store. Release 0.3.0 was also verified on this watch: debug-to-release key rotation, retained configuration/provider bindings and permissions, active display and natural AOD. Battery use has not been measured in a controlled comparison.

![Active mode captured on the watch](docs/images/active-2026-10-23.png) ![Ambient mode captured on the watch](docs/images/ambient-2026-10-23.png)

*Unedited screenshots captured on the watch on 23 October 2026: current active mode on the left, natural always-on display on the right.*

[Українською](README.uk.md) · [Install on a watch](docs/install.md) · [Data and limitations](docs/data-sources.md) · [Troubleshooting](docs/troubleshooting.md)

## What you need

- A compatible Wear OS watch with Android 15 or newer (SDK 35+). The tested device is listed above; other models are unverified.
- A computer with Android Debug Bridge (ADB) and wireless access to the watch for sideloading.
- Two APKs built from this repository: the watch face and its companion. The face itself needs no phone application.

The companion supplies compass, pressure, sunrise and sunset complications. Other values come from the watch or complication providers already installed on your devices. For phone battery, install [Phone Battery Complication](https://play.google.com/store/apps/details?id=com.weartools.phonebattcomp&hl=en) on the phone and watch. This third-party provider is not included in the face; when installed, its **RANGED_VALUE** source is the face's default.

## Install and set up

Follow the [step-by-step installation guide](docs/install.md). Build both APKs with `bash scripts/build-release.sh`, pair ADB with the watch, install the companion first, then the face, and choose **Pip-Boy** in the watch-face picker. The calendar, phone battery, compass, pressure, sunrise and sunset sources are preset in the face; available providers do not need manual selection. Open **Pip-Boy Compass** once to enable its sensor service. For solar times, grant approximate and background location to the companion and open its environment screen to fetch the watch's location.

Use the two signed **0.3.0 release APKs** from [GitHub Releases](https://github.com/and1gum/pip-boy-watchface/releases). Release is the primary installation variant. The companion uses R8 code and resource optimization; battery savings have not been measured. Debug builds remain available through `bash scripts/build.sh`.

The release uses a dedicated permanent key with a verified signing lineage from the project's original debug key. The [installation script](docs/install.md#4-install-and-select-the-face) checks both installed signatures before updating without uninstalling. This migration preserved the existing face instance, heart-rate settings, provider bindings and location permissions on the tested watch. A debug build signed with another developer's key is incompatible. See [signing and migration](docs/release-signing.md).

## How the face behaves

The compass uses the watch's rotation sensor and may disappear when the display sleeps, locks, or the sensor reading becomes stale. Ambient mode keeps only the date, digital time and weather. Pressure, sunrise and sunset remain on the active screen. Weather and calendar availability depend on the watch's system providers and their permissions. The system weather service controls refresh frequency; WFF has no watch-face setting for an hourly fetch interval. Sunrise and sunset use an approximate watch location; pressure uses the watch's pressure sensor. Missing data appears as missing data rather than a made-up reading.

The heart icon changes color with the heart-rate range. These default thresholds and colors are set in the code:

| Heart rate, bpm | Color |
| --- | --- |
| 1–98 | Blue |
| 99–109 | Green |
| 110–131 | Yellow |
| 132–164 | Orange |
| 165 and above | Red |

You can manually change the four boundaries between ranges in the watch-face editor; they must stay in ascending order. The colors remain fixed. This is the face's own indicator, not your personal Samsung Health zones. When heart rate is unavailable, the number becomes a dash and the heart keeps its default green color without indicating a zone.

The project makes no network request of its own. Location and pressure history stay on the watch in the companion's local storage; the face itself receives data through Wear OS complications. Android permissions used by the companion are explained in the [installation guide](docs/install.md#permissions-and-privacy).

## Tap actions

| Tap | Opens |
| --- | --- |
| Weather area | Samsung Weather |
| Calendar arc | The system calendar event |
| Steps icon or sector | Samsung Health steps |
| Watch or phone battery icon or sector | Watch battery status |
| Bottom steps or battery number, or compass heading | Samsung Compass |
| Heart-rate number | Heart-rate screen |
| Sunrise or sunset | Companion location screen |

Samsung app shortcuts depend on those apps being installed.

## Help and development

- [Troubleshooting](docs/troubleshooting.md): missing data, compass wake-up, updates and ADB.
- [Optional diagnostics](docs/companion-diagnostics.md): record and export a compass issue.
- [Developer guide](docs/development.md): build requirements, source layout and companion lifecycle.

Third-party font and library notices are in [licenses/](licenses/).
