# Джерела даних і фактичні обмеження

Поточна версія 0.2.0 повертає лімб і власне числове ускладнення компаса.
Новий механізм — публічні push-запити, без privileged immediate callbacks.
Обидва APK установлені; фізичні push-оновлення й зупинка/відновлення
датчика підтверджені. Лімб і нижні показники відновлені; згладжування очікує оцінки користувача.

Перевірка на SM-L715F 2026-10-11. Скріншоти та повні журнали не включаються
в Git: вони можуть містити особисті календарні дані або ідентифікатори.

| Елемент | Джерело | Фактичний стан |
| --- | --- | --- |
| Час і дата | WFF HOUR_0_23_Z, MINUTE_Z, DAY_OF_WEEK, DAY_Z | Великий час на фізичному екрані, зміна хвилини спостерігалася |
| Кроки / ціль | STEP_COUNT, STEP_GOAL | Система повернула 2603 / 10000, прогрес відображається |
| Пульс | HEART_RATE | На екрані 76, синє серце; 128 → жовте перевірено тестом |
| Батарея годинника | BATTERY_PERCENT | Реальний відсоток і сектор на екрані |
| Батарея телефона | MobileBatteryComplicationService, RANGED_VALUE_VALUE | Провайдер прив'язаний, сектор і число на екрані; SHORT_TEXT не підтримуємо |
| Календар | NEXT_EVENT, LONG_TEXT | NEXT_EVENT: на фізичному екрані підтверджено подію з часом 20:00 та українською назвою у двох дугах; попереднє повідомлення без подій також перевірено |
| Погода | WEATHER і WEATHER.HOURS.3/.6 | Після перемикання циферблата відновлено NOW 19°, +3 18°, +6 16°; підтверджено runtime та фізичним AOD-скриншотом |
| Компас | TYPE_ROTATION_VECTOR → азимут верхнього краю екрана | У native Activity отримано N · 002°, sensorservice підтвердив потік подій |

## Компас: власний push-провайдер

`TYPE_ROTATION_VECTOR` → азимут верхнього краю дисплея → `RANGED_VALUE`
безперервні градуси (текст нормалізовано до 0–359°) → від’ємний кут обертання лімба. Нерухомі годинні позначки окремі.
Новий код використовує `ComplicationDataSourceUpdateRequester`; оновлення
при зміні експериментально до 30 Гц із програмною інтерполяцією, незмінний
азимут підтверджується раз на 4 секунди. Частота датчика не підвищена;
користь для плавності та витрата батареї ще перевіряються.
Недостовірні або старші за 5 секунд дані повертаються як `NoData`.
Справжній північний напрямок 0° не вважається відсутністю даних.

Датчик працює лише за наявності активного слота, увімкненого провайдера,
активного розблокованого дисплея поза AOD. Відсутній сигнал точної видимості
циферблата: інший foreground-застосунок теж може залишити датчик активним.
Системний рушій може обмежувати push-запити; плавність лімба ще перевіряється.
Зупинка датчика підтверджена sensorservice та журналами. Див. [архітектуру](compass-push.md).

Попередній механізм immediate callbacks потребував
`USE_IMMEDIATE_COMPLICATION_UPDATE` рівня signature|privileged|vendorPrivileged;
`pm grant` повернув `not a changeable permission type`. Новий код цей дозвіл
не декларує. Samsung Compass публікує лише барометр, а Samsung Ultra читає
SensorManager всередині свого виконуваного циферблата. Це не доводить
ексклюзивності живого компаса: [дослідження SimpleWF](simplewf-compass.md)
підтвердило використання публічних push-запитів стороннім провайдером.

## Календар

Поточні радіуси 194/173, сектор −60°..+60°, вирівнювання CENTER кожного
рядка та обидва шрифти Liberation Mono Bold 20. Місткість першого рядка
33 отримана з метрик вбудованого моноширинного шрифту. Час має розмір
115.434; host-перевірки не знаходять перетину, включно із запасом 2 пікселі.

Перший рядок переноситься на останньому пробілі/NBSP, що вміщується.
Другий отримує весь залишок тексту; WFF TextCircular ellipsis=TRUE
обрізає його за фактичною шириною. Попереднє ручне відкидання цілого
останнього слова створювало зайву порожнечу й прибране. Тепер останнє
видиме слово може закінчуватися трикрапкою; ручного зрізання всередині
UTF-16 пари в XML немає. Нативне обрізання складних emoji та їх повне
відображення цим шрифтом не підтверджене. Табуляції, явні переноси рядка
та перенесення за дефісами окремо не реалізовані. Джерело календаря
залишається системним NEXT_EVENT. Деталі — [calendar-layout.md](calendar-layout.md).

Для фактично спостереженого українського та англійського повідомлення
відсутності подій використовується NO UPCOMING EVENTS. Інші локалізації
системного повідомлення можуть залишатися мовою провайдера. Коли джерело
відсутнє, використовується CALENDAR UNAVAILABLE. Після встановлення
оновлення на фізичному екрані підтверджено наявну подію з часом 20:00 та
довгою українською назвою у двох дугах: artifacts/device-calendar-restored.png.
Точний розподіл часу між TEXT/TITLE у dump залишається прихованим, але
сам час події та дворядковий текст видно без обрізання чи перетину з часом.

## Погода, свіжість і AOD

Для +3/+6 використовуємо незалежні погодинні стан, температуру та IS_DAY.
Підписи — поточна ціла година +3/+6, а не підтверджений timestamp провайдера.
Погодинна ймовірність опадів у WFF не задокументована, тому майбутні іконки
відображають стан без запозичення поточної ймовірності. Для поточного дощу
пороги 20/70 відповідають 1/2/3 краплям. Інтенсивність не обчислюється з
ймовірності. Сухий стан не отримує краплі навіть при ненульовій ймовірності.

При IS_AVAILABLE=false — «—» і невідома іконка; при доступних даних та
IS_ERROR=true — позначка «!». HEART_RATE, STEP_COUNT і стороння батарея не
дають надійного часу вимірювання в використаному WFF інтерфейсі. Сам факт
позитивного пульсу не доводить свіжість. Стан відсутності даних перевірено,
але всі сценарії втрати/відновлення телефона ще не підтверджені.

Перевірка 2026-10-11: усі три IS_AVAILABLE=false, IS_ERROR=true,
Loading=false, WeatherOperationError=WeatherGenericException із скасованим
coroutine job. Samsung Weather водночас показував наявні погодні дані;
геолокація ввімкнена, дозволи системного погодного провайдера надані.
Відкриття Weather і повторний вибір того самого циферблата не відновили WFF.
Перемикання на Samsung Ultra (Favorite 5), потім назад на Pip-Boy (Favorite 13)
створило новий запит: Loading=true, потім доступні всі три точки,
IS_ERROR=false, TWC, 14 погодинних записів. Runtime повернув 19/18/16°C;
скриншот природного AOD підтвердив температури й іконки NOW/20:00/23:00.
Після відкриття іншого застосунку та повернення дані залишилися доступними.
Код/APK та дозволи не змінювалися. Це підтверджує відновлення через
перестворення циферблата; початкова причина скасування запиту й автоматичне
відновлення після майбутнього повторення ще не встановлені.

AOD у XML приховує активні групи та всі три complication slots; лишає час,
дату, три погодні точки зеленими та приглушений обідок. Host-прев'ю це
перевіряє. Початкова примусова спроба засинання дала екран блокування; її припинено
через PIN. У 0.2.0 природний AOD підтверджений скриншотом: час, дата,
три погодні точки та обідок, без компаса/пульсу/секторів.

## Первинні довідники

- [WFF sources](https://developer.android.com/reference/wear-os/wff/common/attributes/source-type)
- [Expressions and numeric +](https://developer.android.com/reference/wear-os/wff/common/attributes/arithmetic-expression)
- [Font resources](https://developer.android.com/reference/wear-os/wff/group/part/text/font)
- [Immediate complication updates](https://developer.android.com/reference/androidx/wear/watchface/complications/datasource/ComplicationDataSourceService)


## Пульс, тиск і сонячні часи — 2026-10-12

Пульс має шрифт 48 px, окремий тач на серці й числі та короткі роздільники.
Тиск надходить із TYPE_PRESSURE годинника (медіана короткої серії), у hPa;
історія зберігається локально. Тренд порівнює тиск із вимірюванням приблизно
три години тому: від +1 hPa — жовтий стовпчик, до −1 hPa — синій, між ними —
зелений. Без достатньої історії стовпчик приглушений; стрілок немає.
Число округлюється до цілих мм рт. ст., тому колір може змінитися, поки
відображене число залишається тим самим. Без вимірювання показується риска.

Схід і захід обчислює Commons Suncalc 3.11 за приблизними координатами,
локальною датою й часовим поясом годинника. Пошук обмежений поточним днем,
тому після заходу залишається сьогоднішній схід. Для полярного дня/ночі
відсутні події показуються рискою. Будинки й рельєф не враховуються.

Компілекейшен автоматично запитує приблизне мережеве місце, коли попереднє
старше 30 хвилин; планова частота оновлення — раз на годину, фактичний час
визначає Wear OS. Потрібні ACCESS_COARSE_LOCATION та ACCESS_BACKGROUND_LOCATION
(«Дозволяти завжди»). Постійного GPS, foreground service для локації й
серверного обчислення немає. Якщо свіже місце недоступне, використовується
останнє збережене. Зміна дати/часового поясу запускає перерахунок.

Samsung Informative №8 використовує приватний WeatherComplicationDataProvider,
який перевіряє системний статус/підпис Samsung. Стандартний Samsung
SunriseSunsetComplicationService віддає лише найближчу подію. Наші слоти 5/6
тому використовують власний SolarSource, а не приватний API Samsung.


Фізична перевірка 2026-10-12: сонячний провайдер повернув 07:15 / 18:13,
що збігається із Samsung Informative №8. Пульс: серце, лівий і правий край
числа відкрили Samsung Health HeartRateActivity. Обидва краї погодного
прямокутника відкрили WeatherActivity. Журнали й скриншоти збережені лише
в локальних artifacts/. Текст тиску опущено до y=337 і повністю вміщено
в рамку комплікейшена; є запас ширини для 1100 hPa.


Поточна геометрія тиску: число й `mm` мають спільний лівий край x=279
(START), число y=337; стовпчик займає y=332…385. Колір передає тренд,
а висота заповнення — значення тиску в діапазоні 950–1050 hPa.

## Millimeters and ambient display — 2026-10-12

Pressure display converts sensor hPa to whole mmHg using 0.750061683 and uses
the compact user-selected label `mm`. The ranged value, column range and
history stay in hPa, so the trend and column preserve their physical meaning.
1013.25 hPa → 760 mm; 994 hPa → 746 mm are covered by companion unit tests.
Pressure, sunrise and sunset slots now remain visible in AOD. Text and icons
use the existing ambient green; pressure vector parts use reduced alpha.
Calendar, compass, pulse and step/battery groups retain their existing AOD policy.

Physical verification: installed both APKs successfully, switched stock face and
back to restore weather. Active and actual Dozing/AOD screenshots both show
745 mm and today's 07:15 / 18:13. Ambient pressure, text and solar icons remain
visible at reduced brightness; wake restored the active face. Evidence:
artifacts/mm-active.png, artifacts/mm-ambient.png. 46 Python tests, companion
unit tests (including conversion) and both lint/builds passed.

Ambient readability refinement: preserve authored colors using a neutral white
ambient tint, with pressure vector opacity 255. Hardware still controls panel
brightness in AOD. The outer calendar and solar labels now share radius 194;
calendar span is 100°, solar centers ±67.5°, horizon icons y=160. Calculation
and provider bindings are unchanged.

Calendar truncation uses an explicit single U+2026 glyph, reserving one character
of the measured second-row capacity and selecting the last fitting word boundary.
Native WFF ellipsis is disabled for calendar arcs because this watch renders it
as three full-width periods. A word too long to fit without a safe boundary is
represented by the ellipsis; UTF-16 pairs and emoji sequences are never sliced.
