import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";

import { Layout } from "@/app/Layout";
import { NotFoundScreen } from "@/app/NotFoundScreen";
import { Providers } from "@/app/providers";
import { DashboardScreen } from "@/features/dashboard/DashboardScreen";
import { ObjectsScreen } from "@/features/objects/ObjectsScreen";

/** Корень приложения: провайдеры и маршруты (apps/web/README.md, §3). */
export function App() {
  return (
    <Providers>
      <Router>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Navigate to="/objects" replace />} />
            <Route path="objects" element={<ObjectsScreen />} />
            <Route path="objects/:objectId" element={<DashboardScreen />} />
            <Route path="*" element={<NotFoundScreen />} />
          </Route>
        </Routes>
      </Router>
    </Providers>
  );
}
