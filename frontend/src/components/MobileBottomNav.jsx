import { FolderCog, History, Search } from "lucide-react";

const items = [
  { id: "search", label: "Search", icon: Search },
  { id: "history", label: "History", icon: History },
  { id: "categories", label: "Categories", icon: FolderCog },
];

export function MobileBottomNav({ active, onChange }) {
  return (
    <nav className="bottom-nav" aria-label="Primary navigation">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <button
            key={item.id}
            type="button"
            className={active === item.id ? "active" : ""}
            onClick={() => onChange(item.id)}
          >
            <Icon size={20} />
            <span>{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

