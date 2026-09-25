/**
 * Запросы, которые нужны нескольким экранам. Ключи кэша — `[сервис, ресурс, …]`: после
 * пересчёта достаточно сбросить всё, что начинается с `["analysis"]`.
 */
import { queryOptions } from "@tanstack/react-query";

import { ApiError, apiGet } from "@/shared/api/client";
import type { AnalysisSchema, PlanSchema, SiteSchema } from "@/shared/api/schemas";

export type ObjectRead = PlanSchema<"ObjectRead">;
export type ObjectStatus = AnalysisSchema<"ObjectStatusRead">;
export type CameraRead = SiteSchema<"CameraRead">;
export type ZoneRead = SiteSchema<"ZoneRead">;
export type ImageRead = SiteSchema<"ImageRead">;
export type ImageDetail = SiteSchema<"ImageDetail">;

// Камер и зон у объекта единицы, снимков в демо — десятки: одной страницы в 200 хватает.
// Больше 200 снимков у камеры — экран покажет последние 200 и скажет об этом.
const PAGE = 200;

/** Камеры объекта, включая выключенные: на экране они видны, но помечены. */
export function camerasQuery(objectId: string) {
  return queryOptions({
    queryKey: ["site", "cameras", objectId],
    queryFn: ({ signal }) =>
      apiGet<SiteSchema<"Page_CameraRead_">>(
        `/site/cameras?object_id=${objectId}&limit=${PAGE}`,
        signal,
      ),
  });
}

/** Активные зоны одной камеры. */
export function zonesQuery(cameraId: string) {
  return queryOptions({
    queryKey: ["site", "zones", cameraId],
    queryFn: ({ signal }) =>
      apiGet<SiteSchema<"Page_ZoneRead_">>(`/site/zones?camera_id=${cameraId}&limit=${PAGE}`, signal),
  });
}

/** Участки объекта: какие подписи уже есть — чтобы связать зоны разных камер одним участком. */
export function areasQuery(objectId: string) {
  return queryOptions({
    queryKey: ["site", "areas", objectId],
    queryFn: ({ signal }) =>
      apiGet<SiteSchema<"ObjectAreas">>(`/site/objects/${objectId}/areas`, signal),
  });
}

/** Карточка снимка: presigned-ссылка, размер кадра, рамки детекций. */
export function imageQuery(imageId: string) {
  return queryOptions({
    queryKey: ["site", "image", imageId],
    queryFn: ({ signal }) => apiGet<ImageDetail>(`/site/images/${imageId}`, signal),
  });
}

/** Русские названия классов техники из plan: в коде интерфейса классов нет (AGENTS.md, §2). */
export const equipmentClassesQuery = queryOptions({
  queryKey: ["plan", "equipment-classes"],
  queryFn: ({ signal }) =>
    apiGet<PlanSchema<"Page_EquipmentClassRead_">>(`/plan/equipment-classes?limit=${PAGE}`, signal),
  select: (page) => new Map(page.items.map((c) => [c.code, c.name_ru])),
  staleTime: Infinity,
});

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
