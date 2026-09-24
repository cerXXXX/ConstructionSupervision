import type { ReactNode } from "react";

import { ApiError } from "@/shared/api/client";
import { ru } from "@/shared/locale/ru";

/** Загрузка: одна строка, без скелетонов — данных немного, ответ быстрый. */
export function Loading() {
  return <p className="text-muted">{ru.states.loading}</p>;
}

/** Пусто — всегда с объяснением, почему и что сделать: пустота без слов — дефект. */
export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-ink/20 p-6 text-muted">{children}</div>
  );
}

/**
 * Ошибка API: сообщение сервиса и `request_id` мелким шрифтом — по нему ошибку находят
 * в логах за секунды (apps/web/README.md, §5).
 */
export function ErrorBox({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const api = error instanceof ApiError ? error : null;
  return (
    <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-900">
      <p className="font-medium">{ru.states.error}</p>
      <p>{api?.message ?? (error instanceof Error ? error.message : String(error))}</p>
      {api?.requestId && (
        <p className="mt-1 text-xs text-red-800/70">
          {ru.states.requestId}: {api.requestId}
        </p>
      )}
      {onRetry && (
        <button type="button" onClick={onRetry} className="mt-2 text-sm underline">
          {ru.states.retry}
        </button>
      )}
    </div>
  );
}
