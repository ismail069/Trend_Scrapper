import { ExternalLink } from "lucide-react";
import { CategoryBadge } from "./CategoryBadge";

function formatDate(value) {
  if (!value) return "Date unavailable";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(
    new Date(value),
  );
}

export function ResultCard({ result }) {
  return (
    <article className="result-card">
      <div className="card-topline">
        <CategoryBadge>{result.category}</CategoryBadge>
        {result.relevance_score !== null &&
        result.relevance_score !== undefined ? (
          <span className="score">
            {Math.round(result.relevance_score * 100)}% match
          </span>
        ) : null}
      </div>
      <h3>{result.title}</h3>
      <p>{result.summary}</p>
      <footer>
        <span>
          {result.source_name || "Public feed"} · {formatDate(result.published_at)}
        </span>
        {result.source_url ? (
          <a href={result.source_url} target="_blank" rel="noreferrer">
            Open source <ExternalLink size={14} />
          </a>
        ) : null}
      </footer>
    </article>
  );
}

