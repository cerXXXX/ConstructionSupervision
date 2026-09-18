import { ru } from "@/shared/locale/ru";

/**
 * Список объектов. Пока экран пустой и говорит об этом прямо: пустота без
 * объяснения — дефект интерфейса (apps/web/README.md, §5). Данные из
 * `GET /api/v1/plan/objects` подключаются задачей D-03.
 */
export function ObjectsScreen() {
  return (
    <section className="space-y-2">
      <h2 className="text-lg font-semibold">{ru.objects.title}</h2>
      <p className="text-muted">{ru.objects.notReady}</p>
    </section>
  );
}
