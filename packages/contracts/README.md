# contracts — контракты системы

Единственный источник истины по тому, о чём сервисы договорились между собой.
Меняется раньше кода, а не после.

## Состав

```text
contracts/
├── enums.yaml              # канонические перечисления, общие для сервисов и фронтенда
├── events.md               # доменные события: имена и полезная нагрузка
└── openapi/                # снапшоты OpenAPI каждого сервиса (коммитятся)
    ├── plan-service.json
    ├── site-service.json
    ├── analysis-service.json
    ├── vision-service.json
    ├── pos-engine.json
    └── report-service.json
```

## Как это работает

1. Разработчик меняет схемы в своём сервисе.
2. `make contracts` перегенерирует снапшоты OpenAPI и TS-клиент.
3. CI сравнивает снапшот в репозитории с тем, что отдаёт код. Расхождение — **ошибка сборки**.

Смысл: изменение контракта невозможно протащить незаметно. Оно всегда видно в диффе,
и его всегда видит потребитель.

## enums.yaml

Перечисления, которые используют минимум два сервиса. **Дублировать их списком в коде
запрещено** — сервис импортирует значения отсюда либо хранит в БД справочником.

```yaml
object_type:      [RESIDENTIAL_MONOLITH, RESIDENTIAL_PANEL, PUBLIC_BUILDING, ROAD]
construction_phase: [PREPARATORY, SUBSTRUCTURE, SUPERSTRUCTURE, ENVELOPE_ROOF, NETWORKS, LANDSCAPING]
zone_type:        [PIT, BUILDING_FOOTPRINT, PERIMETER, ENTRY_GATE, STORAGE, DANGER, ROAD]
equipment_role:   [REQUIRED, ALLOWED, SIGNATURE]
equipment_state:  [WORKING, IDLE, OUT_OF_ZONE, UNKNOWN]
stage_label:      [PIT, PILES, FOUNDATION, FRAME, FACADE, LANDSCAPING]
visibility_status:[OK, PARTIAL, BLIND]
deviation_code:   [D1, D2, D3, D4, D5, D6, D7, D8, D9, D10]
severity:         [INFO, LOW, MEDIUM, HIGH]
deviation_status: [NEW, CONFIRMED, REJECTED, RESOLVED]
stage_fact_status:[NOT_STARTED, IN_PROGRESS, DONE, LATE, AHEAD]
object_status:    [ON_TRACK, DELAY, AHEAD, UNKNOWN]
confidence:       [LOW, MEDIUM, HIGH]
image_status:     [NEEDS_TIME, PENDING, PROCESSING, ANALYZED, FAILED]
dependency_type:  [FS, SS, FF, SF]
```

**Классы техники сюда не входят** — это не перечисление, а справочник в базе
`plan-service`, редактируемый оператором. В `enums.yaml` лежит лишь **стартовая
таксономия** для первичного заполнения:

```yaml
equipment_class_seed:
  - {code: excavator,        name_ru: "Экскаватор",              group: EARTHWORKS}
  - {code: dump_truck,       name_ru: "Самосвал",                group: TRANSPORT}
  - {code: bulldozer,        name_ru: "Бульдозер",               group: EARTHWORKS}
  - {code: loader,           name_ru: "Погрузчик",               group: EARTHWORKS}
  - {code: roller,           name_ru: "Каток",                   group: ROAD}
  - {code: tower_crane,      name_ru: "Башенный кран",           group: LIFTING}
  - {code: truck_crane,      name_ru: "Автокран",                group: LIFTING}
  - {code: manipulator_crane,name_ru: "Кран-манипулятор",        group: LIFTING}
  - {code: concrete_mixer,   name_ru: "Автобетоносмеситель",     group: CONCRETE}
  - {code: concrete_pump,    name_ru: "Автобетононасос",         group: CONCRETE}
  - {code: pile_driver,      name_ru: "Буровая/сваебойная установка", group: EARTHWORKS}
  - {code: truck,            name_ru: "Грузовик",                group: TRANSPORT}
  - {code: asphalt_paver,    name_ru: "Асфальтоукладчик",        group: ROAD}
  - {code: grader,           name_ru: "Грейдер",                 group: ROAD}
  - {code: person,           name_ru: "Человек",                 group: OTHER}
```

Коды классов — `lower_snake_case`, потому что совпадают с метками CV-модели;
все остальные перечисления — `SCREAMING_SNAKE_CASE`.

## Правила изменения

- Добавить значение в перечисление — можно.
- Удалить или переименовать значение — **несовместимое изменение**, требует ADR и `v2`.
- Изменение любого из двух ключевых межсервисных контрактов (план на дату, факт сессии) —
  только через ADR: на них завязана вся методика.
