import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiPost } from "@/shared/api/client";
import { objectQuery, statusQuery } from "@/shared/api/queries";
import type { AnalysisSchema, SiteSchema } from "@/shared/api/schemas";

/** Сколько последних снимков показывать на дашборде. */
const LATEST_IMAGES = 4;

export type StageAtRisk = {
  stageId: string;
  name: string;
  planEnd: string | null;
  forecastEnd: string | null;
  delayDays: number | null;
};

/**
 * Вехи в риске приходят объектами без схемы (`stages_at_risk: object[]`), поэтому поля
 * разбираются здесь с проверкой типа, а не приведением: неизвестная форма даст прочерк.
 */
export function stagesAtRisk(items: ReadonlyArray<Record<string, unknown>>): StageAtRisk[] {
  const text = (v: unknown) => (typeof v === "string" ? v : null);
  const number = (v: unknown) => (typeof v === "number" ? v : null);
  return items.map((item) => ({
    stageId: text(item.stage_id) ?? "",
    name: text(item.name) ?? "—",
    planEnd: text(item.plan_end),
    forecastEnd: text(item.forecast_end),
    delayDays: number(item.delay_days),
  }));
}

export function useDashboard(objectId: string) {
  const object = useQuery(objectQuery(objectId));
  const status = useQuery(statusQuery(objectId));
  return { object, status };
}

/**
 * Пересчёт по кнопке: прогон с ожиданием, затем свежие выводы на всех экранах.
 *
 * Считается на тот же момент `as_of`, что и показанный статус: кнопка отвечает на вопрос
 * «что изменилось после правки настроек», а не сдвигает момент анализа. Без статуса момент
 * выбирает analysis.
 */
export function useRecompute(objectId: string, asOf: string | null | undefined) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiPost<AnalysisSchema<"RunRead">>("/analysis/runs?wait=true", {
        object_id: objectId,
        triggered_by: "MANUAL",
        as_of: asOf ?? null,
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["analysis"] }),
  });
}

/**
 * Последние снимки объекта. Список отдаётся по возрастанию времени съёмки, поэтому сначала
 * берётся общее число, затем хвост; ссылка на файл есть только в карточке снимка.
 */
export function useLatestImages(objectId: string) {
  const base = `/site/images?object_id=${objectId}&status=ANALYZED`;
  const count = useQuery({
    queryKey: ["site", "images", objectId, "count"],
    queryFn: ({ signal }) => apiGet<SiteSchema<"Page_ImageRead_">>(`${base}&limit=1`, signal),
  });
  const total = count.data?.total ?? 0;
  const tail = useQuery({
    queryKey: ["site", "images", objectId, "tail", total],
    enabled: total > 0,
    queryFn: ({ signal }) =>
      apiGet<SiteSchema<"Page_ImageRead_">>(
        `${base}&limit=${LATEST_IMAGES}&offset=${Math.max(0, total - LATEST_IMAGES)}`,
        signal,
      ),
  });
  const ids = [...(tail.data?.items ?? [])].reverse().map((i) => i.id);
  const details = useQueries({
    queries: ids.map((id) => ({
      queryKey: ["site", "image", id],
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        apiGet<SiteSchema<"ImageDetail">>(`/site/images/${id}`, signal),
    })),
  });
  return {
    isPending: count.isPending || (total > 0 && tail.isPending),
    error: count.error ?? tail.error,
    total,
    images: details.flatMap((d) => (d.data ? [d.data] : [])),
  };
}
