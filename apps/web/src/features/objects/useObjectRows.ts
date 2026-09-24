import { useQueries, useQuery } from "@tanstack/react-query";

import { openDeviations } from "@/entities/status";
import { type ObjectRead, type ObjectStatus, objectsQuery, statusQuery } from "@/shared/api/queries";

export type ObjectRow = {
  object: ObjectRead;
  /** undefined — статус ещё грузится, null — прогона не было. */
  status: ObjectStatus | null | undefined;
  statusError: unknown;
  openDeviations: number | null;
};

/**
 * Строки списка: объект из plan и его статус из analysis. Статусы грузятся параллельно и
 * не задерживают список: объект виден сразу, статус дорисовывается.
 */
export function useObjectRows() {
  const objects = useQuery(objectsQuery);
  const items = objects.data?.items ?? [];
  const statuses = useQueries({ queries: items.map((o) => statusQuery(o.id)) });

  const rows: ObjectRow[] = items.map((object, i) => {
    const status = statuses[i]?.data;
    return {
      object,
      status,
      statusError: statuses[i]?.error ?? null,
      openDeviations: status ? openDeviations(status.deviations) : null,
    };
  });
  return { objects, rows };
}
