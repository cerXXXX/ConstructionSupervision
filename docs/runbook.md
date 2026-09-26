# Запуск, конфигурация и эксплуатация

---

## 1. Требования

| Что | Версия | Зачем |
| :--- | :--- | :--- |
| Docker + Docker Compose | 24+ / v2; на Windows — Docker Desktop с бэкендом WSL2 | Единственный обязательный способ запуска |
| Python | 3.12 | Скрипты `scripts/*.py`, локальные тесты сервисов |
| ruff | **0.16.8** (как в `requirements-dev.txt`) | Линт. Другая версия ruff проверяет по другим правилам |
| Node.js | 20+ | Локальная разработка фронтенда |
| GNU Make + bash | любая | Удобные обёртки. На Windows без bash не работают — раздел 3 |
| Оперативная память | 8 ГБ минимум, 16+ комфортно | CV-сервис + Postgres + MinIO + воркеры |
| Диск | ~20 ГБ | Образ с CUDA весит несколько гигабайт, плюс остальные образы, веса и демо-снимки |
| GPU | NVIDIA, 4+ ГБ VRAM | Не обязателен, но целевой стенд — с ним |

**Целевой стенд:** ноутбук Ryzen 5 5600H, 32 ГБ, RTX 3060 Laptop 6 ГБ, Windows 10, Docker Desktop.

**GPU в Docker на Windows.** Docker Desktop с бэкендом WSL2 пробрасывает видеокарту сам. Нужен
только свежий драйвер NVIDIA для Windows, а `nvidia-container-toolkit` отдельно не ставится.
Проверка:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

Без GPU система работает целиком, но распознавание идёт секунды вместо миллисекунд. Для
отладки этого достаточно, для показа нет.

Карту в `vision-service` пробрасывает оверлей `docker-compose.gpu.yml` (раздел 5). На стенде
с картой стек поднимается так:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

Фактическое устройство показывает `GET /api/v1/vision/model` (поле `device`).

## 2. Первый запуск

```bash
cp .env.example .env               # при необходимости поменять пароли и ключ API
python scripts/fetch_models.py     # веса детектора, OpenCLIP и текстового CLIP в data/models
docker compose up -d --build       # весь стек
python scripts/seed.py             # демо-объект, график, камеры, зоны, снимки, прогон анализа
```

| Адрес | Что |
| :--- | :--- |
| <http://localhost:8080> | Интерфейс |
| <http://localhost:8080/docs> | Сводный Swagger с выбором сервиса |
| <http://localhost:8001/docs> … <http://localhost:8004/docs> | Swagger отдельных сервисов |
| <http://localhost:9001> | Консоль MinIO |

## 3. Команды

Все скрипты проекта написаны на Python и работают одинаково в Linux, macOS и Windows. Цели
`Makefile` — короткие обёртки над теми же командами. Их рецепты требуют bash, поэтому на Windows
(`make` из Chocolatey запускает рецепты через cmd) пользуйтесь правым столбцом.

| `make` | PowerShell (Windows) | Что делает |
| :--- | :--- | :--- |
| `make up` / `make down` | `docker compose up -d --build` / `docker compose down` | Поднять / остановить стек |
| `make pull` | `docker compose pull` | Забрать опубликованные образы из ghcr вместо локальной сборки |
| `make restart s=site` | `docker compose restart site-service` | Перезапустить один сервис |
| `make logs s=analysis f=1` | `docker compose logs -f --tail=200 analysis-service` | Логи сервиса |
| `make ps` | `docker compose ps` | Состояние контейнеров |
| `make health` | `python scripts/health.py` | Опросить `/health/ready` всех сервисов |
| `make seed` | `python scripts/seed.py` | Загрузить демо-данные и прогнать анализ |
| `make demo` | `python scripts/demo.py` | Сценарий показа: четыре дня объекта с заложенными отклонениями, ссылки на снимки |
| `make reset` | `docker compose down -v` | Полная очистка: тома БД, бакеты MinIO, очередь |
| `make test s=plan` | `cd services/plan-service; $env:PYTHONPATH='.'; pytest -q; cd ../..` | Тесты одного сервиса |
| `make lint` | `ruff check --config tools/ruff.toml packages services scripts; ruff format --check --config tools/ruff.toml packages services scripts` | Линт и проверка формата |
| `make fmt` | `ruff format --config tools/ruff.toml packages services scripts` | Автоформатирование |
| `make e2e` | `python scripts/e2e.py` | Сквозной сценарий на поднятом стеке |
| `make contracts` | `python scripts/contracts.py` | Пересобрать снапшоты OpenAPI и TS-клиент |
| `make migrate s=plan m="…"` | `cd services/plan-service; $env:PYTHONPATH='.'; alembic revision --autogenerate -m "…"` | Создать миграцию Alembic |
| `make models` | `python scripts/fetch_models.py` | Скачать веса моделей |
| `make dev` | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build` | Стек с hot-reload |
| `make backup` | `python scripts/backup.py` | Дамп баз и зеркало бакетов MinIO |

Если локальный ruff другой версии: `python -m pip install ruff==0.16.8`. Если установка из
сессии агента не видна в терминале пользователя (Windows Store Python хранит пакеты отдельно),
установку делает человек.

## 4. Переменные окружения

Один `.env` в корне на весь compose. Секции — по назначению.

### Общие

| Переменная | По умолчанию | Смысл |
| :--- | :--- | :--- |
| `ENV` | `dev` | `dev` / `prod`: влияет на подробность логов и показ `/docs` |
| `LOG_LEVEL` | `INFO` | |
| `API_KEY` | `dev-key-change-me` | Ключ для `X-API-Key`; в проде обязателен к замене |
| `TZ` | `Europe/Moscow` | Отображение времени; хранение всегда UTC |
| `RUN_MIGRATIONS` | `true` | Применять Alembic при старте контейнера |
| `CONTRACTS_DIR` | `/contracts` | Куда смонтирован `packages/contracts` (классы техники, перечисления) |
| `GATEWAY_PORT` | `8080` | Внешний порт gateway; поменять, если 8080 на машине занят |

### Образы

| Переменная | По умолчанию | Смысл |
| :--- | :--- | :--- |
| `IMAGE_REGISTRY` | `ghcr.io/cerxxxx/constructionsupervision` | Откуда `make pull` тянет образы (раздел 10) |
| `IMAGE_TAG` | `latest` | Версия образов: `latest` или тег релиза, например `v0.2.0` |

### Базы данных

| Переменная | По умолчанию |
| :--- | :--- |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `postgres` / `5432` |
| `POSTGRES_SUPERUSER` / `POSTGRES_PASSWORD` | `postgres` / задаётся в `.env` |
| `PLAN_DB_DSN` | `postgresql+asyncpg://plan_user:***@postgres:5432/plandb` |
| `SITE_DB_DSN` | `postgresql+asyncpg://site_user:***@postgres:5432/sitedb` |
| `ANALYSIS_DB_DSN` | `postgresql+asyncpg://analysis_user:***@postgres:5432/analysisdb` |

Базы и роли создаются один раз скриптом инициализации Postgres (`infra/postgres/init/`). Роль
имеет права только на свою базу — граница сервисов защищена самой СУБД.

### Хранилище и очередь

| Переменная | По умолчанию | Смысл |
| :--- | :--- | :--- |
| `S3_ENDPOINT` | `http://minio:9000` | MinIO внутри сети Docker |
| `S3_PUBLIC_ENDPOINT` | `http://localhost:9000` | Адрес MinIO для браузера: на него подписываются ссылки, которые открывает интерфейс |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | задаются в `.env` | |
| `S3_BUCKET_IMAGES` / `S3_BUCKET_REPORTS` | `images` / `reports` | |
| `S3_PRESIGN_TTL_S` | `3600` | Срок жизни ссылок |
| `REDIS_URL` | `redis://redis:6379/0` | Очередь задач site-worker |

### Адреса сервисов

| Переменная | По умолчанию |
| :--- | :--- |
| `PLAN_URL` | `http://plan-service:8000` |
| `SITE_URL` | `http://site-service:8000` |
| `ANALYSIS_URL` | `http://analysis-service:8000` |
| `VISION_URL` | `http://vision-service:8000` |

### Компьютерное зрение

| Переменная | По умолчанию | Смысл |
| :--- | :--- | :--- |
| `VISION_DEVICE` | `cuda` | `cuda` на демо-стенде, `cpu` — запасной путь |
| `VISION_DET_WEIGHTS` | `/models/yolov8s-worldv2.pt` | Веса детектора; дообученные подставляются сюда же |
| `VISION_DET_CONF` | `0.35` | Порог уверенности |
| `VISION_DET_IMGSZ` | `1280` | Размер входа |
| `VISION_STAGE_MODEL` | `openclip-vit-b32` | Классификатор стадии |

### Конвейер и методика

| Переменная | По умолчанию | Смысл |
| :--- | :--- | :--- |
| `SESSION_WINDOW_MINUTES` | `30` | Длина окна сессии |
| `MAX_IMAGE_MB` | `20` | Предел размера снимка |
| `WORKER_CONCURRENCY` | `4` | Параллельных задач в воркере |
| `MOVE_THRESHOLD` | `0.01` | Смещение (доля диагонали кадра), с которого единица считается сдвинувшейся |
| `MIN_BRIGHTNESS` / `MAX_BLUR` | `0.15` / `0.6` | Пригодность кадра |
| `TRANSIENT_WINDOW_SESSIONS` | `4` | Окно присутствия транзитной техники |
| `MIN_STAGE_CONF` | `0.5` | Порог уверенной стадии по фото |
| `MIN_ACTIVITY` | `0.1` | Нижняя граница темпа в прогнозе |
| `ON_TRACK_TOLERANCE_DAYS` | `2` | Порог статуса «в графике» |

Пороги отклонений D1–D10 живут в таблице `deviation_rule` и правятся в интерфейсе; начальные
значения — `services/analysis-service/data/deviation_rules.yaml`.

### LLM

| Переменная | По умолчанию | Смысл |
| :--- | :--- | :--- |
| `LLM_ENABLED` | `true` | `false` → шаблонные резюме без модели |
| `LLM_PROVIDER` | `openai_compatible` | `openai_compatible` (по умолчанию) / `ollama` для закрытого контура |
| `LLM_BASE_URL` | — | Адрес провайдера |
| `LLM_API_KEY` | — | **Настоящий секрет.** Только в `.env`, никогда в git |
| `LLM_MODEL` | — | Имя модели у провайдера |
| `LLM_TIMEOUT_S` | `30` | По истечении — шаблонное резюме |

LLM внешняя: видеопамять полностью отдана распознаванию. Наружу уходят только
структурированные факты — названия вех, даты, числа, коды отклонений; ни снимков, ни
персональных данных. Прямой доступ к OpenAI и Anthropic из РФ без прокси не работает:
провайдера нужно проверить **с той машины, на которой будет демонстрация**, заранее.

## 5. Профили и оверлеи compose

Разработка — это **оверлей**, а не профиль: отдельный файл `docker-compose.dev.yml` поверх
основного. Он добавляет hot-reload и монтирование исходников; `packages/py-common` намеренно
не монтируется — его правка требует пересборки образа, иначе получается «работает только у меня».

| Профиль | Что добавит | Когда | Состояние |
| :--- | :--- | :--- | :--- |
| `llm` | Ollama + загрузка модели | Закрытый контур без внешнего API | появится вместе с резюме |
| `gpu` | `vision-service` с пробросом видеокарты | Целевой стенд | сделан **оверлеем** `docker-compose.gpu.yml`: профиль добавляет сервисы, но не дополняет описанный |

## 6. Демо-сценарий (5 минут)

`python scripts/demo.py` готовит данные и ведёт по шагам ниже: по каждому дню печатает, что
рассказать, найденные отклонения и ссылки на снимки-доказательства в интерфейсе. Ожидаемые
отклонения — `data/seed/expected.json`; `python scripts/e2e.py` проверяет, что лента с ними
совпадает.

Объект — монолитный каркас на кадрах датасета Лимы ([data/README.md](../data/README.md)): две
камеры, обзорная `cam-torre-h` и наземная `cam-d3`, демо-дни 19–22.10.2026. По графику идёт
надземная часть: каркас 12.4.4 (правило ТЗ: башенный кран) и с 21.10 — бетонирование колонн и
перекрытий 12.4.10 (миксер и бетононасос). Участки: «Пятно застройки» на обеих камерах, «Въезд»
(дорога вдоль корпуса) на Torre H, «Склад» (навесы) только на D3.

1. **График.** Импорт графика из XLSX (или генерация по МРР из типа и параметров объекта):
   вехи, даты, критический путь, правила «веха → техника».
2. **19.10 — нормальный день.** Кран на каркасе, погрузчики и самосвалы на въезде. D2 нет.
   Погрузчик у въезда даёт **D4 «простой»**: по методике нетранзитная машина на служебном
   участке простаивает (methodology.md, раздел 6).
3. **20.10 — простой и чужая техника.** Погрузчики весь день на месте: у въезда и на пятне
   застройки → **D4**. Погрузчика нет в правилах вех каркаса → **D3 «техника не по этапу»**.
   Кран стоит на месте, но простоем не считается: он работает стоя.
4. **21.10 — бетонирование и слепой участок.** По графику бетонирование, а с утра нет ни
   миксера, ни насоса → **D1**. С 11:00 приходят миксеры, насоса нет → **D2 «неполный
   комплект»**: бетон ждёт насоса. Открываем карточку: правило, числа, снимок с рамками.
   Камера D3 закрыта → склад, который видит только она, получает **D10 «участок вне контроля
   ИИ, проверить вручную»**. Пятно застройки при этом видно частично, с Torre H: наглядный плюс
   нескольких камер на участок.
5. **22.10 — комплект полный.** Миксер и насос на месте, D2 закрыт. Насос стоит на опорах весь
   день, но работает стоя: простоя нет.
6. **Гант.** Фактический старт, прогноз окончания, задержка, перенос на зависимые вехи.
7. **Отчёт.** PDF с планом-фактом, загрузкой техники и LLM-резюме со ссылками на ID отклонений.
8. **Правка правила.** Дашборд → «Правила» → веха 12.4.10: убираем из обязательной техники
   группу «бетононасос» (бетон можно подавать краном в бадье) → «Сохранить и пересчитать» →
   экран сообщает, что D2 исчез из ленты, утреннее D1 остаётся. Вернули группу — D2 вернулся. Это демонстрация главного архитектурного тезиса:
   логика — данные, а не код. Проверено через API 26.09 на свежем объекте.

## 7. Диагностика

| Симптом | Причина | Что делать |
| :--- | :--- | :--- |
| `vision-service` не готов | Не скачаны веса | `python scripts/fetch_models.py`, затем `docker compose restart vision-service` |
| Снимки остаются в статусе `PENDING` | Воркер не поднялся или недоступен Redis | `docker compose logs site-worker`, проверить `REDIS_URL` |
| Снимки в статусе `NEEDS_TIME` | Нет EXIF и время не распознано из имени файла | Указать время при загрузке или переименовать по шаблону `YYYYMMDD_HHMMSS.jpg` |
| Анализ не находит отклонений | Нет активных вех на дату снимков, не размечены зоны или участок невидим | Проверить `GET /api/v1/plan/objects/{id}/plan`, зоны камер и `as_of` прогона |
| Все участки `BLIND` | Зоны не размечены или кадры непригодны | Проверить `data/seed/cameras.json` и `usable` у снимков |
| Снимки не открываются в браузере | Ссылка подписана на внутренний адрес MinIO | Проверить `S3_PUBLIC_ENDPOINT` (`http://localhost:9000`) |
| Отчёт без LLM-резюме | Нет сети, неверный ключ или таймаут | Проверить `LLM_BASE_URL` и `LLM_API_KEY`; `LLM_ENABLED=false` — резюме станет шаблонным |
| Распознавание идёт на CPU, хотя есть карта | Docker не видит GPU | `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi`; обновить драйвер NVIDIA; проверить `GET /api/v1/vision/model` |
| `make` пишет `'grep' is not recognized` | Windows: рецепты Makefile исполняет cmd | Команды из правого столбца раздела 3 |
| Повторная загрузка того же файла в `rejected` | Защита от дублей по sha256 | Это не ошибка |

**Куда смотреть в первую очередь:** `request_id` из ответа об ошибке —
`docker compose logs | Select-String <request_id>` (PowerShell) или `| grep <request_id>` (bash)
показывает всю цепочку вызовов через все сервисы.

## 8. Резервное копирование и перенос

- Данные: тома `pgdata` (три базы) и `miniodata`.
- Логический дамп: `python scripts/backup.py` → `backup/YYYY-MM-DD/{plandb,sitedb,analysisdb}.sql`
  + зеркало бакетов MinIO.
- Перенос к заказчику: те же образы, свой `.env`, свои адреса Postgres и S3.
  Ничего, кроме переменных окружения, менять не требуется.

## 9. Состав docker-compose

Один файл `docker-compose.yml` на весь стек, оверлей `docker-compose.dev.yml` для разработки.
Порядок запуска задаётся через `depends_on: condition: service_healthy`. Файлы
`packages/contracts/*.yaml` монтируются в сервисы только для чтения
(`./packages/contracts:/contracts:ro`).

Ниже — **целевой** состав. Что из него уже стоит в compose, видно по задачам в
[board.md](board.md).

| Контейнер | Образ / сборка | Команда | Зависит от | Тома |
| :--- | :--- | :--- | :--- | :--- |
| `postgres` | `postgres:16-alpine` | — | — | `pgdata`, скрипт инициализации трёх баз и ролей |
| `minio` | `quay.io/minio/minio` | `server /data --console-address :9001` | — | `miniodata` |
| `redis` | `redis:7-alpine` | — | — | — |
| `plan-service` | `services/plan-service` | `uvicorn src.main:app` | `postgres` | `contracts` |
| `site-service` | `services/site-service` | `uvicorn src.main:app` | `postgres`, `minio`, `redis` | `contracts` |
| `site-worker` | тот же образ, что `site-service` | `arq src.worker.WorkerSettings` | `redis`, `vision-service` | `contracts` |
| `analysis-service` | `services/analysis-service` | `uvicorn src.main:app` | `postgres`, `minio` | `contracts` |
| `vision-service` | `services/vision-service` | `uvicorn src.main:app` | — | `data/models` → `/models`, `contracts` |
| `gateway` | `services/gateway` | nginx | — | собранная статика `apps/web` |
| `ollama` (профиль `llm`) | `ollama/ollama` | — | — | `ollamadata`; только закрытый контур |

Особенности:

- `site-service` и `site-worker` — **один образ, разные команды**. Воркеров можно поднять
  несколько: `docker compose up -d --scale site-worker=3`.
- Веса моделей монтируются томом, а не копируются в образ: образ остаётся лёгким, а смена
  модели не требует пересборки.
- Ни один контейнер не знает пароля от чужой базы: у каждого своя роль и свой DSN.

## 10. Публикация и получение образов

Образы собирает и публикует `.github/workflows/release.yml` — **не** демо-ноутбук. Сервисы
конвейер находит сам, по наличию `Dockerfile`; перечислять их нигде не нужно.

```bash
git tag v0.2.0 && git push origin v0.2.0   # релиз по тегу
gh workflow run Release                    # то же самое вручную, без тега
```

Образы уезжают в `ghcr.io/<владелец>/<репозиторий>/<сервис>` с тегами `v0.2.0` и `latest`.
Реестр приватный, поэтому на машине, которая их забирает, нужен вход:

```bash
echo "$GITHUB_TOKEN" | docker login ghcr.io -u <логин> --password-stdin
docker compose pull && docker compose up -d
```

`IMAGE_REGISTRY` и `IMAGE_TAG` в `.env` задают, откуда и какую версию тянуть. Имя образа в
`docker-compose.yml` стоит рядом с `build:`, поэтому собранный локально образ получает то же имя,
что опубликованный.

**Зачем это вообще.** Образ `vision-service` с CUDA весит несколько гигабайт и собирается десятки
минут. За час до показа собирать его на ноутбуке нельзя — только скачать. Поэтому перед
демонстрацией ставится тег, конвейер собирает образы на своих машинах, а на стенде выполняется
`docker compose pull`.
