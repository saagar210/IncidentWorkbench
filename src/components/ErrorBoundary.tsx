import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught error:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
          padding: "2rem",
          background: "var(--bg-primary, #f9fafb)",
        }}>
          <div style={{
            maxWidth: "500px",
            background: "var(--bg-secondary, white)",
            padding: "2rem",
            borderRadius: "8px",
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            textAlign: "center",
          }}>
            <h1 style={{
              fontSize: "1.5rem",
              fontWeight: "bold",
              marginBottom: "1rem",
              color: "var(--text-primary, #111827)",
            }}>
              Something went wrong
            </h1>
            <p style={{
              color: "var(--text-secondary, #6b7280)",
              marginBottom: "1.5rem",
              lineHeight: "1.5",
            }}>
              The application encountered an unexpected error. Try reloading the page.
            </p>
            {this.state.error && (
              <details style={{
                marginBottom: "1.5rem",
                textAlign: "left",
                background: "#fef2f2",
                padding: "1rem",
                borderRadius: "4px",
                border: "1px solid #fecaca",
              }}>
                <summary style={{ cursor: "pointer", fontWeight: "500", marginBottom: "0.5rem" }}>
                  Error details
                </summary>
                <code style={{
                  fontSize: "0.875rem",
                  color: "#991b1b",
                  display: "block",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}>
                  {this.state.error.toString()}
                </code>
              </details>
            )}
            <button
              onClick={this.handleRetry}
              style={{
                background: "#3b82f6",
                color: "white",
                padding: "0.75rem 1.5rem",
                borderRadius: "6px",
                border: "none",
                fontSize: "1rem",
                fontWeight: "500",
                cursor: "pointer",
                transition: "background 0.2s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#2563eb")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "#3b82f6")}
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
