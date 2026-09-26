import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { formatClock, formatDay } from "@/entities/format";
import { SEVERITY_ORDER, deviationStatusTone, severityTone } from "@/entities/status";
import { DeviationCard } from "@/features/deviations/DeviationCard";
import {
  STATUS_PRESETS,
  useDeviationFilter,
  useDeviations,
  type StatusPreset,
} from "@/features/deviations/useDeviations";
import { objectQuery, type DeviationRead } from "@/shared/api/queries";
import { label, ru } from "@/shared/locale/ru";
import { Badge } from "@/shared/ui/Badge";
import { Empty, ErrorBox, Loading } from "@/shared/ui/QueryState";

const CODES = Object.keys(ru.deviationCode);

/**
 * Лента предупреждений (T30) — главный экран: правило, числа и снимок-доказательство
 * (apps/web/README.md, §3). Слева лента по дням, справа карточка выбранного отклонения.
 */
export function DeviationsScreen() {
  const { objectId = "" } = useParams();
  const object = useQuery(objectQuery(objectId));
  const { filter, preset, selectedId, update } = useDeviationFilter();
  const { feed, items, selected } = useDeviations(objectId, filter, selectedId);

  return (
    <section className="space-y-4">
      <div>
        <Link to={`/objects/${objectId}`} className="text-sm text-muted hover:text-ink">
          ← Дашборд
        </Link>
        <h2 className="text-xl font-semibold">Предупреждения</h2>
        {object.data && <p className="text-sm text-muted">{object.data.name}</p>}
      </div>

      <Filters
        preset={preset}
        code={filter.codes[0] ?? ""}
        severity={filter.severities[0] ?? ""}
        from={filter.from ?? ""}
        to={filter.to ?? ""}
        onChange={(changes) => update({ ...changes, id: null })}
      />

      {feed.isPending && <Loading />}
      {feed.isError && <ErrorBox error={feed.error} onRetry={() => feed.refetch()} />}
      {feed.isSuccess && items.length === 0 && (
        <Empty>
          {preset === "all" && !filter.codes.length && !filter.severities.length && !filter.from
            ? "Отклонений нет. Лента заполняется прогоном анализа: он идёт сам после распознавания снимков и правки плана, вручную — кнопкой «Пересчитать» на дашборде."
            : "Под фильтр ничего не попало. Сбросьте часть условий."}
        </Empty>
      )}
      {items.length > 0 && (
        <div className="grid items-start gap-4 lg:grid-cols-[22rem_1fr]">
          <Feed items={items} total={feed.data?.total ?? items.length} selected={selected} onSelect={(id) => update({ id })} />
          {selected && <DeviationCard key={selected.id} objectId={objectId} deviation={selected} />}
        </div>
      )}
    </section>
  );
}

function Filters({
  preset,
  code,
  severity,
  from,
  to,
  onChange,
}: {
  preset: StatusPreset;
  code: string;
  severity: string;
  from: string;
  to: string;
  onChange: (changes: Record<string, string | null>) => void;
}) {
  const field = "rounded border border-ink/20 bg-white px-2 py-1";
  return (
    <div className="flex flex-wrap items-end gap-3 rounded-lg border border-ink/10 bg-white/60 p-3 text-sm">
      <div className="flex gap-1">
        {(Object.keys(STATUS_PRESETS) as StatusPreset[]).map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => onChange({ status: key === "all" ? null : key })}
            className={`rounded px-2 py-1 ${key === preset ? "bg-ink text-white" : "hover:bg-ink/10"}`}
          >
            {STATUS_PRESETS[key].label}
          </button>
        ))}
      </div>
      <label className="flex flex-col gap-0.5">
        <span className="text-muted">Код</span>
        <select value={code} onChange={(e) => onChange({ code: e.target.value || null })} className={field}>
          <option value="">все</option>
          {CODES.map((c) => (
            <option key={c} value={c}>
              {c} — {label(ru.deviationCode, c)}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-0.5">
        <span className="text-muted">Серьёзность</span>
        <select
          value={severity}
          onChange={(e) => onChange({ severity: e.target.value || null })}
          className={field}
        >
          <option value="">любая</option>
          {SEVERITY_ORDER.map((s) => (
            <option key={s} value={s}>
              {label(ru.severity, s)}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-0.5">
        <span className="text-muted">С</span>
        <input type="date" value={from} onChange={(e) => onChange({ from: e.target.value || null })} className={field} />
      </label>
      <label className="flex flex-col gap-0.5">
        <span className="text-muted">По</span>
        <input type="date" value={to} onChange={(e) => onChange({ to: e.target.value || null })} className={field} />
      </label>
    </div>
  );
}

/** Лента по дням начала эпизода; внутри дня — как отдал API, новые сверху. */
function Feed({
  items,
  total,
  selected,
  onSelect,
}: {
  items: DeviationRead[];
  total: number;
  selected: DeviationRead | null;
  onSelect: (id: string) => void;
}) {
  const days = new Map<string, DeviationRead[]>();
  for (const item of items) {
    const day = formatDay(item.first_seen_at);
    days.set(day, [...(days.get(day) ?? []), item]);
  }
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted">
        Отклонений: {total}
        {total > items.length && `, показаны последние ${items.length}`}
      </p>
      {[...days].map(([day, group]) => (
        <div key={day} className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">{day}</p>
          {group.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item.id)}
              className={`block w-full rounded-lg border p-3 text-left text-sm ${
                item.id === selected?.id
                  ? "border-accent bg-white"
                  : "border-ink/10 bg-white/60 hover:border-ink/30"
              }`}
            >
              <div className="flex flex-wrap items-center gap-1.5">
                <Badge tone={severityTone(item.severity)}>{item.code}</Badge>
                <Badge tone={deviationStatusTone(item.status)}>{label(ru.deviationStatus, item.status)}</Badge>
                <span className="ml-auto text-xs tabular-nums text-muted">
                  {formatClock(item.first_seen_at)}–{formatClock(item.last_seen_at)}
                </span>
              </div>
              <p className="mt-1 font-medium">{item.title}</p>
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}
