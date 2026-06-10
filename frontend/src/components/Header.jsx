import { RadioTower } from "lucide-react";

export function Header() {
  return (
    <header className="app-header">
      <div className="brand-mark" aria-hidden="true">
        <RadioTower size={22} />
      </div>
      <div>
        <p className="eyebrow">30-day signal finder</p>
        <h1>Feed Tren Scrapper</h1>
      </div>
    </header>
  );
}

