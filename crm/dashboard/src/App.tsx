import { Navigate, Outlet, Route, Routes } from "react-router";
import { PageFrame } from "./components/PageFrame";
import { RequireWorker } from "./components/RequireWorker";
import { StateMessage } from "./components/StateMessage";
import { CasePage } from "./pages/CasePage";
import { ConfigurationPage } from "./pages/ConfigurationPage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { ImprovementPage } from "./pages/ImprovementPage";
import { QueuePage } from "./pages/QueuePage";
import { RecipePage } from "./pages/RecipePage";
import { ScoreboardPage } from "./pages/ScoreboardPage";
import { SettingsPage } from "./pages/SettingsPage";
import { SignInPage } from "./pages/SignInPage";
import { VersionPage } from "./pages/VersionPage";
import {
  CASE_PAGE,
  CONFIGURATION,
  EVALUATION_PAGE,
  IMPROVEMENT,
  INSTRUCTIONS,
  QUEUE,
  RECIPE_PAGE,
  SCOREBOARD,
  SETTINGS,
  SIGN_IN,
  VERSION_PAGE,
} from "./paths";

export function App() {
  return (
    <Routes>
      <Route path={SIGN_IN} element={<SignInPage />} />
      <Route
        element={
          <RequireWorker>
            <PageFrame>
              <Outlet />
            </PageFrame>
          </RequireWorker>
        }
      >
        <Route path={QUEUE} element={<QueuePage />} />
        <Route path={CASE_PAGE} element={<CasePage />} />
        <Route path={SCOREBOARD} element={<ScoreboardPage />} />
        <Route path={EVALUATION_PAGE} element={<EvaluationPage />} />
        <Route path={IMPROVEMENT} element={<ImprovementPage />} />
        <Route path={RECIPE_PAGE} element={<RecipePage />} />
        <Route path={CONFIGURATION} element={<ConfigurationPage />} />
        <Route path={VERSION_PAGE} element={<VersionPage />} />
        <Route path={SETTINGS} element={<SettingsPage />} />
        <Route
          path={INSTRUCTIONS}
          element={<Navigate to={CONFIGURATION} replace />}
        />
        <Route
          path="*"
          element={
            <StateMessage empty="Page not found. Choose a page from the header." />
          }
        />
      </Route>
    </Routes>
  );
}
