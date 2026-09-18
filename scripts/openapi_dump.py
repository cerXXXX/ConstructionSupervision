"""Снимает спецификацию OpenAPI из кода сервиса, не поднимая его.

Используется в CI: контракт проверяется без docker и без запущенной БД.
Приложение только импортируется — lifespan не выполняется, соединений нет.

    python scripts/openapi_dump.py services/plan-service
"""

import importlib
import json
import sys
from pathlib import Path


def dump(service_dir: Path) -> dict:
    sys.path.insert(0, str(service_dir.resolve()))
    module = importlib.import_module("src.main")
    return module.app.openapi()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("использование: python scripts/openapi_dump.py <каталог сервиса>", file=sys.stderr)
        raise SystemExit(2)

    spec = dump(Path(sys.argv[1]))
    print(json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True))
