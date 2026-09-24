import type { ReactNode } from "react";

/** Бейдж статуса: цвет задаёт вызывающий, чтобы значения перечислений не жили здесь. */
export function Badge({ tone, children }: { tone: string; children: ReactNode }) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-sm font-medium ${tone}`}>
      {children}
    </span>
  );
}
