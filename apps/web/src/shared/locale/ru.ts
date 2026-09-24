/**
 * Общие русские строки интерфейса: названия перечислений, состояния экранов, единицы.
 * Строки конкретного экрана пишутся прямо в JSX (apps/web/README.md, §5). Названия значений
 * перечислений повторяют enums.yaml: новое значение без строки здесь покажется как есть.
 */
export const ru = {
  app: {
    title: "СтройКонтроль",
    subtitle: "Мониторинг строительной площадки по снимкам камер",
  },
  nav: {
    objects: "Объекты",
  },
  states: {
    loading: "Загружаем данные…",
    empty: "Данных пока нет",
    error: "Не удалось загрузить данные",
    requestId: "Идентификатор запроса",
    retry: "Повторить",
  },
  notFound: {
    title: "Страница не найдена",
    hint: "Проверьте адрес или вернитесь к списку объектов.",
  },
  units: {
    workDays: "раб. дн.",
  },
  objectType: {
    RESIDENTIAL_MONOLITH: "Жилой монолитный дом",
    RESIDENTIAL_PANEL: "Жилой панельный дом",
    PUBLIC_BUILDING: "Общественное здание",
    ROAD: "Дорога",
  } as Record<string, string>,
  objectLifecycle: {
    DRAFT: "Черновик",
    ACTIVE: "В работе",
    ARCHIVED: "В архиве",
  } as Record<string, string>,
  objectStatus: {
    ON_TRACK: "В графике",
    DELAY: "Отставание",
    AHEAD: "Опережение",
    UNKNOWN: "Недостаточно данных",
  } as Record<string, string>,
  confidence: {
    LOW: "низкая",
    MEDIUM: "средняя",
    HIGH: "высокая",
  } as Record<string, string>,
  severity: {
    HIGH: "Высокая",
    MEDIUM: "Средняя",
    LOW: "Низкая",
    INFO: "Инфо",
  } as Record<string, string>,
  stageFactStatus: {
    NOT_STARTED: "не начаты",
    IN_PROGRESS: "в работе",
    DONE: "завершены",
    LATE: "с опозданием",
    AHEAD: "с опережением",
  } as Record<string, string>,
} as const;

/** Название значения перечисления; неизвестное значение показывается как есть, а не пропадает. */
export function label(names: Record<string, string>, value: string | null | undefined): string {
  if (value == null) return "—";
  return names[value] ?? value;
}
