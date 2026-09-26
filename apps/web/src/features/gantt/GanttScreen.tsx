import { useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { formatDelay, formatMoment, formatPlanDate, formatSpi } from "@/entities/format";
import { stageStatusTone } from "@/entities/status";
import { GanttChart, type Zoom } from "@/features/gantt/GanttChart";
import { useGantt, useSelectedRow, type GanttRow, type PlanStage } from "@/features/gantt/useGantt";
import { label, ru } from "@/shared/locale/ru";
import { Badge } from "@/shared/ui/Badge";
import { Empty, ErrorBox, Loading } from "@/shared/ui/QueryState";

const ZOOMS: { label: string; value: Zoom }[] = [
  { label: "Весь график", value: "fit" },
  { label: "Месяцы", value: 4 },
  { label: "Недели", value: 14 },
];

/**
 * Гант план-факт (F10): плановые окна вех из plan-service, факт и прогноз из analysis-service.
 * Прогноз — при сохранении текущего темпа, с уверенностью (apps/web/README.md, §5).
 */
export function GanttScreen() {
  const { objectId = "" } = useParams();
  const { plan, progress, rows, asOfDay } = useGantt(objectId);
  const { selected, select } = useSelectedRow(rows);
  const [zoom, setZoom] = useState<Zoom>("fit");

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link to={`/objects/${objectId}`} className="text-sm text-muted hover:text-ink">
            ← Дашборд
          </Link>
          <h2 className="text-xl font-semibold">График план-факт</h2>
          {plan.data && (
            <p className="text-sm text-muted">
              {plan.data.object.name} · версия плана {plan.data.plan_version} · календарь{" "}
              {plan.data.calendar.code}
              {progress.data && ` · анализ на ${formatMoment(progress.data.as_of)}`}
            </p>
          )}
        </div>
        <div className="flex gap-1 text-sm">
          {ZOOMS.map((z) => (
            <button
              key={z.label}
              type="button"
              onClick={() => setZoom(z.value)}
              className={`rounded px-3 py-1 ${zoom === z.value ? "bg-ink text-white" : "border border-ink/20 hover:border-accent"}`}
            >
              {z.label}
            </button>
          ))}
        </div>
      </div>

      {plan.isPending && <Loading />}
      {plan.isError && <ErrorBox error={plan.error} onRetry={() => plan.refetch()} />}
      {progress.isError && <ErrorBox error={progress.error} onRetry={() => progress.refetch()} />}
      {plan.isSuccess && rows.length === 0 && (
        <Empty>У объекта нет графика: импортируйте его или сгенерируйте по МРР.</Empty>
      )}
      {progress.data === null && rows.length > 0 && (
        <Empty>
          Анализа по объекту ещё не было: показан только план, без факта и прогноза.
        </Empty>
      )}

      {rows.length > 0 && (
        <>
          <GanttChart
            rows={rows}
            asOfDay={asOfDay}
            zoom={zoom}
            selectedId={selected?.stage.id ?? null}
            onSelect={select}
          />
          <Legend />
          {selected ? (
            <StagePanel row={selected} stages={rows.map((r) => r.stage)} />
          ) : (
            <p className="text-sm text-muted">Щёлкните по вехе — откроется её карточка.</p>
          )}
        </>
      )}
    </section>
  );
}

function Legend() {
  const item = (swatch: ReactNode, text: string) => (
    <span className="flex items-center gap-1.5">
      <svg width="22" height="12">
        {swatch}
      </svg>
      {text}
    </span>
  );
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted">
      {item(<rect x="1" y="1" width="20" height="10" rx="2" className="fill-stone-200 stroke-stone-400" />, "плановое окно")}
      {item(<rect x="1" y="1" width="20" height="10" rx="2" className="fill-accent/20 stroke-accent" />, "критический путь")}
      {item(<rect x="1" y="3" width="14" height="6" className="fill-amber-500" />, "выполнено (цвет — статус)")}
      {item(<path d="M6 1 h10 l-5 7 z" className="fill-ink" />, "фактический старт")}
      {item(<rect x="1" y="2" width="20" height="8" className="fill-red-100 stroke-red-600" strokeDasharray="3 2" />, "прогноз позже плана")}
      {item(<line x1="11" x2="11" y1="0" y2="12" className="stroke-sky-600" strokeWidth="2" />, "прогноз раньше плана")}
      <span>±N — отставание в {ru.units.workDays}</span>
    </div>
  );
}

function StagePanel({ row, stages }: { row: GanttRow; stages: PlanStage[] }) {
  const { stage, progress } = row;
  const names = new Map(stages.map((s) => [s.id, `${s.code} ${s.name}`]));
  const facts = (progress?.facts ?? {}) as Record<string, unknown>;
  return (
    <article className="grid gap-5 rounded-lg border border-ink/10 bg-white p-5 lg:grid-cols-2">
      <div className="space-y-2 text-sm">
        <h3 className="text-lg font-semibold">
          {stage.code} {stage.name}
        </h3>
        <p>
          По плану {formatPlanDate(stage.plan_start)} — {formatPlanDate(stage.plan_end)}, норма{" "}
          {stage.norm_duration_days} {ru.units.workDays}
        </p>
        <p>
          {stage.is_critical
            ? "На критическом пути: задержка вехи сдвигает окончание объекта."
            : stage.total_float_days < 0
              ? `Резерв ${formatDelay(stage.total_float_days)} ${ru.units.workDays}: даты вехи нарушают связи с соседями.`
              : `Резерв ${stage.total_float_days} ${ru.units.workDays}: на столько веха может сдвинуться без сдвига объекта.`}
        </p>
        {stage.basis && <p className="text-muted">Основание срока: {stage.basis}</p>}
        {stage.predecessors.length > 0 && (
          <div>
            <p className="text-muted">Зависит от:</p>
            <ul className="list-disc pl-5">
              {stage.predecessors.map((p) => (
                <li key={p.stage_id}>
                  {names.get(p.stage_id) ?? p.stage_id} — {label(ru.linkType, p.type)}
                  {p.lag_days !== 0 && `, лаг ${p.lag_days} ${ru.units.workDays}`}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="space-y-2 text-sm">
        {!progress ? (
          <p className="text-muted">Факта по вехе нет: анализ её ещё не считал.</p>
        ) : (
          <>
            <p>
              <Badge tone={stageStatusTone(progress.status)}>{label(ru.stageStatus, progress.status)}</Badge>{" "}
              <span className="text-muted">уверенность {label(ru.confidence, progress.confidence)}</span>
            </p>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
              <dt className="text-muted">Фактический старт</dt>
              <dd>{formatPlanDate(progress.actual_start)}</dd>
              <dt className="text-muted">Прогресс</dt>
              <dd>
                {Math.round(progress.progress * 100)} % при плане {Math.round(progress.planned_progress * 100)} %
              </dd>
              <dt className="text-muted">SPI</dt>
              <dd>{formatSpi(progress.spi)}</dd>
              <dt className="text-muted">Прогноз окончания</dt>
              <dd>
                {formatPlanDate(progress.forecast_end)}, отставание {formatDelay(progress.delay_days)}{" "}
                {ru.units.workDays} — при сохранении текущего темпа
              </dd>
            </dl>
            <p className="text-muted">{basis(facts)}</p>
          </>
        )}
      </div>
    </article>
  );
}

/** Откуда прогресс вехи: по плану (и почему) или по наблюдениям (сколько дней). */
function basis(facts: Record<string, unknown>): string {
  if (typeof facts.basis_reason === "string") return `Прогресс по плану: ${facts.basis_reason}.`;
  if (facts.basis === "OBSERVED") {
    const days = typeof facts.observed_days === "number" ? facts.observed_days : "—";
    const since = typeof facts.observation_start === "string" ? facts.observation_start : null;
    return `Прогресс по наблюдениям: дней наблюдений ${days}${since ? ` с ${formatPlanDate(since)}` : ""}.`;
  }
  return "";
}
