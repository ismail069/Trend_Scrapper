import { EmptyState } from "./EmptyState";
import { ResultCard } from "./ResultCard";

export function ResultList({ results }) {
  if (!results.length) {
    return (
      <EmptyState
        title="No recent results"
        message="The configured public sources did not return a matching item. Try a broader topic."
      />
    );
  }
  return (
    <div className="result-list">
      {results.map((result) => (
        <ResultCard key={result.id} result={result} />
      ))}
    </div>
  );
}

