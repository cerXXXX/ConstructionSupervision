import { NavLink, Outlet } from "react-router-dom";

import { ru } from "@/shared/locale/ru";

/** Общая рамка всех экранов: шапка, навигация, место под содержимое. */
export function Layout() {
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="border-b border-ink/10">
        <div className="mx-auto flex max-w-6xl flex-col gap-1 px-6 py-4">
          <h1 className="text-xl font-semibold">{ru.app.title}</h1>
          <p className="text-sm text-muted">{ru.app.subtitle}</p>
        </div>
        <nav className="mx-auto max-w-6xl px-6 pb-3">
          <NavLink
            to="/objects"
            className={({ isActive }) =>
              isActive ? "text-accent font-medium" : "text-muted hover:text-ink"
            }
          >
            {ru.nav.objects}
          </NavLink>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
