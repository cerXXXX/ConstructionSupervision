# Доменные события

События **названы сейчас, реализованы прямыми HTTP-вызовами**. Это сделано намеренно
([ADR-0004](../../docs/decisions/0004-sync-rest-and-queue.md)): брокер за полторы недели
не окупается, но переход на него не должен требовать переписывания логики.

Когда брокер появится, изменится только реализация в `clients/`: вместо вызова — публикация.

| Событие | Кто порождает | Полезная нагрузка | Кто реагирует сейчас |
| :--- | :--- | :--- | :--- |
| `image.registered` | site-service | `image_id, object_id, camera_id, captured_at, session_id` | Очередь задач воркера |
| `image.analyzed` | site-worker | `image_id, session_id, detections_count, stage_label, model_version` | Проверка закрытия сессии |
| `image.failed` | site-worker | `image_id, error_code` | Лента ошибок в UI |
| `session.closed` | site-service | `session_id, object_id, window_start, window_end` | Задача агрегации |
| `session.aggregated` | site-worker | `session_id, object_id, zones_count, zones_version` | Вызов `POST /analysis/runs` |
| `plan.updated` | plan-service | `object_id, plan_revision, changed_stage_ids` | Сигнал пересчёта анализа |
| `rules.updated` | plan-service | `object_id, rules_version, changed_rule_ids` | Сигнал пересчёта анализа |
| `zones.updated` | site-service | `object_id, zones_version, changed_zone_ids` | Задача `reapply_zones`, затем пересчёт |
| `analysis.completed` | analysis-service | `run_id, object_id, opened, resolved, status, delay_days` | Обновление дашборда |
| `deviation.opened` | analysis-service | `deviation_id, object_id, code, severity, stage_id, zone_id` | Лента; в будущем — уведомления |
| `deviation.resolved` | analysis-service | `deviation_id, object_id, code, resolved_at` | Лента |

## Правила

1. Событие — факт в прошедшем времени, а не команда. `session.aggregated`, не `aggregate_session`.
2. Полезная нагрузка — идентификаторы и минимум контекста. Подробности потребитель
   запрашивает у владельца данных: событие не должно превращаться в способ передачи состояния.
3. Событие не гарантирует доставку и может прийти дважды. Любой обработчик идемпотентен —
   это требование действует уже сейчас, до всякого брокера.
4. Потеря события не должна ломать состояние: восстановление — повторный прогон
   (`POST /analysis/runs`, `POST /site/images/reanalyze`). Именно поэтому сигналы
   пересчёта ничего не возвращают и не входят в транзакции.
