import { ru } from "@/shared/locale/ru";

/** Неизвестный маршрут: SPA отдаётся на любой путь, поэтому объясняем, что произошло. */
export function NotFoundScreen() {
  return (
    <section className="space-y-2">
      <h2 className="text-lg font-semibold">{ru.notFound.title}</h2>
      <p className="text-muted">{ru.notFound.hint}</p>
    </section>
  );
}
