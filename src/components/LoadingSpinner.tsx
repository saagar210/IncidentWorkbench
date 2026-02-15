interface LoadingSpinnerProps {
  message?: string;
  size?: "small" | "medium" | "large";
}

export function LoadingSpinner({ message = "Loading...", size = "medium" }: LoadingSpinnerProps) {
  const sizes = {
    small: "24px",
    medium: "40px",
    large: "64px",
  };

  const spinnerSize = sizes[size];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        gap: "1rem",
      }}
    >
      <div
        style={{
          width: spinnerSize,
          height: spinnerSize,
          border: "4px solid var(--border-color)",
          borderTop: "4px solid var(--accent)",
          borderRadius: "50%",
          animation: "spin 1s linear infinite",
        }}
      />
      <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>{message}</p>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
