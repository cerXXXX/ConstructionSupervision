import { queryOptions, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

import { dayNumber, moscowDay } from "@/features/gantt/layout";
import { ApiError, apiGet } from "@/shared/api/client";
import type { AnalysisSchema, PlanSchema } from "@/shared/api/schemas";

export type Plan = PlanSchema<"Plan">;
export type PlanStage = PlanSchema<"PlanStage">;
export type Progress = AnalysisSchema<"ProgressRead">;
export type StageProgress = AnalysisSchema<"StageProgress">;

/** Веха на диаграмме: план из plan-service и факт с прогнозом из analysis, если он есть. */
export type GanttRow = {
  stage: PlanStage;
  progress: StageProgress | null;
  start: number;
  end: number;
  actualStart: number | null;
  forecastEnd: number | null;
};

/** «Весь план» объекта: вехи по `seq`, связи, критический путь, календарь. */
export function planQuery(objectId: string) {
  return queryOptions({
    queryKey: ["plan", "plan", objectId],
    queryFn: ({ signal }) => apiGet<Plan>(`/plan/objects/${objectId}/plan`, signal),
  });
}

/** Факт и прогноз по вехам; `null` — анализа ещё не было, диаграмма показывает только план. */
export function progressQuery(objectId: string) {
  return queryOptions({
    queryKey: ["analysis", "progress", objectId],
    queryFn: async ({ signal }) => {
      try {
        return await apiGet<Progress>(`/analysis/objects/${objectId}/progress`, signal);
      } catch (error) {
        if (error instanceof ApiError && error.code === "OBJECT_NOT_ANALYZED") return null;
        throw error;
      }
    },
  });
}

export function useGantt(objectId: string) {
  const plan = useQuery(planQuery(objectId));
  const progress = useQuery(progressQuery(objectId));
  const byStage = new Map((progress.data?.stages ?? []).map((p) => [p.stage_id, p]));
  const rows: GanttRow[] = (plan.data?.stages ?? []).map((stage) => {
    const fact = byStage.get(stage.id) ?? null;
    return {
      stage,
      progress: fact,
      start: dayNumber(stage.plan_start),
      end: dayNumber(stage.plan_end),
      actualStart: fact?.actual_start ? dayNumber(fact.actual_start) : null,
      forecastEnd: fact?.forecast_end ? dayNumber(fact.forecast_end) : null,
    };
  });
  const asOf = progress.data?.as_of ?? null;
  return { plan, progress, rows, asOfDay: asOf ? moscowDay(asOf) : null };
}

/** Все даты, которые должны поместиться в окно диаграммы. */
export function rowDays(rows: GanttRow[], asOfDay: number | null): number[] {
  const days = rows.flatMap((r) => [r.start, r.end, r.actualStart, r.forecastEnd]);
  return [...days, asOfDay].filter((d): d is number => d != null);
}

/** Выбранная веха — в адресе (`?stage=`), как на экране правил. */
export function useSelectedRow(rows: GanttRow[]) {
  const [params, setParams] = useSearchParams();
  const selected = rows.find((r) => r.stage.id === params.get("stage")) ?? null;
  const select = (stageId: string | null) =>
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (stageId) next.set("stage", stageId);
        else next.delete("stage");
        return next;
      },
      { replace: true },
    );
  return { selected, select };
}
