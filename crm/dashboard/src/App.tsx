import { Link, NavLink, Route, Routes } from "react-router";
import { CasePage } from "./pages/CasePage";
import { InstructionsPage } from "./pages/InstructionsPage";
import { QueuePage } from "./pages/QueuePage";
import { CASE_PAGE } from "./paths";

export function App() {
  return (
    <>
      <header className="header">
        <Link to="/" className="brand">
          CRM <span className="tagline">cases pilot</span>
        </Link>
        <nav className="nav" aria-label="Main">
          <NavLink to="/" end>
            Queue
          </NavLink>
          <NavLink to="/instructions">Instructions</NavLink>
        </nav>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<QueuePage />} />
          <Route path={CASE_PAGE} element={<CasePage />} />
          <Route path="/instructions" element={<InstructionsPage />} />
          <Route path="*" element={<p className="message">Page not found</p>} />
        </Routes>
      </main>
    </>
  );
}
