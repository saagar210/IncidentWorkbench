import { Suspense, lazy, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ToastContainer } from "./components/Toast";
import { ToastProvider } from "./contexts/ToastContext";
import { useDarkMode } from "./hooks/useDarkMode";
import { useToast } from "./hooks/useToast";
import { resetVault, unlockVault } from "./utils/stronghold";

const DashboardPage = lazy(async () => {
  const mod = await import("./pages/DashboardPage");
  return { default: mod.DashboardPage };
});

const IncidentsPage = lazy(async () => {
  const mod = await import("./pages/IncidentsPage");
  return { default: mod.IncidentsPage };
});

const ClustersPage = lazy(async () => {
  const mod = await import("./pages/ClustersPage");
  return { default: mod.ClustersPage };
});

const ReportsPage = lazy(async () => {
  const mod = await import("./pages/ReportsPage");
  return { default: mod.ReportsPage };
});

const SettingsPage = lazy(async () => {
  const mod = await import("./pages/SettingsPage");
  return { default: mod.SettingsPage };
});

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
          <Suspense
            fallback={
              <div className="route-loading">
                <p>Loading page...</p>
              </div>
            }
          >
            <Routes>
              <Route path="/" element={<Navigate to="/incidents" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/incidents" element={<IncidentsPage />} />
              <Route path="/clusters" element={<ClustersPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </Suspense>
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

          .route-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            color: var(--text-secondary);
          }
        `}</style>
    </>
  );
}

function VaultUnlockScreen({ onUnlocked }: { onUnlocked: () => void }) {
  const [passphrase, setPassphrase] = useState("");
  const [isUnlocking, setIsUnlocking] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleUnlock = async () => {
    setIsUnlocking(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await unlockVault(passphrase);
      onUnlocked();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to unlock vault");
    } finally {
      setIsUnlocking(false);
    }
  };

  const handleReset = async () => {
    setIsResetting(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await resetVault();
      setSuccessMessage("Vault was reset. Enter a new passphrase to continue.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to reset vault");
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="vault-screen">
      <div className="vault-card">
        <h1>Unlock Credentials Vault</h1>
        <p>
          Enter your vault passphrase to access saved Jira and Slack credentials.
          This passphrase is never hardcoded or stored in source code.
        </p>
        <label htmlFor="vault-passphrase">Vault Passphrase</label>
        <input
          id="vault-passphrase"
          type="password"
          value={passphrase}
          onChange={(e) => setPassphrase(e.target.value)}
          placeholder="At least 12 characters"
        />
        <div className="vault-actions">
          <button
            type="button"
            onClick={handleUnlock}
            disabled={isUnlocking || passphrase.trim().length < 12}
          >
            {isUnlocking ? "Unlocking..." : "Unlock Vault"}
          </button>
          <button type="button" className="danger" onClick={handleReset} disabled={isResetting}>
            {isResetting ? "Resetting..." : "Reset Vault"}
          </button>
        </div>
        {errorMessage && <div className="vault-error">{errorMessage}</div>}
        {successMessage && <div className="vault-success">{successMessage}</div>}
      </div>
      <style>{`
        .vault-screen {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
          background: radial-gradient(circle at top, #dbeafe, #f8fafc 55%);
        }

        .vault-card {
          width: 100%;
          max-width: 520px;
          background: #ffffff;
          border: 1px solid #dbeafe;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 15px 40px rgba(15, 23, 42, 0.12);
        }

        .vault-card h1 {
          margin: 0 0 0.75rem 0;
          font-size: 1.5rem;
          color: #0f172a;
        }

        .vault-card p {
          margin: 0 0 1rem 0;
          color: #334155;
          line-height: 1.5;
        }

        .vault-card label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 600;
          color: #1e293b;
        }

        .vault-card input {
          width: 100%;
          padding: 0.65rem 0.75rem;
          border: 1px solid #94a3b8;
          border-radius: 8px;
          font-size: 0.95rem;
        }

        .vault-card input:focus {
          outline: none;
          border-color: #2563eb;
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
        }

        .vault-actions {
          display: flex;
          gap: 0.75rem;
          margin-top: 1rem;
        }

        .vault-actions button {
          border: none;
          border-radius: 8px;
          padding: 0.65rem 1rem;
          font-weight: 600;
          color: #ffffff;
          background: #2563eb;
          cursor: pointer;
        }

        .vault-actions button:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        .vault-actions .danger {
          background: #b91c1c;
        }

        .vault-error {
          margin-top: 1rem;
          padding: 0.7rem;
          background: #fee2e2;
          border: 1px solid #ef4444;
          border-radius: 8px;
          color: #991b1b;
          font-size: 0.9rem;
        }

        .vault-success {
          margin-top: 1rem;
          padding: 0.7rem;
          background: #dcfce7;
          border: 1px solid #16a34a;
          border-radius: 8px;
          color: #166534;
          font-size: 0.9rem;
        }
      `}</style>
    </div>
  );
}

function App() {
  const [vaultUnlocked, setVaultUnlocked] = useState(false);

  if (!vaultUnlocked) {
    return <VaultUnlockScreen onUnlocked={() => setVaultUnlocked(true)} />;
  }

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
