/**
 * Запросы, которые нужны нескольким экранам. Ключи кэша — `[сервис, ресурс, …]`: после
 * пересчёта достаточно сбросить всё, что начинается с `["analysis"]`.
 */
import { queryOptions } from "@tanstack/react-query";

import { ApiError, apiGet } from "@/shared/api/client";
import type { AnalysisSchema, PlanSchema } from "@/shared/api/schemas";

export type ObjectRead = PlanSchema<"ObjectRead">;
export type ObjectStatus = AnalysisSchema<"ObjectStatusRead">;

export const objectsQuery = queryOptions({
  queryKey: ["plan", "objects"],
  // Объектов на демо-стенде единицы: одной страницы в 200 хватает с запасом.
  queryFn: ({ signal }) => apiGet<PlanSchema<"Page_ObjectRead_">>("/plan/objects?limit=200", signal),
});

export function objectQuery(objectId: string) {
  return queryOptions({
    queryKey: ["plan", "objects", objectId],
    queryFn: ({ signal }) => apiGet<ObjectRead>(`/plan/objects/${objectId}`, signal),
  });
}

/**
 * Статус объекта; `null` — прогона ещё не было (`OBJECT_NOT_ANALYZED`). Это не ошибка, а
 * состояние объекта: экран объясняет его словами, а не красной плашкой.
 */
export function statusQuery(objectId: string) {
  return queryOptions({
    queryKey: ["analysis", "status", objectId],
    queryFn: async ({ signal }) => {
      try {
        return await apiGet<ObjectStatus>(`/analysis/objects/${objectId}/status`, signal);
      } catch (error) {
        if (error instanceof ApiError && error.code === "OBJECT_NOT_ANALYZED") return null;
        throw error;
      }
    },
  });
}
