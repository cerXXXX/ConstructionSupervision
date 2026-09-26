/**
 * Цвета и порядок статусов. Порядок серьёзностей — от высокой к низкой, как в ленте
 * отклонений analysis-service; значения — из enums.yaml.
 */

export const SEVERITY_ORDER = ["HIGH", "MEDIUM", "LOW", "INFO"] as const;

const OBJECT_STATUS_TONE: Record<string, string> = {
  ON_TRACK: "bg-emerald-100 text-emerald-900",
  AHEAD: "bg-sky-100 text-sky-900",
  DELAY: "bg-red-100 text-red-900",
  UNKNOWN: "bg-stone-200 text-stone-800",
};

const SEVERITY_TONE: Record<string, string> = {
  HIGH: "bg-red-100 text-red-900",
  MEDIUM: "bg-amber-100 text-amber-900",
  LOW: "bg-yellow-50 text-yellow-900",
  INFO: "bg-stone-200 text-stone-800",
};

const DEVIATION_STATUS_TONE: Record<string, string> = {
  NEW: "bg-accent/15 text-ink",
  CONFIRMED: "bg-red-100 text-red-900",
  REJECTED: "bg-stone-200 text-stone-700 line-through",
  RESOLVED: "bg-emerald-50 text-emerald-900",
};

const STAGE_STATUS_TONE: Record<string, string> = {
  NOT_STARTED: "bg-stone-200 text-stone-800",
  IN_PROGRESS: "bg-amber-100 text-amber-900",
  DONE: "bg-emerald-100 text-emerald-900",
  LATE: "bg-red-100 text-red-900",
  AHEAD: "bg-sky-100 text-sky-900",
};

// Заливка выполненной части полосы на Ганте — тем же цветом, что бейдж статуса вехи.
const STAGE_STATUS_FILL: Record<string, string> = {
  NOT_STARTED: "fill-stone-400",
  IN_PROGRESS: "fill-amber-500",
  DONE: "fill-emerald-600",
  LATE: "fill-red-600",
  AHEAD: "fill-sky-600",
};

export function stageStatusTone(status: string | null | undefined): string {
  return STAGE_STATUS_TONE[status ?? "NOT_STARTED"] ?? STAGE_STATUS_TONE.NOT_STARTED!;
}

export function stageStatusFill(status: string | null | undefined): string {
  return STAGE_STATUS_FILL[status ?? "NOT_STARTED"] ?? STAGE_STATUS_FILL.NOT_STARTED!;
}

export function deviationStatusTone(status: string): string {
  return DEVIATION_STATUS_TONE[status] ?? DEVIATION_STATUS_TONE.RESOLVED!;
}

export function objectStatusTone(status: string | null | undefined): string {
  return OBJECT_STATUS_TONE[status ?? "UNKNOWN"] ?? OBJECT_STATUS_TONE.UNKNOWN!;
}

export function severityTone(severity: string): string {
  return SEVERITY_TONE[severity] ?? SEVERITY_TONE.INFO!;
}

/** Сколько открытых отклонений всего: сумма по серьёзностям. */
export function openDeviations(bySeverity: Record<string, number>): number {
  return Object.values(bySeverity).reduce((sum, n) => sum + n, 0);
}
