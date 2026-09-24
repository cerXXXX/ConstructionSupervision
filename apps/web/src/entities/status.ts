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
