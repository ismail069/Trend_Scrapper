import { Search, Sparkles } from "lucide-react";

export function PromptInput({
  prompt,
  setPrompt,
  category,
  setCategory,
  categories,
  onSubmit,
  loading,
  error,
}) {
  return (
    <section className="hero-card">
      <div className="hero-copy">
        <span className="live-pill">
          <Sparkles size={14} />
          AI-assisted research
        </span>
        <h2>What is gaining attention right now?</h2>
        <p>Search public feed signals published during the last 30 days.</p>
      </div>
      <form onSubmit={onSubmit} className="prompt-form">
        <label htmlFor="prompt">Topic or research prompt</label>
        <textarea
          id="prompt"
          rows="4"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="Example: practical uses of small language models"
          maxLength={500}
          disabled={loading}
        />
        <div className="prompt-options">
          <label htmlFor="category">Category</label>
          <select
            id="category"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            disabled={loading}
          >
            {categories.map((item) => (
              <option key={item.id} value={item.name}>
                {item.name}
              </option>
            ))}
          </select>
        </div>
        {error ? <p className="field-error">{error}</p> : null}
        <button className="primary-button" type="submit" disabled={loading}>
          <Search size={19} />
          {loading ? "Searching..." : "Run Feed Scrapper"}
        </button>
      </form>
    </section>
  );
}

