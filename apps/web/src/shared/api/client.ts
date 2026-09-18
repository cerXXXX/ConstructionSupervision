/**
 * Обёртка над HTTP-вызовами к API.
 *
 * Единственное место, где интерфейс знает про конверт ошибки
 * `{"error": {code, message, details, request_id}}` и про ключ доступа.
 * Типы ответов сюда придут из `packages/ts-api-client` (задача D-04);
 * дублировать их руками нельзя.
 */

/** Ошибка API в том виде, в каком её показывают пользователю. */
export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly requestId: string | null,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Путь относительный: в проде статику и API отдаёт один gateway, в разработке
// запрос проксирует Vite. Абсолютный адрес сервиса в коде — ошибка.
const API_BASE = "/api/v1";
const API_KEY = import.meta.env.VITE_API_KEY ?? "dev-key-change-me";

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "X-API-Key": API_KEY },
    signal,
  });

  if (!response.ok) {
    throw await toApiError(response);
  }
  return (await response.json()) as T;
}

async function toApiError(response: Response): Promise<ApiError> {
  // Ответ мог прийти не от сервиса, а от gateway или прокси — тогда это
  // не наш конверт, и придумывать код ошибки за него мы не станем.
  try {
    const payload = (await response.json()) as {
      error?: { code?: string; message?: string; request_id?: string };
    };
    const error = payload.error;
    if (error?.message) {
      return new ApiError(
        error.code ?? "UNKNOWN",
        error.message,
        error.request_id ?? null,
        response.status,
      );
    }
  } catch {
    // тело не JSON — ниже вернём ошибку по коду ответа
  }
  return new ApiError("HTTP_ERROR", `HTTP ${response.status}`, null, response.status);
}
