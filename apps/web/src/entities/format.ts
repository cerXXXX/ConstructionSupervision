/**
 * Форматирование чисел и времени для экрана. Время приходит в UTC, показывается по Москве
 * (AGENTS.md, §7); даты плана — без времени и без сдвига пояса.
 */

const MOSCOW = "Europe/Moscow";

const dateTime = new Intl.DateTimeFormat("ru-RU", {
  timeZone: MOSCOW,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const planDate = new Intl.DateTimeFormat("ru-RU", {
  timeZone: "UTC",
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

/** Момент (ISO-8601 UTC) по московскому времени: «20.10.2026, 09:30». */
export function formatMoment(iso: string | null | undefined): string {
  return iso ? dateTime.format(new Date(iso)) : "—";
}

/** Дата плана `YYYY-MM-DD` без сдвига на пояс браузера. */
export function formatPlanDate(value: string | null | undefined): string {
  return value ? planDate.format(new Date(`${value}T00:00:00Z`)) : "—";
}

/** SPI с двумя знаками; null — «не посчитан», а не ноль. */
export function formatSpi(spi: number | null | undefined): string {
  return spi == null ? "—" : spi.toFixed(2);
}

/** Отклонение от графика со знаком: «+14», «−3», «0». */
export function formatDelay(days: number | null | undefined): string {
  if (days == null) return "—";
  if (days > 0) return `+${days}`;
  if (days < 0) return `−${Math.abs(days)}`;
  return "0";
}
