import { EmptyState } from "./EmptyState";
import { HistoryItem } from "./HistoryItem";

export function HistoryList({ history, onOpen, onDelete }) {
  if (!history.length) {
    return (
      <EmptyState
        title="No saved searches"
        message="Every completed feed search will appear here automatically."
      />
    );
  }
  return (
    <div className="history-list">
      {history.map((item) => (
        <HistoryItem
          key={item.id}
          item={item}
          onOpen={onOpen}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}

