# Data sources and limitations

Pip-Boy 0.2.0 was tested on a Samsung Galaxy Watch Ultra2 (2026; SM-L715F) with Wear OS 7. The face uses Watch Face Format (WFF) system data and Wear OS complications. The [installation guide](install.md) explains how to build both APKs, install the companion, and check the preset providers. Behavior on other watches has not been verified.

| Display | Source | Current limitation |
| --- | --- | --- |
| Digital time and date | WFF time and calendar fields | Time uses the watch's clock in 24-hour format. |
| Steps and goal | WFF step count and goal | Availability depends on the watch's health provider. |
| Heart rate | WFF heart rate | WFF does not expose a reliable measurement timestamp here; a positive number does not prove that it is fresh. |
| Watch battery | WFF battery percentage | The percentage and sector come from the watch. |
| Phone battery | [Phone Battery Complication](https://play.google.com/store/apps/details?id=com.weartools.phonebattcomp&hl=en), RANGED_VALUE | Separate third-party phone and watch apps are required. The provider is not included in this repository. |
| Next event | Wear OS NEXT_EVENT complication | Calendar access and event availability depend on the system provider. |
| Weather | WFF current and +3/+6 hour fields | Forecast labels are calculated from the current whole hour; they are not provider timestamps. |
| Compass | Pip-Boy Compass companion, TYPE_ROTATION_VECTOR | Updates require an active, unlocked display and may be limited by Wear OS. |
| Pressure | Pip-Boy Barometer companion, TYPE_PRESSURE | The whole-mmHg number can stay the same while the trend color changes. |
| Sunrise and sunset | Pip-Boy companion, approximate watch location | Times depend on location availability and the watch's local date and time zone. |

## Compass

The companion converts the rotation-vector sensor reading to the heading of the top edge of the watch. It supplies a continuous RANGED_VALUE from 0 to 359 degrees; the face rotates the compass rim by the negative heading. Fixed hour markers do not rotate. North at 0° is a valid reading. Invalid readings and readings older than five seconds are withheld.

The provider uses public ComplicationDataSourceUpdateRequester requests. It can request updates when the heading changes, experimentally up to 30 Hz, and confirms an unchanged heading every four seconds. The sensor sampling rate was not raised. Wear OS may throttle requests, so smoothness and long-term battery use still need evaluation. Tracking pauses when its provider is disabled or the display is asleep, locked, or in AOD. The watch does not expose an exact face-visibility signal; another foreground app can leave the sensor active. See [compass architecture](compass-push.md).

## Calendar

The upper two arcs show the next event from the system NEXT_EVENT provider. The event time and title are wrapped at a fitting word boundary. The second row is truncated with a single ellipsis when necessary; the XML does not split UTF-16 pairs or emoji sequences. Tabs, explicit line breaks, and hyphenation are not handled separately. Other locales may return provider text in their own language.

When no event is reported, the face displays NO UPCOMING EVENTS for the system responses observed during testing. When the source is unavailable, it displays CALENDAR UNAVAILABLE. The system provider, not the face, controls calendar access. See [calendar layout](calendar-layout.md).

## Weather and AOD

The +3/+6 weather positions use their own hourly condition, temperature, and day/night fields. Their labels are the watch's current whole hour plus three or six hours, not a confirmed timestamp from the provider. WFF does not document hourly precipitation probability for these fields, so future icons do not borrow the current probability. For current rain, thresholds of 20 and 70 percent select one, two, or three drops; these icons do not claim to measure rainfall intensity.

If a weather value is unavailable, the face shows a dash and an unknown icon. An error marker appears when the provider reports an error, independently of availability. On the test watch, weather once remained unavailable after an interrupted provider request while Samsung Weather still had data. Switching to another face and back recreated the request and restored all three values. The original cancellation and automatic recovery behavior remain unverified; see [weather recovery](weather-recovery.md).

AOD keeps digital time, date, and three weather positions. It hides pressure, sunrise, sunset, the active compass, calendar, heart rate, steps, battery sectors, and analog hands. Pressure and solar times remain on the active screen. The watch controls actual panel brightness; hiding a slot does not itself set its provider's update interval.

Weather is supplied through the system's WFF `WEATHER.*` data sources. Pip-Boy has no weather fetch timer, network client, or weather complication provider. WFF exposes `WEATHER.LAST_UPDATED` for freshness, but no documented watch-face setting for the fetch interval. Consequently, the face cannot enforce at most one weather update per hour; scheduling belongs to the watch's system weather service. This is separate from rendering the latest available value or advancing the +3/+6-hour labels. See the [official WFF weather documentation](https://developer.android.com/training/wearables/wff/weather).

## Heart rate, pressure, and solar times

The heart color uses five fixed colors and four default boundaries. The boundaries can be changed manually in the face editor; they are not imported from Samsung Health. The [README](../README.md#how-the-face-behaves) lists the default ranges. An unavailable heart-rate value appears as a dash.

The pressure provider takes a short burst from the watch's pressure sensor and uses its median. It keeps a short local history in hPa. The displayed value is rounded to whole millimeters of mercury (mmHg), using 0.750061683 mmHg per hPa, with the compact label “mm”. For example, 994 hPa displays as 746 mm. The color compares the current reading with one from about three hours earlier: amber for at least +1 hPa, blue for at most −1 hPa, green between those thresholds, and muted when history is insufficient. There is no direction arrow. Rounding can leave the displayed number unchanged even when the trend color changes. The column's fill represents pressure on a 950–1050 hPa scale; its current vertical span is y=342–375.

Samsung Barometer's complication on the tested watch supports `SHORT_TEXT` and `LONG_TEXT`, but not the `RANGED_VALUE` needed for this numeric column. The companion supplies that value and calculates the trend; it still uses the watch's own pressure sensor.

The companion calculates sunrise and sunset for the watch's local calendar day using Commons Suncalc 3.11 and approximate coordinates. It keeps today's sunrise visible after sunset. Polar days or nights can leave an event unavailable. Buildings and terrain are not included in the calculation. When the saved location is older than 30 minutes, the provider requests a new approximate network location. Planned updates are hourly, but Wear OS controls their actual timing. If a fresh location is unavailable, it may use the last saved one. Date and time-zone changes trigger recalculation.

The companion needs approximate and background location access (“Allow all the time”) for periodic solar updates. It does not run continuous GPS or send the calculation to a project server. The watch's system location service may use its own network services. Samsung's standard SunriseSunsetComplicationService supplies only the next event, so Pip-Boy uses its own provider for separate sunrise and sunset fields.

## References

- [WFF source fields](https://developer.android.com/reference/wear-os/wff/common/attributes/source-type)
- [WFF expressions](https://developer.android.com/reference/wear-os/wff/common/attributes/arithmetic-expression)
- [WFF fonts](https://developer.android.com/reference/wear-os/wff/group/part/text/font)
- [Wear OS complication provider updates](https://developer.android.com/reference/androidx/wear/watchface/complications/datasource/ComplicationDataSourceService)
