/**
 * Progress indicator for Slack rate-limited operations
 */

interface ProgressIndicatorProps {
  fetchedCount: number;
  nextRequestIn: number;
}

export function ProgressIndicator({ fetchedCount, nextRequestIn }: ProgressIndicatorProps) {
  return (
    <div className="progress-indicator">
      <div className="progress-content">
        <span className="progress-count">Fetched {fetchedCount} messages</span>
        {nextRequestIn > 0 && (
          <span className="progress-timer">
            Next request in {nextRequestIn} seconds (rate limit)
          </span>
        )}
      </div>

      <style>{`
        .progress-indicator {
          background: #eff6ff;
          border: 1px solid #3b82f6;
          border-radius: 8px;
          padding: 12px 16px;
          margin: 16px 0;
        }

        .progress-content {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .progress-count {
          font-weight: 600;
          color: #1e40af;
          font-size: 14px;
        }

        .progress-timer {
          color: #3b82f6;
          font-size: 12px;
        }
      `}</style>
    </div>
  );
}
