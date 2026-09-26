import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";

import { Layout } from "@/app/Layout";
import { NotFoundScreen } from "@/app/NotFoundScreen";
import { Providers } from "@/app/providers";
import { CamerasScreen } from "@/features/cameras/CamerasScreen";
import { DashboardScreen } from "@/features/dashboard/DashboardScreen";
import { DeviationsScreen } from "@/features/deviations/DeviationsScreen";
import { ObjectsScreen } from "@/features/objects/ObjectsScreen";
import { RulesEditorScreen } from "@/features/rules-editor/RulesEditorScreen";
import { ZonesEditorScreen } from "@/features/zones-editor/ZonesEditorScreen";

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
            <Route path="objects/:objectId/deviations" element={<DeviationsScreen />} />
            <Route path="objects/:objectId/cameras" element={<CamerasScreen />} />
            <Route path="objects/:objectId/settings/zones" element={<ZonesEditorScreen />} />
            <Route path="objects/:objectId/settings/rules" element={<RulesEditorScreen />} />
            <Route path="*" element={<NotFoundScreen />} />
          </Route>
        </Routes>
      </Router>
    </Providers>
  );
}
