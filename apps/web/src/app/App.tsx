import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";

import { Layout } from "@/app/Layout";
import { NotFoundScreen } from "@/app/NotFoundScreen";
import { ObjectsScreen } from "@/app/ObjectsScreen";
import { Providers } from "@/app/providers";

/** Корень приложения: провайдеры и маршруты. Экраны появляются по мере задач трека D. */
export function App() {
  return (
    <Providers>
      <Router>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Navigate to="/objects" replace />} />
            <Route path="objects" element={<ObjectsScreen />} />
            <Route path="*" element={<NotFoundScreen />} />
          </Route>
        </Routes>
      </Router>
    </Providers>
  );
}
