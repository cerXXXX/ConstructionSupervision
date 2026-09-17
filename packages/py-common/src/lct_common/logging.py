"""Структурный лог в stdout: одна строка — один JSON-объект.

Событие называется точкой (`domain.action`), остальное уходит полями:

    log.info("plan.generated", object_id=str(obj.id), stages=12, duration_ms=340)

Форматирование сообщения f-строками и print запрещены: по логам должно быть
возможно фильтровать и агрегировать, а не только читать глазами.
"""

import logging
import sys
from typing import Any

import structlog

from lct_common.request_id import current_request_id


def _add_request_id(_logger: Any, _name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Подмешивает идентификатор запроса в каждую запись."""
    request_id = current_request_id()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def setup_logging(service_name: str, level: str = "INFO", *, pretty: bool = False) -> None:
    """Настраивает логирование один раз при старте приложения.

    pretty=True включает человекочитаемый вывод — только для локальной отладки,
    в контейнере всегда JSON.
    """
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level.upper())

    renderer = (
        structlog.dev.ConsoleRenderer() if pretty else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _add_request_id,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[level.upper()]
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
