# Порядок работ

Единственный список задач проекта: что делать, в каком порядке, как понять, что готово.
Рубежи, порядок сокращения объёма и риски — в [roadmap.md](roadmap.md). Правила кода — в
[AGENTS.md](../AGENTS.md).

---

## 1. Протокол для агента: «начинай» / «продолжай»

Если человек назвал конкретную задачу — делай её. Если сказал «начинай», «продолжай» или
«делай дальше» — работай по этому протоколу.

1. **Прочитай** (если ещё не читал в этой сессии) `CLAUDE.md` → `AGENTS.md` →
   `docs/architecture.md` → `packages/contracts/interservice.md`.
2. **Найди задачу:**
   - первая задача со статусом `[~]` — незаконченная, продолжай её с заметки «остановился»;
   - если таких нет — первая `[ ]` сверху, у которой все задачи из «ждёт» закрыты `[x]`;
   - задачи с пометкой **(человек)** не делаешь, а в конце сессии напоминаешь о незакрытых.
3. **Поставь `[~]`** у взятой задачи.
4. **Прочитай всё из «спец»** задачи и README затрагиваемого сервиса.
5. **Сделай задачу** снизу вверх: `core/` с тестами → `dal/` → `services/` → `api/`. Не выходи
   за пределы задачи. Соседний баг, найденный по пути, — запиши строкой в раздел 9, не чини молча.
6. **Проверь** (команды — раздел 2):
   - линт;
   - тесты затронутого сервиса;
   - если менялись контейнеры или compose — стек поднимается и отвечает `/health/ready`.

   Не проходит — чини. После трёх безуспешных подходов остановись и опиши проблему в задаче.
7. **Обнови документы** по DoD из AGENTS.md, раздел 5:
   - README сервиса — если менялись эндпоинты, конфигурация или модель;
   - `docs/traceability.md` — если закрыто требование ТЗ.
8. **Закрой задачу:** поставь `[x]` и допиши в её строку одну фразу — что сделано и где.
9. **Закоммить** код и `board.md` одним коммитом в текущую ветку: `feat(<сервис>): <кратко> (T07)`.
   Добавляй в коммит только свои файлы (`git add <пути>`, не `git add -A`): чужие незакоммиченные
   правки в рабочем дереве не трогай. Не пушь: это решает человек.
10. **Бери следующую задачу** (шаг 2).

**Когда останавливаться и спрашивать человека:**
- доступных задач нет — всё закрыто или ждёт задач человека;
- нужны данные, которых нет в репозитории: снимки, XLSX, нормы, ключи;
- спецификация противоречит сама себе или коду так, что выбор меняет контракт или методику;
- Docker не запущен, а задаче он нужен. В этом случае сначала сделай всё, что возможно без
  Docker (`core/` и unit-тесты);
- контекст на исходе. Закоммить готовое, если проверки зелёные, оставь `[~]` и строку
  «остановился: …; дальше: …».

**Чего не делать:**
- **Не выдумывай данные.** Нормативы, метрики, результаты замеров, праздники, пути к весам —
  только из документов и реальных запусков. Нет данных — пиши «не измерено» или «ждёт H3».
- **Не меняй молча документы-источники** (`architecture.md`, `methodology.md`, `data-model.md`,
  `interservice.md`). Если реализация требует отступить, сначала правка документа или ADR
  отдельным коммитом `docs: …` с объяснением, потом код.
- **Не дроби без записи.** Если задача разрастается больше чем на ~300 строк диффа, раздели её
  здесь же на `T15a`, `T15b` и делай по одной.

## 2. Команды проверки на демо-стенде (Windows, PowerShell)

`make` здесь не работает: рецепты Makefile требуют bash. Используй прямые команды.

```powershell
# линт (версия ruff — 0.16.8; при другой: python -m pip install ruff==0.16.8)
ruff check --config tools/ruff.toml packages services scripts
ruff format --check --config tools/ruff.toml packages services scripts

# тесты одного сервиса (unit-тесты core/ работают без Docker)
cd services/analysis-service; $env:PYTHONPATH='.'; pytest -q; cd ../..

# стек (нужен запущенный Docker Desktop)
docker compose up -d --build
docker compose ps
curl.exe -s http://localhost:8001/health/ready
```

API-тесты с базой требуют `TEST_DB_DSN` и поднятый `postgres`. Без базы они пропускаются: это
не ошибка, но и не проверка слоя API.

## 3. Формат записи

```markdown
- [ ] `T07` analysis: календарь и активные вехи
      спец: … · ждёт: T06 · готово, когда: …
```

| Знак | Значение |
| :--- | :--- |
| `[ ]` | не начата |
| `[~]` | в работе или остановлена; ниже строка «остановился: …» |
| `[x]` | закрыта по DoD и закоммичена |
| `[-]` | снята: не делаем в MVP (раздел 8) |

---

## 4. Задачи человека — параллельно, с первого дня

Агент их не делает, но от них зависят его задачи. Чем раньше, тем лучше.

- [ ] `H1` **(человек)** Демо-хронология. Неподвижных камер в материалах организаторов нет: там
      фото хода строительства с разных точек ([data/README.md](../data/README.md), «Материалы
      организаторов»). Из `ml/datasets/lct-raw/` (или своих снимков) выбрать один объект.
      Каждую точку съёмки завести отдельной «камерой», снимки разложить в
      `data/seed/images/cam-<код>/YYYYMMDD_HHMMSS.jpg` на 3 «дня» по сценарию
      [runbook.md](runbook.md), раздел 6, плюс «нормальный день». Зоны разметить на каждой точке
      (LabelMe или CVAT, метка `ТИП:Название`). Если сценарий не собирается из кадров — поправить
      сценарий, а не кадры. · нужно к: 25.09 · блокирует T27
- [x] `H2` XLSX справочника работ лежит в `data/reference/`, его устройство описано в
      [data/README.md](../data/README.md). 23.09
- [x] `H3` **(человек)** МРР-3.2.81 последней редакции → `data/reference/`: таблицы сроков для
      жилого монолитного дома с номерами пунктов. · нужно к: 25.09 · блокирует T21 — сделано
      агентом по поручению 23.09: `data/reference/МРР-3.2.81-12.htm`, полный текст со страницы,
      указанной в ТЗ (meganorm.ru); редакции новее -12 не найдено. Жилые здания — п. 5.1,
      табл. 1 (п. 5.1.21)
- [ ] `H4` **(человек)** LLM: провайдер, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` в `.env`;
      проверить доступ с демо-машины. · нужно к: 26.09 · для T35
- [ ] `H5` **(человек)** Тестовый набор CV: разметить рамки техники на 100 снимках организаторов
      из `ml/datasets/lct-raw/` (лето, зима, разные стадии) в CVAT или LabelMe →
      `ml/datasets/lct-test/`. Классы — коды из `equipment_classes.yaml`. · нужно к: 27.09 · блокирует T36
- [ ] `H6` **(человек)** Запустить Docker Desktop, проверить GPU:
      `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi`. · нужно к: 24.09
- [ ] `H7` **(человек)** Презентация (слайды 7–11 шаблона без изменения дизайна), видео демо,
      документация .docx/.pdf, загрузка на платформу до 20:00 29.09.

## 5. Сделано ранее

- [x] `A-01` plan-service: каркас, схема `plandb`, миграция `0001`
- [x] `A-02` plan-service: CRUD объектов
- [x] `B-01` site-service: каркас, схема `sitedb`, миграция `0001`
- [x] `C-02` analysis-service: каркас, схема `analysisdb`, миграция `0001`
- [x] `D-01` docker compose, gateway, `.env.example`, Makefile
- [x] `D-02` CI: линт, тесты по сервисам, сборка образов, сверка снапшота OpenAPI, шаблон PR
- [x] vision-service: каркас в compose; web: каркас SPA, сборка в образ gateway
- [x] Документы переписаны под целевую схему (ADR-0011…0014, контракты, методика), 23.09
- [x] Материалы организаторов разложены: README кейса — `docs/official-readme.md`, справочник
      работ и ссылки на датасеты — `data/reference/`, 100 снимков — `ml/datasets/lct-raw/`
      (вне git), 23.09

---

## 6. Задачи по порядку

### R0. Выравнивание кода с документами — 23.09

- [x] `T01` infra: убрать pos-engine и report-service, смонтировать справочные файлы — сделано:
      Makefile, gateway (неизвестный `/api/…` → 404 в конверте ошибки), `.env.example`, том
      `/contracts:ro`; попутно для подъёма стека: MinIO с quay.io, `GATEWAY_PORT`, `.gitattributes`
      (LF для `*.sh`), healthcheck gateway на 127.0.0.1
      спец: [architecture.md](architecture.md) §3, [runbook.md](runbook.md) §4 и §9 · ждёт: —
      что: `Makefile` (`SERVICES`, `NAME_*`, `PORT_*` без pos и report); `services/gateway/nginx.conf`
      и `swagger/index.html` без pos и report; `.env.example` без `POS_URL`, `REPORT_URL`,
      `S3_BUCKET_PREVIEWS`, `SESSION_CLOSE_GRACE_MINUTES`, с `S3_PUBLIC_ENDPOINT`, `CONTRACTS_DIR` и
      переменными методики из runbook §4; том `./packages/contracts:/contracts:ro` у plan, site,
      analysis и vision в `docker-compose.yml`
      готово, когда: `docker compose config` без ошибок; стек поднимается; `/api/v1/pos/…` → 404
- [x] `T02` scripts: скрипты на Python — сделано: `scripts/health.py`, `scripts/fetch_models.py`
      (sha256 обоих файлов сверены, OpenCLIP — с Hugging Face), `_common.py`, заготовки остальных;
      Makefile вызывает `python scripts/…`, `*.sh` удалены
      спец: [scripts/README.md](../scripts/README.md) · ждёт: T01
      что: `health.py` и `fetch_models.py` — полностью (YOLO-World `yolov8s-worldv2` и OpenCLIP
      в `data/models/`); `seed.py`, `demo.py`, `e2e.py`, `contracts.py`, `backup.py`,
      `labelme_to_zones.py` — заготовки, которые печатают «не реализовано, задача Txx» и
      возвращают 1; цели Makefile вызывают `python scripts/…`; `*.sh` и `_not_implemented.sh` удалить
      готово, когда: `python scripts/health.py` печатает сводку по поднятым сервисам
- [x] `T03` plan-service: убрать клиент pos-engine, схема по data-model §1 — сделано:
      `dal/models.py` и миграция `0001` по data-model §1, `plan_version` в API объекта,
      pos-engine удалён из клиентов, конфига и health; 21 тест зелёный в контейнере
      спец: [data-model.md](data-model.md) §1, [ADR-0011](decisions/0011-generator-and-reports-as-modules.md) · ждёт: —
      что: удалить `clients/pos_client.py`, `pos_url`, проверку pos в health, `PosDep`, упоминания
      в комментариях; `object.current_revision` → `plan_version`; `work_calendar.timezone`;
      `stage`: + `visual_stage`, `basis`, − `free_float_days`, `shifts_per_day`, `regulatory_basis`,
      источники `GENERATED/IMPORT/MANUAL`; `stage_rule`: без `zone_type`, `stage_id` уникален,
      `required` — список групп, `signature` — объект; удалить таблицы `equipment_class` и
      `plan_revision`. Миграцию `0001` править на месте: реальных данных нет, после правки
      локально `docker compose down -v`
      готово, когда: тесты plan-service зелёные, включая тест миграций (если есть база)
- [x] `T04` site-service: схема по data-model §2 — сделано: `dal/models.py` и миграция `0001`;
      видимость и факты окна по участку `ТИП:Название`, `session_fact.count > 0`; тесты зелёные
      в контейнере, стек отвечает `/health/ready`
      спец: [data-model.md](data-model.md) §2, [ADR-0012](decisions/0012-facts-without-judgement.md), [ADR-0013](decisions/0013-zones-and-areas.md) · ждёт: —
      что: `camera.reference_image_id`; `zone` без `overlaps_with`; `image.usable`,
      `usable_reason`, без `thumb_key`; `session` без `is_working_time` и `status`, + `stage_label`,
      `stage_conf`, `stage_scores`; `detection`: + `camera_id`, `moved`, `displacement`,
      − `state`, `state_reason`; `stage_observation` без `floors_estimate`;
      `zone_visibility` → `area_visibility`; `session_fact` по `area` со `static`.
      Миграцию `0001` править на месте
      готово, когда: тесты site-service зелёные
- [x] `T05` analysis-service: схема по data-model §3 — сделано: `dal/models.py` и миграция
      `0001`; тест `tests/migrations/test_deviation_key.py` проверяет ключ открытого отклонения
      с `NULLS NOT DISTINCT`; начало и конец прогона — `created_at`/`updated_at`
      спец: [data-model.md](data-model.md) §3 · ждёт: —
      что: `analysis_run` (`as_of`, триггеры `FACTS_UPDATED/PLAN_CHANGED/MANUAL`, `plan_version`,
      `zones_version`, `rerun_requested`, `error`, без `period_*` и `rules_version`); `deviation`
      (`area`, `equipment_class`, `verdict_*`, уникальный индекс по
      `(object_id, stage_id, area, code, equipment_class)` с `NULLS NOT DISTINCT`);
      `stage_fact.facts`; `daily_activity.object_id`; новая `daily_equipment`; `object_status`
      (`as_of`, `confidence`, `stages_at_risk`); удалить `deviation_feedback`. Миграцию `0001`
      править на месте
      готово, когда: тесты analysis-service зелёные
- [x] `T06` analysis: входные модели контрактов, фикстуры демо-дней, чтение enums — сделано:
      `core/inputs.py`, `core/enums.py` (+ `pyyaml`, `CONTRACTS_DIR` в конфиге),
      `tests/factories.py`; факты демо-дней собирает `tests/fixtures/build_fixtures.py`
      (окна 06:00–12:00 UTC), тесты сверяют сценарий дней и значения с `enums.yaml`
      спец: [interservice.md](../packages/contracts/interservice.md) §1–2, [methodology.md](methodology.md), [runbook.md](runbook.md) §6 · ждёт: —
      что: `src/core/inputs.py` — Pydantic-модели «весь план» и «факты за период»
      (`extra="ignore"`); `src/core/enums.py` — чтение `enums.yaml` из `CONTRACTS_DIR` (роли
      типов зон, порядок стадий). `tests/fixtures/`:
      - `plan.json` — пример из interservice §1 с полными UUID;
      - `facts_normal_day.json` (2026-10-19): экскаватор работает, самосвалы видны раз в 2 часа,
        по два за раз → без D2;
      - `facts_day1.json` (2026-10-20): экскаватор в котловане, самосвалов нет весь день → D2;
      - `facts_day2.json` (2026-10-21): появился бетононасос → D3 по будущей вехе «Фундаментная плита»;
      - `facts_day3.json` (2026-10-22): экскаватор неподвижно на въезде, его видит обзорная
        `cam-north` → D4; камера въезда `cam-gate` тёмная весь день → участок «Склад»,
        размеченный только на ней, `BLIND` → D10, а въезд остаётся `PARTIAL` за счёт обзорной камеры.

      Участки — как в примере `data/README.md`: котлован (`cam-north`), въезд (`cam-north` и
      `cam-gate`), склад (только `cam-gate`).

      Окна — рабочие часы 04:00–20:00 UTC (07:00–23:00 МСК), не обязательно каждое.
      Плюс `tests/factories.py`
      готово, когда: все фикстуры разбираются моделями; тест сверяет роли зон с `enums.yaml`

### R1. Методика на фикстурах — 24.09

Всё в `services/analysis-service/src/core/`, чистые функции с unit-тестами.

- [x] `T07` analysis: календарь, рабочие сессии, активные вехи — сделано: `core/calendar.py`
      (рабочая сессия целиком в рабочих часах местного дня, `working_days_between` со знаком
      и обратная ей `add_working_days`), `core/plan_on_date.py`; тесты в `tests/unit/`
      спец: [methodology.md](methodology.md) §2, §8 · ждёт: T06
      что: `core/calendar.py` (рабочие дни, `add/count_working_days`, рабочая сессия по
      `timezone` и `work_hours`); `core/plan_on_date.py` (активные вехи на местную дату, плановая
      визуальная стадия). Даты вех включительно
      готово, когда: тесты на границы дня, выходные, праздник 4 ноября, окно на границе рабочих часов
- [x] `T08` analysis: проверка правила вехи — сделано: `core/rules.py` (`check_rule` →
      группы с числами и доказательствами, `complete` / `partial` / `nothing_required`,
      сигнатура; окно транзитной техники по времени), параметры в `config.py`, допущения в
      README
      спец: [methodology.md](methodology.md) §5 · ждёт: T07
      что: `core/rules.py` — группы `any_of/min`, транзитное окно `TRANSIENT_WINDOW_SESSIONS`,
      `allowed`, сигнатура с `stage_label`, учёт только видимых участков типа вехи
      готово, когда: тесты, включая «нормальный день» — группа самосвалов выполнена через окно
- [x] `T09` analysis: статус техники — сделано: `core/equipment_state.py` (`equipment_states`
      по таблице §6 с обоснованием строкой; `person`, опасные и слепые участки статуса не
      получают); тест на каждую строку таблицы
      спец: [methodology.md](methodology.md) §6 · ждёт: T08
      что: `core/equipment_state.py` по таблице §6 с обоснованием статуса строкой
      готово, когда: тест на каждую строку таблицы для транзитного и нетранзитного класса и для `person`
- [x] `T10` analysis: реестр предикатов, D1, D2, объяснение — сделано: `core/predicates.py`
      (контекст только из рабочих сессий, серии, эскалация, реестр, D1, D2), `core/explain.py`,
      `data/deviation_rules.yaml` с десятью кодами, миграция `0002` (`title_template`);
      контракт дополнен `cameras[].image_ids` для доказательств D1
      спец: [methodology.md](methodology.md) §9, §12 · ждёт: T09
      что: `core/predicates.py` (реестр, ключ отклонения); D1, D2;
      `data/deviation_rules.yaml` — все десять кодов (предикат, серьёзность, `params`, шаблон);
      `core/explain.py` — текст из шаблона и `facts`
      готово, когда: тесты «срабатывает / не срабатывает / граница»; инварианты: без `facts` и
      `evidence` нет отклонения, по слепому участку ничего, кроме D10, вне рабочего времени ничего
- [x] `T11` analysis: D3, D4, D5, D6 — сделано: `core/equipment_predicates.py` (ключ
      «участок × класс», серии по `params.min_sessions`, D3 «возможное опережение» с ключом
      будущей вехи через `params.variants` в `deviation_rules.yaml`), тесты в
      `tests/unit/test_equipment_predicates.py`; допущения — в README сервиса
      спец: [methodology.md](methodology.md) §6, §9 · ждёт: T10
      готово, когда: день 2 → D3 с ключом будущей вехи; день 3 → D4; транзитные классы не дают D4 и D5
- [x] `T12` analysis: фактический старт, активность, загрузка техники, D8, D9, D10 — сделано:
      `core/activity.py` (старт, индекс активности, загрузка техники), `core/context.py`
      (контекст прогона вынесен из реестра, добавлен `as_of`), D8 в `core/predicates.py`,
      D9 и D10 в `core/stage_predicates.py`; «по въезду» ниже — опечатка: въезд `PARTIAL`,
      D10 дня 3 — по складу (как в T06 и T14); D10 без снимков при `NO_IMAGES` — правка
      methodology §12 отдельным коммитом
      спец: [methodology.md](methodology.md) §7, §9, §10.1–10.2 · ждёт: T10
      что: `core/activity.py` — фактический старт по сигнатуре, индекс активности по дням,
      агрегат «загрузка техники по дням»; предикаты D8, D9, D10 (участок и веха без участка)
      готово, когда: день 3 → D10 по въезду; тесты D8 и D9 на синтетике
- [x] `T13` analysis: прогресс, SPI, прогноз, статус объекта, D7 — сделано:
      `core/forecast.py` (прогресс с ограничением по стадии, SPI, прогноз по темпу, перенос
      по FS/SS/FF/SF, `stages_at_risk`, статус и уверенность объекта), D7 в
      `core/stage_predicates.py`; пороги уверенности вынесены в окружение (правка
      methodology §11 отдельным коммитом)
      спец: [methodology.md](methodology.md) §8, §10 · ждёт: T12
      что: `core/forecast.py` — прогресс с ограничением по стадии, плановый прогресс на `as_of`,
      SPI, прогноз, перенос по связям, `stages_at_risk`, статус объекта, `confidence`; D7
      готово, когда: тесты на деление на ноль, полный простой (`MIN_ACTIVITY`), `as_of` в прошлом,
      нехватку данных (`UNKNOWN`)
- [x] `T14` analysis: прогон целиком как чистая функция — сделано: `core/run.py`
      (`analyze` → отклонения с текстами, факт вех, активность, загрузка техники, статус,
      счётчики), тесты `tests/unit/test_run.py`; на четырёх демо-днях подряд объект `DELAY`
      +14 рабочих дней, уверенность MEDIUM. Рубеж R1 пройден
      спец: [analysis-service README](../services/analysis-service/README.md) §4 · ждёт: T11, T12, T13
      что: `core/run.py` — `analyze(plan, facts, as_of, rules) -> AnalysisResult`
      готово, когда: на фикстурах: день 1 → D2, день 2 → D3, день 3 → D4 и D10,
      нормальный день → ни одного D2; повторный вызов даёт тот же результат. **Рубеж R1.**

### R2. Сервисы и сквозной прогон — 25–26.09

- [x] `T15a` analysis: прогон как сервис — сделано: клиенты `src/clients/`, сценарий
      `src/services/runs.py`, сверка ленты `core/ledger.py`, репозитории `dal/repositories/`,
      `POST /runs` и `GET /runs/{id}`, миграция `0003`, `timestamptz` в моделях; 14 api-тестов
      на базе `analysisdb_test`; в стеке правила D1–D10 заполняются при старте. Живой прогон ждёт
      `GET /plan` из T19
      спец: [interservice.md](../packages/contracts/interservice.md) §4, [analysis-service README](../services/analysis-service/README.md) §4 · ждёт: T05, T14
      что: клиенты plan и site (py-common http: 10 с, 2 повтора); `POST /runs` с `?wait=true`
      и фоновым запуском без него; `GET /runs/{id}`; запись результатов (UPSERT по ключу,
      `RESOLVED`); заполнение `deviation_rule` из YAML при первом старте; миграция `0003`
      (`activity_index` nullable)
      готово, когда: api-тесты с клиентами-заглушками на фикстурах; повтор не создаёт дублей
- [x] `T15b` analysis: схлопывание сигналов прогона — сделано: advisory-блокировка объекта,
      `rerun_requested` с атомарным снятием и одним повтором (`services/runs.py`), брошенный
      прогон → `RUN_ABANDONED`, `wait=true` ждёт чужой прогон; 6 api-тестов
      `tests/api/test_run_coalescing.py`
      спец: [interservice.md](../packages/contracts/interservice.md) §4 · ждёт: T15a
      что: на объект один прогон; сигнал во время прогона — `rerun_requested` и ответ
      `coalesced: true` с номером текущего; по окончании ровно один новый прогон
      готово, когда: api-тест: два сигнала подряд → один прогон + один повтор
- [x] `T16a` analysis: статус, прогресс, загрузка техники, настройки правил — сделано:
      роуты `objects.py`, `rules.py`, сценарии `services/results.py`, `services/rules.py`,
      проверка настройки `validate_rule` в `core/explain.py`; `X-Actor` в URL-кодировке
      (api-guidelines §6); 15 api-тестов `test_results.py`, `test_deviation_rules.py`
      спец: [analysis-service README](../services/analysis-service/README.md) §3 · ждёт: T15
      что: `/objects/{id}/status`, `/progress`, `/equipment`; `GET /deviation-rules`,
      `GET/PATCH /deviation-rules/{code}` с проверкой порогов и шаблонов
      готово, когда: api-тест на каждый эндпоинт
- [x] `T16b` analysis: лента отклонений, карточка, объяснение, вердикт — сделано: роут
      `deviations.py`, сценарий `services/deviations.py`, репозиторий с фильтрами и сортировкой
      по порядку серьёзностей из `enums.yaml`; `/explain` с сессиями эпизода от site-service и
      честным `null` без него; 15 api-тестов `tests/api/test_deviations.py`
      спец: [analysis-service README](../services/analysis-service/README.md) §3, [methodology.md](methodology.md) §9, §12 · ждёт: T16a
      что: `/deviations` с фильтрами и пагинацией; `/deviations/{id}`, `/explain`;
      `PATCH /deviations/{id}` (вердикт, `X-Actor`)
      готово, когда: api-тест на каждый эндпоинт
- [x] `T17` plan: справочные файлы и классы техники — сделано: `core/reference.py` (разбор и
      проверка файлов), `src/reference.py` (чтение при старте), `GET /equipment-classes`,
      `check_equipment_codes` → `UNKNOWN_EQUIPMENT_CLASS` для T18; `StrEnum` в схемах заменены
      `Literal` из `enums.yaml`; в контейнере 15 классов, как в файле
      спец: [ADR-0014](decisions/0014-equipment-classes-file.md), [plan-service README](../services/plan-service/README.md) · ждёт: T01, T03
      что: чтение `equipment_classes.yaml` и `enums.yaml` из `CONTRACTS_DIR`;
      `GET /equipment-classes`; проверка кодов классов (`UNKNOWN_EQUIPMENT_CLASS`)
      готово, когда: тесты; в контейнере список классов совпадает с файлом
- [x] `T18a` plan: календари, вехи, сигнал «пересчитай» — сделано: миграция `0002`
      (праздники `moscow-6day` по ТК РФ ст. 112 ч. 1 на 2026–2028, объектам — календарь по
      умолчанию), `/calendars` с проверкой `core/calendar.py`, `GET /objects/{id}/stages` и
      `PATCH /stages/{id}` с проверкой `core/stages.py`, рост `plan_version` и сигнал после
      commit (`services/plan_version.py`, `clients/analysis_client.py`: 2 с, без повторов)
      спец: [plan-service README](../services/plan-service/README.md) §3 · ждёт: T17
      что: календарь `moscow-6day` (часовой пояс `Europe/Moscow`, выходной `[7]`, праздники
      только с источником, для 2026 минимум 4 ноября); `GET /objects/{id}/stages`,
      `PATCH /stages/{id}`; рост `plan_version`; клиент сигнала в analysis (2 с, без повторов,
      ошибки — в лог)
      готово, когда: api-тесты; правка вехи и календаря увеличивает `plan_version` и шлёт сигнал
- [x] `T18b` plan: правила «веха → техника» — сделано: `/rules` (список с фильтрами, создание,
      правка, удаление), проверка формы `core/stage_rules.py` и кодов по
      `equipment_classes.yaml`, версия правила растёт в SQL, `plan_version` и сигнал через
      `services/plan_version.py`; правило в ответе вех; `X-Actor` в журнал
      спец: [plan-service README](../services/plan-service/README.md) §3, [interservice.md](../packages/contracts/interservice.md) §1 · ждёт: T18a
      что: CRUD `/rules` в новом формате (группы `any_of`/`min`, `allowed`, `signature`,
      `min_sessions`), коды классов — `check_equipment_codes`; версия правила и `plan_version`
      растут; правило в ответе `GET /objects/{id}/stages`
      готово, когда: api-тесты; правка правила увеличивает `plan_version` и шлёт сигнал (заглушка)
- [x] `T19a` plan: «весь план» и критический путь — сделано: `core/cpm.py` (обратный проход
      по номерам рабочих дней, FS/SS/FF/SF с лагом, отрицательный резерв при нарушенных
      связях), `GET /objects/{id}/plan` по контракту 1 (выключенное правило — `rule: null`),
      пересчёт резервов после правки дат вехи и календаря (`services/critical_path.py`)
      спец: [interservice.md](../packages/contracts/interservice.md) §1 · ждёт: T18
      что: `GET /objects/{id}/plan` строго по контракту (календарь объекта — `calendar_id`);
      `core/cpm.py`; `PATCH /stages/{id}` после правки дат пересчитывает критический путь;
      правило с `is_active: false` — решить и записать в README
      готово, когда: api-тест сверяет форму `/plan` с контрактом; unit-тесты CPM
- [x] `T19b` plan: шаблон вех жилого монолита и импорт графика — сделано:
      `data/wbs_templates.json` (12 вех по ТЗ §5.2, проверка при старте `core/templates.py`),
      `core/plan_import.py` (CSV/XLSX, шаблон заполняет недостающее, ошибки всех строк с
      номерами, код из даты Excel), `POST /objects/{id}/plan/import` с `force`; демо-график
      `tests/fixtures/demo_schedule.csv` даёт `/plan` со значениями фикстуры T06; в стеке
      analysis забирает импортированный план (прогон падает на фактах site — ждёт T26)
      спец: [ТЗ §3, §5.2](<ТЗ Мониторинг строительной площадки по снимкам камер (ЛЦТ 2026, кейс 07).md>) · ждёт: T19a
      что: `POST /objects/{id}/plan/import` (CSV/XLSX: код, наименование, начало, окончание;
      необязательно тип участка, визуальная стадия, связи); проверка дат и циклов.
      `data/wbs_templates.json`: вехи жилого монолита с типом участка, визуальной стадией,
      связями и правилами по таблице ТЗ §5.2, включая группы «любой из». Доли фаз пока
      `null` — их заполнит T21
      готово, когда: ответ `/plan` на демо-графике совпадает по форме с `tests/fixtures/plan.json`
      из T06; импорт с ошибкой возвращает номер строки
- [x] `T20` plan: парсер справочника работ — сделано: `core/reference_import.py` (коды из
      дат и чисел, точка в конце, строки без кода — `<родитель>/<n>` 4-го уровня, отметки по
      столбцам шапки, ошибки всех строк), `POST /work-types/import` (замена целиком),
      `GET /work-types` в порядке файла; на настоящем файле 377 строк, 250 без кода, 19 кодов
      восстановлены — тестом и в стеке
      спец: [plan-service README](../services/plan-service/README.md) §4 · ждёт: T03
      что: `core/reference_import.py` по описанию файла в [data/README.md](../data/README.md):
      коды из дат Excel (`d.m.2025` → `d.m`), код-число, точка в конце кода, строки без кода,
      отметка `˅` в девяти столбцах типов объектов; `POST /work-types/import`, `GET /work-types`
      готово, когда: unit-тесты на крайних случаях; на настоящем файле из `data/reference/`
      разобраны все 377 строк данных, 19 испорченных кодов восстановлены
- [x] `T21a` plan: нормы МРР и генератор графика как чистая функция · **режется первым** —
      сделано: `data/mrr_norms.json` (32 строки табл. 1, тест сверяет каждое число с HTML МРР),
      `core/mrr_norms.py`, `core/schedule_generator.py`, доли и `piles` в шаблоне; демо-объект —
      12 вех с 21.09.2026 по 19.06.2027, у каждой `basis` со ссылкой на пункт; месяцы МРР
      откладываются по обычному календарю (`add_months`). Кст = 1,1 для монолита в МРР есть
      только у школ и больниц, жильё считается без поправки (README §4); московских норм
      свежее МРР-3.2.81-12 поиск 24.09 не нашёл
      спец: [plan-service README](../services/plan-service/README.md) §4 · ждёт: T19, H3
      что: `data/mrr_norms.json` (табл. 1 п. 5.1.21, интерполяция и экстраполяция п. 4.9 и
      5.1.3–5.1.4, сменность п. 4.10, сваи п. 5.1.6; у каждого числа `source`), доли вех в
      `wbs_templates.json`, `core/schedule_generator.py` (фазы → вехи → даты по календарю)
      готово, когда: unit-тесты: 17 этажей, 10 000 м² → 8,7 мес. = 1,0 + 1,5 + 4,7 + 1,5 (ТЗ §8);
      интерполяция, экстраполяция и её пределы, сменность, сваи; ни одного числа без источника
- [x] `T21b` plan: `POST /objects/{id}/plan/generate` · **режется первым** — сделано:
      `services/plan_generate.py`, запись графика вынесена из импорта в
      `services/plan_writer.py`, нормы сверяются с шаблоном при старте
      (`check_generator_template`), коды `NORMS_NOT_AVAILABLE` и `GENERATOR_PARAMS_INVALID`;
      5 api-тестов; в стеке демо-объект — 12 вех, 21.09.2026–21.06.2027 по `moscow-6day`
      спец: [plan-service README](../services/plan-service/README.md) §4 · ждёт: T21a
      что: сценарий и роут (`force`, `NORMS_NOT_AVAILABLE`), запись вех и правил как при
      импорте, критический путь, `plan_version` и сигнал; README
      готово, когда: api-тест; график демо-объекта строится в стеке
- [x] `T22a` site: привязка к зонам как чистая функция — сделано: `core/zones.py`
      (точка контакта, основная зона — наименьшая не опасная, опасные поверх по роли `SAFETY`,
      граница — внутри, `check_polygon`), `core/reference.py` (типы и роли зон из `enums.yaml`),
      `shapely` и `pyyaml` в зависимостях; 18 unit-тестов; тестовая база `sitedb_test`
      спец: [methodology.md](methodology.md) §3, [ADR-0013](decisions/0013-zones-and-areas.md) · ждёт: T01, T04
      что: `core/zones.py` (точка контакта, основная зона, опасные поверх, ключ участка,
      проверка полигона; `shapely`); `core/reference.py` — типы зон и их роли из `enums.yaml`
      готово, когда: unit-тесты: граница, перекрытие, опасная зона поверх рабочей, вне зон
- [x] `T22b` site: API камер и зон — сделано: `/cameras`, `/zones` (CRUD, деактивация с
      ростом версии), `POST /zones/import` (сверка по коду камеры и подписи участка,
      повтор ничего не меняет, ошибки полигонов с путём), `GET /objects/{id}/areas` с
      `zones_version`; названия типов зон — `zone_type_name` в `enums.yaml` (отдельный коммит);
      7 api-тестов, демо-разметка даёт въезд на `cam-north` и `cam-gate`
      спец: [site-service README](../services/site-service/README.md) §3 · ждёт: T22a
      что: CRUD `/cameras` и `/zones`; `POST /zones/import` из формата `data/seed/cameras.json`;
      `zones_version`
      готово, когда: api-тесты; импорт демо-камер из data/README.md даёт участки въезда на двух камерах
- [x] `T23a` site: время снимка, метаданные кадра, окно сессии — чистые функции — сделано:
      `core/timestamp.py` (проверка правдоподобия, смещение EXIF главнее пояса камеры),
      `core/image_meta.py` (формат по содержимому, EXIF из Exif IFD), `core/sessions.py`,
      `CAMERA_TIMEZONE`, `timestamptz` в моделях site; 23 unit-теста
      спец: [site-service README](../services/site-service/README.md) §4 · ждёт: T22
      что: `core/timestamp.py` (EXIF → имя файла → поле формы → `NEEDS_TIME`; наивное время —
      в `CAMERA_TIMEZONE`), `core/image_meta.py` (размер, EXIF, формат; Pillow),
      `core/sessions.py` (окно 30 мин по :00 и :30 UTC); `timestamptz` в моделях (раздел 9)
      готово, когда: unit-тесты времени, включая нестандартные имена файлов и EXIF со смещением
- [ ] `T23b` site: загрузка снимков в MinIO
      спец: [api-guidelines.md](api-guidelines.md) §7, §8 · ждёт: T23a
      что: `POST /images` (до 200 файлов, частичный успех `202`) и `/images/import` (камера из
      подпапки, заводится автоматически, первый снимок — эталонный кадр); sha256; MinIO;
      привязка к окну; MinIO в `/health/ready`
      готово, когда: api-тест частичного успеха пакета
- [ ] `T23c` site: список, карточка снимка, ручное время
      ждёт: T23b
      что: `GET /images`, `GET /images/{id}` со ссылкой на `S3_PUBLIC_ENDPOINT`;
      `PATCH /images/{id}` для `NEEDS_TIME`
      готово, когда: api-тесты
- [ ] `T24` vision: распознавание
      спец: [interservice.md](../packages/contracts/interservice.md) §3, [vision-service README](../services/vision-service/README.md) · ждёт: T01
      что: `POST /analyze` (YOLO-World с промптами из `equipment_classes.yaml`; OpenCLIP с
      метками из `data/stage_prompts.yaml`; яркость и размытость), `GET /model`, устройство по
      `VISION_DEVICE`, веса из `/models`; образ с torch — если сборка CUDA-образа идёт дольше
      20 минут, сначала CPU-вариант
      готово, когда: тесты постобработки на модели-заглушке; снимки из `ml/datasets/lct-raw/`
      распознаются в контейнере; время на снимок (CPU, GPU при H6) записано в README vision, §8
- [ ] `T25` site-worker: конвейер распознавания и факт окна
      спец: [methodology.md](methodology.md) §4, [site-service README](../services/site-service/README.md) §4 · ждёт: T23, T24
      что: `src/worker.py` (arq), задача `analyze_image`; клиент vision (30 с, 2 повтора);
      `core/movement.py`; `core/aggregation.py` (максимум по камерам, `static`, видимость
      участков, `OUTSIDE`, стадия за окно); сигнал в analysis; контейнер `site-worker` в compose
      готово, когда: unit-тесты агрегации; загруженный снимок доходит до `ANALYZED`, факт окна
      появляется
- [ ] `T26` site: «факты за период» и пересчёты
      спец: [interservice.md](../packages/contracts/interservice.md) §2 · ждёт: T25
      что: `GET /objects/{id}/facts` строго по контракту, включая `cameras[].image_ids`
      (добавлено 23.09 для доказательств D1); `/sessions`, `/sessions/{id}`;
      `POST /zones/reapply`; `POST /images/reanalyze`
      готово, когда: ответ совпадает по форме с фикстурами T06; правка зоны пересчитывает факты
- [ ] `T27` scripts: `seed.py` и `labelme_to_zones.py`
      спец: [scripts/README.md](../scripts/README.md), [data/README.md](../data/README.md) · ждёт: T16, T19, T26, H1
      что: объект → импорт `data/seed/schedule.xlsx` → зоны из `cameras.json` → загрузка
      снимков → ожидание распознавания → `POST /analysis/runs?wait=true` → сводка
      готово, когда: на чистом стеке (`docker compose down -v` → `up`) `python scripts/seed.py`
      даёт отклонения в `GET /analysis/deviations`
- [ ] `T28` scripts: `e2e.py` и `demo.py`
      спец: [runbook.md](runbook.md) §6, [testing.md](testing.md) · ждёт: T27
      готово, когда: `python scripts/e2e.py` находит D2, D3, D4, D10 на своих днях и не находит D2
      в «нормальный день». **Рубеж R2.**

### R3. Интерфейс, отчёт, качество — 27.09

- [ ] `T29` web: типы API, объекты, дашборд
      спец: [apps/web/README.md](../apps/web/README.md) · ждёт: T16, T19
      что: `scripts/contracts.py` (снапшоты OpenAPI + TS-типы в `packages/ts-api-client`);
      экраны «Объекты» и «Дашборд»: статус, SPI, уверенность, счётчики, вехи в риске
      готово, когда: `npm run build`; экраны показывают данные после `seed.py`
- [ ] `T30` web: лента предупреждений и карточка
      ждёт: T29
      что: лента с фильтрами; карточка: текст, числа из `facts`, правило, снимок с рамками
      (SVG поверх), `/explain`, кнопки «подтвердить / ложное»
      готово, когда: на демо-данных у D2 видны числа и снимок с рамкой экскаватора
- [ ] `T31` web: редактор правил «веха → техника» · **не режется**
      ждёт: T29, T18
      что: группы «любой из» с минимумом, допустимая техника, сигнатура, `min_sessions`;
      сохранение → пересчёт → обновление ленты
      готово, когда: минимум самосвалов 2 → 1 — D2 исчезает из ленты без перезагрузки стека
- [ ] `T32` web: Гант план-факт
      ждёт: T29
      что: плановые полосы, фактический старт, прогнозный хвост, критический путь; правка дат
      формой (перетаскивание — по желанию); выбранная библиотека записана в README web
      готово, когда: правка даты вехи пересчитывает прогноз
- [ ] `T33` web: просмотр камеры
      ждёт: T29, T26
      что: снимок, полигоны зон, рамки детекций, переключение камер и окон
      готово, когда: на демо-данных видны зоны и рамки
- [ ] `T34` analysis: PDF-отчёт и экран отчётов
      спец: [analysis-service README](../services/analysis-service/README.md) §5 · ждёт: T16
      что: `src/report/` (Jinja2 → WeasyPrint, восемь разделов, SVG-графики, снимки с рамками);
      `/reports`; в web — список отчётов и кнопка «сформировать»
      готово, когда: PDF по демо-объекту формируется, раздел «Ограничения» заполнен
- [ ] `T35` analysis: резюме по фактам
      спец: [ADR-0008](decisions/0008-llm-narrative-only.md), [analysis-service README](../services/analysis-service/README.md) §5 · ждёт: T34
      что: `POST /summary`; сборка контекста; `prompts/summary.ru.md`; клиент
      OpenAI-совместимого API; валидатор чисел; шаблонное резюме
      готово, когда: тесты валидатора; при `LLM_ENABLED=false` резюме шаблонное; с ключом из H4 —
      LLM-текст со ссылками на ID отклонений
- [ ] `T36` ml: метрики распознавания
      спец: [ml/README.md](../ml/README.md), [testing.md](testing.md) §7 · ждёт: T24, H5
      что: `ml/eval/evaluate.py`; таблица precision / recall / mAP50 по классам и матрица ошибок
      в `docs/metrics.md` с размером выборки и условиями съёмки
      готово, когда: метрики посчитаны на наборе H5; ничего не выдумано
- [ ] `T37` docs: актуализация к сдаче
      ждёт: T28, T31
      что: статусы в `traceability.md`; README и runbook сверены с реальным поведением; раздел
      ограничений; линт и тесты всех сервисов зелёные
      готово, когда: человек может пройти runbook §2 с нуля без вопросов. **Рубеж R3.**

### Сдача — 28.09

- [ ] `T38` release: репетиция на чистом стенде
      спец: [runbook.md](runbook.md) §10 · ждёт: T37
      что: тег → образы в ghcr → на стенде `docker compose down -v`, `pull`, `up`, `seed.py`,
      `e2e.py` → демо по runbook §6 с секундомером; дальше только исправление блокеров
      готово, когда: сценарий проходит за 5 минут без ручных правок

## 7. После R3, если осталось время

- [ ] `T39` web: экран загрузки снимков с ручным вводом времени для `NEEDS_TIME` · ждёт: T29, T23
- [ ] `T40` web: редактор зон на эталонном кадре (F11, Could) · ждёт: T33
- [ ] `T41` ml: дообучение YOLO11s на проверенной авторазметке (гибрид из ml/README) · ждёт: T36

## 8. Снято в MVP

- [-] Второй тип объекта «дорога» — глубина важнее ширины (ТЗ, таблица Q&A).
- [-] Профиль `llm` с локальной Ollama — внешний API и шаблон закрывают F12.
- [-] XLSX-отчёты и экспорт графика — в ТЗ только PDF.
- [-] История правок плана (`plan_revision`) — вместо неё `plan_version`.

## 9. Замечено по ходу (не в рамках текущих задач)

Сюда агент записывает найденное попутно: баг, противоречие, долг. Одна строка — одна находка,
со ссылкой на файл. Человек решает, превращать ли её в задачу.

- `docker-compose.yml`: якорь `service-base` с `env_file: [.env]` передаёт каждому контейнеру
  все переменные, включая DSN с паролями чужих баз. Это расходится с runbook §9 («ни один
  контейнер не знает пароля от чужой базы»). Нужно убрать `env_file` и перечислить переменные
  каждого сервиса в `environment`.
- `scripts/backup.py` (`make backup`, runbook §8) не закреплён ни за одной задачей: сейчас это
  заготовка.
- YOLO-World в Ultralytics для `set_classes`, насколько известно, берёт текстовый энкодер CLIP
  и при первом вызове качает его из интернета (не проверено запуском). Для работы без сети в контейнере `vision-service` его тоже нужно
  положить в `data/models/` — проверить в T24.
- Раздел 2 этого файла: `pytest -q` на хосте не работает — нет `lct_common`, `pytest-asyncio`
  и зависимостей сервиса. Рабочий способ (T03): одноразовый контейнер из образа сервиса в сети
  `lct_lct` с каталогом сервиса, смонтированным в `/app/services/<сервис>`, `pip install pytest
  pytest-asyncio`, `TEST_DB_DSN` на `postgres:5432`. Стоит записать в §2 или в `scripts/`.
  Для analysis-service ещё смонтировать `packages/contracts` в `/app/packages/contracts`.
- `services/plan-service/src/dal/models.py`: поля `Mapped[datetime]` без
  `DateTime(timezone=True)`, хотя колонки в миграциях — `timestamptz`. SQLAlchemy шлёт момент
  как наивный `TIMESTAMP`, и запись момента с часовым поясом падает (`can't subtract
  offset-naive and offset-aware datetimes`); в analysis это исправлено в T15a, в site — в T23a
  тем же `type_annotation_map` в `Base`. plan сам моменты пока не пишет, поэтому не падает.
- ~~`services/plan-service/src/api/schemas/common.py` дублирует в коде списки `object_type`,
  `construction_phase`, `zone_type` и др. в виде `StrEnum`, что запрещено AGENTS.md §7.~~
  Закрыто в T17: типы строятся из `enums.yaml`.
