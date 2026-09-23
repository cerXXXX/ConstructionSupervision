"""Клиент site-service: факты за период одним запросом (interservice.md, контракт 2)."""

from datetime import UTC, datetime
from uuid import UUID

from lct_common import ServiceClient, UpstreamError

from src.core.inputs import Facts


class SiteServiceUnavailable(UpstreamError):
    code = "SITE_SERVICE_UNAVAILABLE"


def _iso(moment: datetime) -> str:
    """ISO-8601 в UTC с `Z`, как требуют общие правила контрактов."""
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


class SiteClient(ServiceClient):
    async def get_facts(self, object_id: UUID, period_from: datetime, period_to: datetime) -> Facts:
        """Факты по сессиям с началом окна в [period_from, period_to)."""
        try:
            payload = await self.get(
                f"/api/v1/site/objects/{object_id}/facts",
                params={"from": _iso(period_from), "to": _iso(period_to)},
            )
        except UpstreamError as exc:
            raise SiteServiceUnavailable(
                "site-service недоступен: факты объекта не получены", **exc.details
            ) from exc
        return Facts.model_validate(payload)
