export function LoadingState() {
  return (
    <div className="loading-state" role="status">
      <span className="spinner" />
      <div>
        <strong>Scanning recent signals</strong>
        <p>Checking public feeds from the last 30 days.</p>
      </div>
    </div>
  );
}

