import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { formatDelay, formatMoment, formatPlanDate, formatSpi } from "@/entities/format";
import { SEVERITY_ORDER, objectStatusTone, openDeviations, severityTone } from "@/entities/status";
import {
  stagesAtRisk,
  useDashboard,
  useLatestImages,
  useRecompute,
} from "@/features/dashboard/useDashboard";
import type { ObjectStatus } from "@/shared/api/queries";
import { label, ru } from "@/shared/locale/ru";
import { Badge } from "@/shared/ui/Badge";
import { Empty, ErrorBox, Loading } from "@/shared/ui/QueryState";

/**
 * Дашборд объекта: что не так и насколько можно верить выводу. Каждое число подписано,
 * откуда оно; прогноз — с уверенностью и оговоркой о темпе (apps/web/README.md, §5).
 */
export function DashboardScreen() {
  const { objectId = "" } = useParams();
  const { object, status } = useDashboard(objectId);
  const recompute = useRecompute(objectId, status.data?.as_of);

  if (object.isPending) return <Loading />;
  if (object.isError) return <ErrorBox error={object.error} onRetry={() => object.refetch()} />;

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/objects" className="text-sm text-muted hover:text-ink">
            ← Объекты
          </Link>
          <h2 className="text-xl font-semibold">{object.data.name}</h2>
          <p className="text-sm text-muted">
            {label(ru.objectType, object.data.object_type)} · начало СМР{" "}
            {formatPlanDate(object.data.plan_start)} · версия плана {object.data.plan_version}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/objects/${objectId}/deviations`}
            className="rounded bg-ink px-3 py-1.5 text-sm text-white hover:bg-ink/80"
          >
            Предупреждения
          </Link>
          <Link
            to={`/objects/${objectId}/gantt`}
            className="rounded border border-ink/20 px-3 py-1.5 text-sm hover:border-accent"
          >
            График
          </Link>
          <Link
            to={`/objects/${objectId}/cameras`}
            className="rounded border border-ink/20 px-3 py-1.5 text-sm hover:border-accent"
          >
            Камеры
          </Link>
          <Link
            to={`/objects/${objectId}/reports`}
            className="rounded border border-ink/20 px-3 py-1.5 text-sm hover:border-accent"
          >
            Отчёты
          </Link>
          <Link
            to={`/objects/${objectId}/settings/rules`}
            className="rounded border border-ink/20 px-3 py-1.5 text-sm hover:border-accent"
          >
            Правила
          </Link>
          <Link
            to={`/objects/${objectId}/settings/zones`}
            className="rounded border border-ink/20 px-3 py-1.5 text-sm hover:border-accent"
          >
            Зоны
          </Link>
          <button
            type="button"
            onClick={() => recompute.mutate()}
            disabled={recompute.isPending}
            title="Прогон анализа на тот же момент, что показан ниже"
            className="rounded border border-ink/20 px-3 py-1.5 text-sm hover:border-accent disabled:opacity-50"
          >
            {recompute.isPending ? "Пересчитываем…" : "Пересчитать"}
          </button>
        </div>
      </div>
      {recompute.isError && <ErrorBox error={recompute.error} />}

      {status.isPending && <Loading />}
      {status.isError && <ErrorBox error={status.error} onRetry={() => status.refetch()} />}
      {status.data === null && (
        <Empty>
          По объекту ещё не было анализа. Он запускается сам после распознавания снимков и правки
          плана; можно запустить и вручную — кнопкой «Пересчитать».
        </Empty>
      )}
      {status.data && <StatusPanels objectId={objectId} status={status.data} />}

      <LatestImages objectId={objectId} />
    </section>
  );
}

function StatusPanels({ objectId, status }: { objectId: string; status: ObjectStatus }) {
  const facts = status.facts as Record<string, unknown>;
  const risk = stagesAtRisk(status.stages_at_risk);
  const total = openDeviations(status.deviations);
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Tile title="Статус">
          <Badge tone={objectStatusTone(status.status)}>{label(ru.objectStatus, status.status)}</Badge>
          <p className="mt-2 text-sm text-muted">
            {status.delay_days != null
              ? `${formatDelay(status.delay_days)} ${ru.units.workDays} по критическому пути, при сохранении текущего темпа`
              : "Отставание не оценено: мало наблюдений или участки не видны"}
          </p>
        </Tile>
        <Tile title="SPI">
          <p className="text-2xl font-semibold">{formatSpi(status.spi)}</p>
          <p className="text-sm text-muted">
            Освоенный объём к плановому, веса — нормативные длительности вех. Меньше 1 — отстаём.
          </p>
        </Tile>
        <Tile title="Уверенность">
          <p className="text-2xl font-semibold">{label(ru.confidence, status.confidence)}</p>
          <p className="text-sm text-muted">
            Дней наблюдений: {String(facts.observation_days ?? "—")}, видимость участков:{" "}
            {typeof facts.visible_share === "number"
              ? `${Math.round(facts.visible_share * 100)} %`
              : "—"}
          </p>
        </Tile>
        <Tile title="На момент">
          <p className="text-lg font-semibold">{formatMoment(status.as_of)}</p>
          <p className="text-sm text-muted">Посчитано {formatMoment(status.computed_at)}</p>
        </Tile>
      </div>

      {status.status === "UNKNOWN" && typeof facts.min_days_for_forecast === "number" && (
        <p className="text-sm text-muted">
          Для прогноза нужно не меньше {facts.min_days_for_forecast} дней наблюдений.
        </p>
      )}

      {status.blind_areas > 0 && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-amber-900">
          Участков вне контроля ИИ: {status.blind_areas}. В последней рабочей сессии их не видела ни
          одна камера — проверить вручную.
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Tile title={`Открытые отклонения: ${total}`}>
          <div className="mt-1 flex flex-wrap gap-2">
            {SEVERITY_ORDER.map((severity) => (
              <Link key={severity} to={`/objects/${objectId}/deviations?status=open&severity=${severity}`}>
                <Badge tone={severityTone(severity)}>
                  {label(ru.severity, severity)}: {status.deviations[severity] ?? 0}
                </Badge>
              </Link>
            ))}
          </div>
          <Link to={`/objects/${objectId}/deviations`} className="mt-2 inline-block text-sm text-accent underline">
            Вся лента, включая закрытые
          </Link>
        </Tile>
        <Tile title={`Вехи: ${status.stages.total ?? 0}`}>
          <ul className="mt-1 text-sm">
            {Object.entries(status.stages)
              .filter(([key]) => key !== "total")
              .map(([key, count]) => (
                <li key={key}>
                  {label(ru.stageFactStatus, key.toUpperCase())}: {count}
                </li>
              ))}
          </ul>
        </Tile>
      </div>

      <div>
        <h3 className="mb-2 font-semibold">Вехи в риске</h3>
        {risk.length === 0 ? (
          <Empty>Вех критического пути с прогнозом позже плана нет.</Empty>
        ) : (
          <table className="w-full border-collapse text-left text-sm">
            <thead className="text-muted">
              <tr className="border-b border-ink/10">
                <th className="py-2 pr-4 font-normal">Веха</th>
                <th className="py-2 pr-4 font-normal">Окончание по плану</th>
                <th className="py-2 pr-4 font-normal">Прогноз</th>
                <th className="py-2 font-normal">Отставание</th>
              </tr>
            </thead>
            <tbody>
              {risk.map((stage) => (
                <tr key={stage.stageId} className="border-b border-ink/10">
                  <td className="py-2 pr-4">
                    <Link to={`/objects/${objectId}/gantt?stage=${stage.stageId}`} className="underline decoration-ink/30 hover:text-accent">
                      {stage.name}
                    </Link>
                  </td>
                  <td className="py-2 pr-4">{formatPlanDate(stage.planEnd)}</td>
                  <td className="py-2 pr-4">{formatPlanDate(stage.forecastEnd)}</td>
                  <td className="py-2">
                    {formatDelay(stage.delayDays)} {ru.units.workDays}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function LatestImages({ objectId }: { objectId: string }) {
  const latest = useLatestImages(objectId);
  return (
    <div>
      <h3 className="mb-2 font-semibold">Последние снимки</h3>
      {latest.isPending && <Loading />}
      {latest.error != null && <ErrorBox error={latest.error} />}
      {!latest.isPending && latest.error == null && latest.total === 0 && (
        <Empty>Распознанных снимков пока нет.</Empty>
      )}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {latest.images.map((image) => (
          <figure key={image.id} className="space-y-1">
            <img
              src={image.url}
              alt={`Снимок ${formatMoment(image.captured_at)}`}
              className="aspect-video w-full rounded object-cover"
            />
            <figcaption className="text-xs text-muted">
              {formatMoment(image.captured_at)} · рамок: {image.detections.length}
              {image.usable === false && ` · непригоден (${image.usable_reason ?? "?"})`}
            </figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}

function Tile({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-ink/10 bg-white/60 p-4">
      <p className="mb-1 text-sm text-muted">{title}</p>
      {children}
    </div>
  );
}
