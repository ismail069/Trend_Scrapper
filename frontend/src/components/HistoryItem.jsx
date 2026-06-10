import { Clock3, RotateCcw, Trash2 } from "lucide-react";
import { CategoryBadge } from "./CategoryBadge";

export function HistoryItem({ item, onOpen, onDelete }) {
  return (
    <article className="history-item">
      <button className="history-open" type="button" onClick={() => onOpen(item)}>
        <div className="card-topline">
          <CategoryBadge>{item.category}</CategoryBadge>
          <span>{item.result_count} results</span>
        </div>
        <h3>{item.prompt}</h3>
        <p>
          <Clock3 size={14} />
          {new Intl.DateTimeFormat(undefined, {
            dateStyle: "medium",
            timeStyle: "short",
          }).format(new Date(item.searched_at))}
        </p>
        <span className="reopen-label">
          <RotateCcw size={14} /> Reopen results
        </span>
      </button>
      <button
        className="icon-button danger"
        type="button"
        onClick={() => onDelete(item)}
        aria-label={`Delete history for ${item.prompt}`}
      >
        <Trash2 size={18} />
      </button>
    </article>
  );
}

