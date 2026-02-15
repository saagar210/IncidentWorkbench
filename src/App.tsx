import { BrowserRouter as Router, Routes, Route, Link, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ToastContainer } from "./components/Toast";
import { ToastProvider } from "./contexts/ToastContext";
import { DashboardPage } from "./pages/DashboardPage";
import { IncidentsPage } from "./pages/IncidentsPage";
import { ClustersPage } from "./pages/ClustersPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { useDarkMode } from "./hooks/useDarkMode";
import { useToast } from "./hooks/useToast";

// Create QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppContent() {
  const { isDark, toggle } = useDarkMode();
  const { toasts, removeToast } = useToast();

  return (
    <>
      <div className="app">
        {/* Sidebar */}
        <nav className="sidebar">
          <div className="sidebar-header">
            <h1>Incident Workbench</h1>
            <button
              onClick={toggle}
              className="theme-toggle"
              title={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDark ? "☀️" : "🌙"}
            </button>
          </div>
          <ul className="nav-menu">
            <li>
              <Link to="/dashboard">Dashboard</Link>
            </li>
            <li>
              <Link to="/incidents">Incidents</Link>
            </li>
            <li>
              <Link to="/clusters">Clusters</Link>
            </li>
            <li>
              <Link to="/reports">Reports</Link>
            </li>
            <li>
              <Link to="/settings">Settings</Link>
            </li>
          </ul>
        </nav>

        {/* Main content */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/incidents" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/incidents" element={<IncidentsPage />} />
            <Route path="/clusters" element={<ClustersPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>

      <ToastContainer toasts={toasts} onRemove={removeToast} />

      <style>{`
        :root {
          --bg-primary: #f9fafb;
          --bg-secondary: #ffffff;
          --text-primary: #111827;
          --text-secondary: #6b7280;
          --border-color: #e5e7eb;
          --accent: #3b82f6;
          --sidebar-bg: #1f2937;
          --sidebar-border: #374151;
          --sidebar-hover: #374151;
        }

        [data-theme="dark"] {
          --bg-primary: #111827;
          --bg-secondary: #1f2937;
          --text-primary: #f9fafb;
          --text-secondary: #9ca3af;
          --border-color: #374151;
          --accent: #60a5fa;
          --sidebar-bg: #0f172a;
          --sidebar-border: #1e293b;
          --sidebar-hover: #1e293b;
        }
          * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
          }

          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: background-color 0.2s, color 0.2s;
          }

          .app {
            display: flex;
            min-height: 100vh;
          }

          .sidebar {
            width: 240px;
            background: var(--sidebar-bg);
            color: white;
            padding: 1.5rem 0;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
          }

          .sidebar-header {
            padding: 0 1.5rem 1.5rem;
            border-bottom: 1px solid var(--sidebar-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
          }

          .sidebar-header h1 {
            font-size: 1.25rem;
            font-weight: 700;
          }

          .theme-toggle {
            background: transparent;
            border: none;
            font-size: 1.25rem;
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 4px;
            transition: background 0.2s;
          }

          .theme-toggle:hover {
            background: var(--sidebar-hover);
          }

          .nav-menu {
            list-style: none;
            margin-top: 1rem;
          }

          .nav-menu li a {
            display: block;
            padding: 0.75rem 1.5rem;
            color: #d1d5db;
            text-decoration: none;
            transition: all 0.2s;
            font-weight: 500;
          }

          .nav-menu li a:hover {
            background: var(--sidebar-hover);
            color: white;
          }

          .main-content {
            flex: 1;
            margin-left: 240px;
            background: var(--bg-primary);
            min-height: 100vh;
          }
        `}</style>
    </>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <Router>
            <AppContent />
          </Router>
        </ToastProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
