# Weather failure and recovery, 2026-10-11

## Confirmed on SM-L715F

The Samsung Weather app had weather data while Pip-Boy's WFF runtime reported
all three availability flags false, error true, loading false and a canceled
coroutine wrapped in WeatherGenericException. Opening Samsung Weather alone
did not heal this state. Selecting the same face did not heal it either.
Switching to Samsung Ultra Favorite 5 and back to Pip-Boy Favorite 13 produced
Loading=true, followed by available NOW/+3/+6 and 19/18/16 degrees. A natural
AOD screenshot confirmed those readings. Another APK installation reproduced
the empty/canceled state. Therefore switching is a recovery workaround, not a
completed fix or proof of reliable automatic retry.

## Installed runtime inspection

Inspected the legitimately installed Samsung runtime 5.0.00.8 APK. No proprietary
implementation is copied into this project. Obfuscated names below describe only
this exact APK and must not be used as a production API.

* x2/X.g starts initial weather registration/fetch via x2/J and x2/X.r.
* x2/X.x registers for updates, then requests initial data. Its generic Exception
  catch includes cancellation and stores x2/C (WeatherGenericException), sets
  loading=false and notifies listeners. That catch has no timed retry loop.
* x2/X.v stores a successful WeatherData snapshot in field u, with its timestamp,
  and clears the error. This is instance memory, not our persistent disk cache.
  A new/replaced face instance cannot rely on its predecessor's snapshot.
* The two-minute constant in x2/X.D / x2/V is a loading watchdog for a specific
  provider error code, not a general two-minute retry interval for cancellation.
* Lifecycle/provider events can request data again; no fixed cancellation-retry
  frequency is established. Our resource-only face has no imperative retry or
  persistent-cache code.

Direct reuse of Samsung's underlying weather service is protected:
WeatherWatch manifest exports DwfWeatherService with
com.google.wear.permission.RECEIVE_WEATHER. The device reports that permission
as signature|privileged, owned by com.google.wear.services. A normal installed
provider cannot assume access or acquire it with an ordinary runtime grant.
This restriction concerns that service; it does not forbid third-party weather
providers using other sources.

## Bounded UI changes are insufficient

The generated face now marks WEATHER.IS_ERROR independently of IS_AVAILABLE,
keeps any data the runtime still supplies, and has a Samsung Weather launch
action. Host tests cover error with/without data and recovery clearing the marker.
These changes do not create a last-good snapshot or a retry mechanism. The earlier fully
transparent launch region did not open Weather in the physical tap test. On
2026-10-12 it was replaced by one shared rectangle with a nonzero-alpha fill,
above complication targets. Its four corners and center physically opened
Samsung Weather; see `artifacts/weather-taps-device-verification.txt`.
Do not report this as a weather-reliability fix.

## Required reliable behavior

A source we control must persist only complete successful forecasts, retain them
on network/provider errors and process restarts, and choose NOW/+3/+6 against
the forecast timestamps as time advances. It must expose stale/error status,
stop using a snapshot after its forecast horizon expires, and distinguish an
empty first run from a failed refresh. Repeated requests need bounded backoff
and a normal refresh schedule, subject to Wear OS background scheduling limits.

Reading the protected Samsung service is not a supported implementation path.
An independent weather source would change the original Samsung/WFF data-source
architecture and needs the user's agreement under the original implementation
plan before implementation. No independent weather source, new location
permission, or network weather request has been introduced.
