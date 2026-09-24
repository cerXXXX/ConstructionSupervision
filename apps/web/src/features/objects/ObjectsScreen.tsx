import { Link } from "react-router-dom";

import { formatDelay, formatPlanDate } from "@/entities/format";
import { objectStatusTone } from "@/entities/status";
import { type ObjectRow, useObjectRows } from "@/features/objects/useObjectRows";
import { label, ru } from "@/shared/locale/ru";
import { Badge } from "@/shared/ui/Badge";
import { Empty, ErrorBox, Loading } from "@/shared/ui/QueryState";

/** Список объектов: статус, отставание и открытые отклонения — с какого объекта начать. */
export function ObjectsScreen() {
  const { objects, rows } = useObjectRows();

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold">Объекты</h2>
      {objects.isPending && <Loading />}
      {objects.isError && <ErrorBox error={objects.error} onRetry={() => objects.refetch()} />}
      {objects.isSuccess && rows.length === 0 && (
        <Empty>
          Объектов пока нет. Демо-объект заводит <code>python scripts/seed.py</code>; свой —
          <code> POST /api/v1/plan/objects</code> и импорт или генерация графика.
        </Empty>
      )}
      {rows.length > 0 && (
        <table className="w-full border-collapse text-left">
          <thead className="text-sm text-muted">
            <tr className="border-b border-ink/10">
              <th className="py-2 pr-4 font-normal">Объект</th>
              <th className="py-2 pr-4 font-normal">Начало СМР</th>
              <th className="py-2 pr-4 font-normal">Статус</th>
              <th className="py-2 pr-4 font-normal">Отклонение от графика</th>
              <th className="py-2 font-normal">Открытых отклонений</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <ObjectLine key={row.object.id} row={row} />
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function ObjectLine({ row }: { row: ObjectRow }) {
  const { object, status } = row;
  const archived = object.status === "ARCHIVED";
  return (
    <tr className={`border-b border-ink/10 ${archived ? "opacity-60" : ""}`}>
      <td className="py-3 pr-4">
        <Link to={`/objects/${object.id}`} className="font-medium hover:text-accent">
          {object.name}
        </Link>
        <div className="text-sm text-muted">
          {label(ru.objectType, object.object_type)} · {label(ru.objectLifecycle, object.status)}
        </div>
      </td>
      <td className="py-3 pr-4">{formatPlanDate(object.plan_start)}</td>
      <td className="py-3 pr-4">
        {status === undefined && !row.statusError && <span className="text-muted">…</span>}
        {row.statusError != null && <span className="text-red-800">статус не получен</span>}
        {status === null && <span className="text-muted">анализа ещё не было</span>}
        {status && (
          <Badge tone={objectStatusTone(status.status)}>
            {label(ru.objectStatus, status.status)}
          </Badge>
        )}
      </td>
      <td className="py-3 pr-4">
        {status?.delay_days != null
          ? `${formatDelay(status.delay_days)} ${ru.units.workDays}`
          : "—"}
      </td>
      <td className="py-3">{row.openDeviations ?? "—"}</td>
    </tr>
  );
}
