# Запуск, конфигурация и эксплуатация

---

## 1. Требования

| Что | Версия | Зачем |
| :--- | :--- | :--- |
| Docker + Docker Compose | 24+ / v2 | Единственный обязательный способ запуска |
| GNU Make | любая | Все команды проекта |
| Python | 3.12 | Локальная разработка сервисов вне докера |
| Node.js | 20+ | Локальная разработка фронтенда |
| Свободная память | 6 ГБ (без LLM) / 12 ГБ (с локальной LLM) | CV-модель + Postgres + MinIO |
| Диск | ~8 ГБ | Образы, веса моделей, демо-снимки |

GPU не требуется. При наличии — `VISION_DEVICE=cuda` и профиль `gpu` в compose.

## 2. Первый запуск

```bash
cp .env.example .env     # при необходимости поменять пароли и ключ API
make models              # скачать веса YOLO и OpenCLIP в data/models (~200 МБ)
make up                  # docker compose up -d --build
make health              # все сервисы должны ответить healthy
make seed                # демо-объект, график, камеры, зоны, снимки, прогон анализа
```

| Адрес | Что |
| :--- | :--- |
| <http://localhost:8080> | Интерфейс |
| <http://localhost:8080/docs> | Сводный Swagger с выбором сервиса |
| <http://localhost:8001/docs> … <http://localhost:8005/docs> | Swagger отдельных сервисов |
| <http://localhost:9001> | Консоль MinIO |

## 3. Команды Make

| Команда | Что делает |
| :--- | :--- |
| `make up` / `make down` | Поднять / остановить стек |
| `make restart s=site` | Перезапустить один сервис |
| `make logs s=analysis` | Логи сервиса (`f=1` — следить) |
| `make ps` | Состояние контейнеров |
| `make health` | Опросить `/health/ready` всех сервисов |
| `make seed` | Загрузить демо-данные |
| `make demo` | `seed` + сценарий показа: три «дня» объекта с заложенными отклонениями |
| `make reset` | Полная очистка: тома БД, бакеты MinIO, очередь |
| `make test` / `make test s=plan` | Тесты всех сервисов / одного |
| `make e2e` | Сквозной сценарий на поднятом стеке |
| `make lint` / `make fmt` | Проверка / автоформатирование |
| `make contracts` | Пересобрать снапшоты OpenAPI и TS-клиент |
| `make migrate s=plan m="описание"` | Создать миграцию Alembic |
| `make models` | Скачать веса моделей |
| `make report o=<object_id>` | Сформировать PDF-отчёт из командной строки |

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

### Базы данных

| Переменная | По умолчанию |
| :--- | :--- |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `postgres` / `5432` |
| `POSTGRES_SUPERUSER` / `POSTGRES_PASSWORD` | `postgres` / задаётся в `.env` |
| `PLAN_DB_DSN` | `postgresql+asyncpg://plan_user:***@postgres:5432/plandb` |
| `SITE_DB_DSN` | `postgresql+asyncpg://site_user:***@postgres:5432/sitedb` |
| `ANALYSIS_DB_DSN` | `postgresql+asyncpg://analysis_user:***@postgres:5432/analysisdb` |

Базы и роли создаются один раз скриптом инициализации Postgres. Роль имеет права
только на свою базу — граница сервисов защищена самой СУБД.

### Хранилище и очередь

| Переменная | По умолчанию |
| :--- | :--- |
| `S3_ENDPOINT` | `http://minio:9000` |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | задаются в `.env` |
| `S3_BUCKET_IMAGES` / `S3_BUCKET_PREVIEWS` / `S3_BUCKET_REPORTS` | `images` / `previews` / `reports` |
| `S3_PRESIGN_TTL_S` | `3600` |
| `REDIS_URL` | `redis://redis:6379/0` |

### Адреса сервисов

| Переменная | По умолчанию |
| :--- | :--- |
| `PLAN_URL` | `http://plan-service:8000` |
| `SITE_URL` | `http://site-service:8000` |
| `ANALYSIS_URL` | `http://analysis-service:8000` |
| `VISION_URL` | `http://vision-service:8000` |
| `POS_URL` | `http://pos-engine:8000` |
| `REPORT_URL` | `http://report-service:8000` |

### Компьютерное зрение

| Переменная | По умолчанию | Смысл |
| :--- | :--- | :--- |
| `VISION_DEVICE` | `cpu` | `cpu` / `cuda` |
| `VISION_DET_WEIGHTS` | `/models/yolo11s-lct.onnx` | Веса детектора |
| `VISION_DET_CONF` | `0.35` | Порог уверенности |
| `VISION_DET_IMGSZ` | `1280` | Размер входа |
| `VISION_STAGE_MODEL` | `openclip-vit-b32` | Классификатор стадии |
| `VISION_BATCH_SIZE` | `4` | |

### Конвейер и методика

| Переменная | По умолчанию | Смысл |
| :--- | :--- | :--- |
| `SESSION_WINDOW_MINUTES` | `30` | Длина окна сессии |
| `SESSION_CLOSE_GRACE_MINUTES` | `10` | Ожидание опоздавших снимков перед агрегацией |
| `MAX_IMAGE_MB` | `20` | Предел размера снимка |
| `WORKER_CONCURRENCY` | `4` | Параллельных задач в воркере |
| `MIN_ACTIVITY` | `0.1` | Нижняя граница темпа в прогнозе |
| `ON_TRACK_TOLERANCE_DAYS` | `2` | Порог статуса «в графике» |

Пороги методики продублированы в таблице `deviation_rule` и редактируются в UI;
переменные окружения задают лишь значения по умолчанию при первичном заполнении.

### LLM

| Переменная | По умолчанию | Смысл |
| :--- | :--- | :--- |
| `LLM_ENABLED` | `true` | `false` → шаблонные резюме без модели |
| `LLM_PROVIDER` | `ollama` | `ollama` / `openai_compatible` |
| `LLM_BASE_URL` | `http://ollama:11434` | |
| `LLM_MODEL` | `qwen2.5:7b-instruct` | |
| `LLM_TIMEOUT_S` | `60` | По истечении — шаблонное резюме |

## 5. Профили compose

| Профиль | Что добавляет | Когда |
| :--- | :--- | :--- |
| по умолчанию | gateway, все сервисы, postgres, minio, redis | Обычная работа |
| `llm` | Ollama + загрузка модели | Нужны LLM-резюме локально |
| `gpu` | `vision-service` с пробросом GPU | Есть NVIDIA |
| `dev` | Hot-reload, проброс портов, Vite вместо статики | Разработка |

```bash
docker compose --profile llm up -d
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 6. Демо-сценарий (5 минут)

`make demo` готовит данные, дальше — по шагам интерфейса:

1. **Настройки → объект.** Вводим наименование: «Строительство монолитного жилого дома
   17 этажей с подземной автостоянкой». Показываем, что `pos-engine` распознал ТЭП
   и построил график по МРР с обоснованием по каждому этапу.
2. **День 1 — котлован.** Экскаватор есть, самосвалов нет → **D2 «неполный комплект»**.
   Открываем карточку: правило, числа, снимок с рамками.
3. **День 2 — опережение.** Появился бетононасос при активном котловане → **D3**,
   стадия по фото подтверждает начало плиты.
4. **День 3 — простой и слепая зона.** Экскаватор стоит у въезда → **D4**;
   одна камера закрыта → **D10 «зона вне контроля ИИ, проверить вручную»**.
5. **Гант.** Фактический старт, прогноз окончания, задержка, перенос на зависимые вехи.
6. **Отчёт.** PDF с планом-фактом, загрузкой техники и LLM-резюме со ссылками на ID отклонений.
7. **Правка правила.** Меняем минимум самосвалов с 2 на 1 в UI → пересчёт → D2 исчезает.
   Это демонстрация главного архитектурного тезиса: логика — данные, а не код.

## 7. Диагностика

| Симптом | Причина | Что делать |
| :--- | :--- | :--- |
| `make health` показывает `vision: fail` | Не скачаны веса | `make models`, затем `make restart s=vision` |
| Снимки остаются в статусе `PENDING` | Воркер не поднялся или недоступен Redis | `make logs s=site-worker`, проверить `REDIS_URL` |
| Снимки в статусе `NEEDS_TIME` | Нет EXIF и время не распознано из имени файла | Указать время при загрузке или переименовать по шаблону `cam_YYYYMMDD_HHMMSS.jpg` |
| Анализ не находит отклонений | Нет активных вех на дату снимков либо зоны не размечены | Проверить `GET /api/v1/plan/objects/{id}/stages?active_on=...` и наличие зон у камер |
| Все зоны `BLIND` | Не размечены зоны или снимки не привязаны к камерам | Разметить зоны на эталонном кадре в UI |
| Отчёт без LLM-резюме | Ollama не поднята или таймаут | Профиль `llm` либо `LLM_ENABLED=false` — резюме станет шаблонным |
| `409 IMAGE_ALREADY_EXISTS` | Повторная загрузка того же файла | Это защита от дублей, не ошибка |
| Медленная обработка на CPU | Большой размер входа | Уменьшить `VISION_DET_IMGSZ`, увеличить `WORKER_CONCURRENCY` |

**Куда смотреть в первую очередь:** `request_id` из ответа об ошибке —
`docker compose logs | grep <request_id>` показывает всю цепочку вызовов через все сервисы.

## 8. Резервное копирование и перенос

- Данные: тома `pgdata` (три базы) и `miniodata`.
- Логический дамп: `make backup` → `backup/YYYY-MM-DD/{plandb,sitedb,analysisdb}.sql` + зеркало
  бакетов MinIO.
- Перенос к заказчику: те же образы, свой `.env`, свои адреса Postgres и S3.
  Ничего, кроме переменных окружения, менять не требуется.

## 9. Состав docker-compose

Один файл `docker-compose.yml` на весь стек, оверлей `docker-compose.dev.yml` для разработки.
Порядок запуска задаётся через `depends_on: condition: service_healthy` — сервис поднимается
только после готовности своих зависимостей.

| Контейнер | Образ / сборка | Команда | Зависит от | Тома |
| :--- | :--- | :--- | :--- | :--- |
| `postgres` | `postgres:16-alpine` | — | — | `pgdata`, скрипт инициализации трёх баз и ролей |
| `minio` | `minio/minio` | `server /data --console-address :9001` | — | `miniodata` |
| `redis` | `redis:7-alpine` | — | — | — |
| `pos-engine` | `services/pos-engine` | `uvicorn src.main:app` | — | справочники внутри образа |
| `plan-service` | `services/plan-service` | `uvicorn src.main:app` | `postgres`, `pos-engine` | — |
| `site-service` | `services/site-service` | `uvicorn src.main:app` | `postgres`, `minio`, `redis` | — |
| `site-worker` | тот же образ, что `site-service` | `arq src.worker.WorkerSettings` | `redis`, `vision-service` | — |
| `analysis-service` | `services/analysis-service` | `uvicorn src.main:app` | `postgres`, `plan-service`, `site-service` | — |
| `vision-service` | `services/vision-service` | `uvicorn src.main:app` | — | `data/models` → `/models` (только чтение) |
| `report-service` | `services/report-service` | `uvicorn src.main:app` | `analysis-service`, `plan-service`, `minio` | — |
| `gateway` | `services/gateway` | nginx | все API-сервисы | собранная статика `apps/web` |
| `ollama` (профиль `llm`) | `ollama/ollama` | — | — | `ollamadata` |

Особенности:

- `site-service` и `site-worker` — **один образ, разные команды**. Воркеров можно поднять
  несколько: `docker compose up -d --scale site-worker=3`.
- Веса моделей монтируются томом, а не копируются в образ: образ остаётся лёгким,
  а смена модели не требует пересборки.
- `docker-compose.dev.yml` добавляет проброс исходников, `--reload`, порты наружу
  и Vite вместо статики.
- Ни один контейнер не знает пароля от чужой базы: у каждого своя роль и свой DSN.
