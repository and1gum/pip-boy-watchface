# Перевірка приватності APK / APK privacy check

23 October 2026 — version 0.3.0. The two APKs were downloaded from GitHub Releases and matched byte for byte with the signed build outputs.

| APK | SHA-256 |
| --- | --- |
| `PipBoy-0.3.0-release.apk` | `1d1b5ddec1602529e8407c5f6fc00a7786cc9c26d1b4b0ac30734b809369b4fc` |
| `PipBoy-Compass-0.3.0-release.apk` | `3054701d59f63fce6c29ccf485365b53d10c167f7aa2c2da357dec6dffc8ce97` |

Перевірено вміст ZIP, рядки DEX, маніфести, таблиці ресурсів, сертифікати й вбудоване прев’ю. Приватних налаштувань, координат із годинника, його серійного номера/IP, журналів, історії, паролів, приватних ключів або шляхів до особистих каталогів у цих APK не виявлено. Обидва APK не запитують INTERNET. Дані, що з’являються на циферблаті під час роботи, надходять від пристрою та провайдерів; вони не копіюються в дистрибутив під час оновлення.

Публічні ідентифікатори автора `and1gum` містяться в назвах пакетів і сертифікаті підпису. APK містить публічні сертифікати й підтвердження ротації, які не є приватними ключами. Параметри зон пульсу включені у WFF. Назву зустрічі у статичному демо-прев’ю залишено за прямою вказівкою користувача; це зображення не оновлюється даними з годинника під час збірки.

The inspection covered ZIP entries, DEX strings, manifests, resource tables, signing certificates and the embedded preview. No private preferences, saved watch coordinates, watch serial/IP, logs, history, passwords, private keys or personal directory paths were found in these binaries. Neither APK requests INTERNET. Runtime complication values come from the device/providers and are not copied into distribution APKs during an update.

The public author handle `and1gum` appears in package names and the signing certificate. APK signing certificates and rotation proof are public, not private keys. Heart-rate zone settings are included in WFF. The calendar meeting title in the static demo preview was explicitly accepted by the user and retained. The packaged preview is not refreshed from the watch during a build.
