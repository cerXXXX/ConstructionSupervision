import { useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { formatDelay, formatMoment, formatPlanDate, formatSpi } from "@/entities/format";
import { stageStatusTone } from "@/entities/status";
import { GanttChart, type Draft, type Zoom } from "@/features/gantt/GanttChart";
import { dayNumber, isoDate } from "@/features/gantt/layout";
import {
  useGantt,
  useSaveDates,
  useSelectedRow,
  type DatesSaveResult,
  type GanttRow,
  type Plan,
  type PlanStage,
} from "@/features/gantt/useGantt";
import { isWorkday, workdaysIn, type Dates } from "@/features/gantt/workdays";
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
  const [draft, setDraft] = useState<Draft | null>(null);
  const activeDraft = draft && draft.stageId === selected?.stage.id ? draft : null;
  // Черновик — только у выбранной вехи: переход к другой вехе его сбрасывает.
  const choose = (stageId: string) => {
    if (stageId !== selected?.stage.id) setDraft(null);
    select(stageId);
  };

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

      {plan.data && rows.length > 0 && (
        <>
          <GanttChart
            rows={rows}
            asOfDay={asOfDay}
            zoom={zoom}
            selectedId={selected?.stage.id ?? null}
            onSelect={choose}
            draft={activeDraft}
            calendar={plan.data.calendar}
            onDraft={setDraft}
          />
          <Legend />
          {selected ? (
            <StagePanel row={selected} stages={rows.map((r) => r.stage)}>
              <DatesEditor
                key={selected.stage.id}
                objectId={objectId}
                row={selected}
                calendar={plan.data.calendar}
                draft={activeDraft}
                onDraft={setDraft}
              />
            </StagePanel>
          ) : (
            <p className="text-sm text-muted">
              Щёлкните по вехе — откроется её карточка. Полосу можно тянуть: целиком или за край.
            </p>
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

function StagePanel({ row, stages, children }: { row: GanttRow; stages: PlanStage[]; children: ReactNode }) {
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
      <div className="lg:col-span-2">{children}</div>
    </article>
  );
}

/**
 * Правка плановых дат вехи (F11): черновик общий с перетаскиванием на диаграмме, сохранение —
 * PATCH вехи и прогон анализа, затем «было → стало» по прогнозу вехи и отставанию объекта.
 */
function DatesEditor({
  objectId,
  row,
  calendar,
  draft,
  onDraft,
}: {
  objectId: string;
  row: GanttRow;
  calendar: Plan["calendar"];
  draft: Draft | null;
  onDraft: (draft: Draft | null) => void;
}) {
  const save = useSaveDates(objectId);
  const dates = draft?.dates ?? { start: row.start, end: row.end };
  const set = (edge: keyof Dates, value: string) => {
    if (value) onDraft({ stageId: row.stage.id, dates: { ...dates, [edge]: dayNumber(value) } });
  };
  const issues = [
    dates.end < dates.start && "окончание раньше начала",
    !isWorkday(dates.start, calendar) && "начало — нерабочий день",
    !isWorkday(dates.end, calendar) && "окончание — нерабочий день",
  ].filter((issue): issue is string => typeof issue === "string");

  return (
    <div className="space-y-3 border-t border-ink/10 pt-4 text-sm">
      <p className="font-medium">Плановые даты</p>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-muted">Начало</span>
          <input
            type="date"
            value={isoDate(dates.start)}
            onChange={(e) => set("start", e.target.value)}
            className="rounded border border-ink/20 px-2 py-1"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-muted">Окончание, включительно</span>
          <input
            type="date"
            value={isoDate(dates.end)}
            onChange={(e) => set("end", e.target.value)}
            className="rounded border border-ink/20 px-2 py-1"
          />
        </label>
        <p className="pb-1.5 text-muted">
          {dates.end >= dates.start ? `${workdaysIn(dates, calendar)} ${ru.units.workDays}` : "—"} по
          календарю {calendar.code}
        </p>
        <button
          type="button"
          disabled={!draft || issues.length > 0 || save.isPending}
          onClick={() => save.mutate({ stageId: row.stage.id, dates }, { onSuccess: () => onDraft(null) })}
          className="rounded bg-accent px-3 py-1.5 text-white hover:bg-accent/85 disabled:opacity-40"
        >
          {save.isPending ? "Сохраняем и пересчитываем…" : "Сохранить и пересчитать"}
        </button>
        {draft && !save.isPending && (
          <button type="button" onClick={() => onDraft(null)} className="rounded border border-ink/20 px-3 py-1.5 hover:border-accent">
            Отменить
          </button>
        )}
      </div>
      {issues.length > 0 && <p className="text-red-800">Не сохранить: {issues.join("; ")}.</p>}
      <p className="text-muted">
        Полосу можно тянуть на диаграмме: целиком — длительность в рабочих днях сохраняется, за
        край — меняется начало или конец. Соседние вехи не сдвигаются: нарушенную связь покажет
        отрицательный резерв.
      </p>
      {save.isError && <ErrorBox error={save.error} />}
      {save.data && <SaveSummary result={save.data} />}
    </div>
  );
}

function SaveSummary({ result }: { result: DatesSaveResult }) {
  const { before, after } = result;
  const change = (was: string, now: string) => (was === now ? `${now} (без изменений)` : `${was} → ${now}`);
  const objectDelay = (s: DatesSaveResult["after"]) =>
    s.status ? `${label(ru.objectStatus, s.status.status)}, ${formatDelay(s.status.delay_days)} ${ru.units.workDays}` : "—";
  const critical = (value: boolean | null) => (value == null ? "—" : value ? "да" : "нет");
  return (
    <div className="rounded bg-emerald-50 p-3 text-emerald-950">
      <p className="font-medium">Сохранено, анализ пересчитан ({formatMoment(result.run.as_of)}):</p>
      <ul className="list-disc pl-5">
        <li>
          прогноз окончания вехи:{" "}
          {change(formatPlanDate(before.stage?.forecast_end), formatPlanDate(after.stage?.forecast_end))}
        </li>
        <li>
          отставание вехи:{" "}
          {change(formatDelay(before.stage?.delay_days), formatDelay(after.stage?.delay_days))} {ru.units.workDays}
        </li>
        <li>на критическом пути: {change(critical(before.critical), critical(after.critical))}</li>
        <li>объект: {change(objectDelay(before), objectDelay(after))}</li>
      </ul>
    </div>
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
