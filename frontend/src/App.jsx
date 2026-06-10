import { useEffect, useMemo, useState } from "react";
import { api } from "./api/client";
import { CategoryManager } from "./components/CategoryManager";
import { ErrorMessage } from "./components/ErrorMessage";
import { ExportButtons } from "./components/ExportButtons";
import { Header } from "./components/Header";
import { HistoryList } from "./components/HistoryList";
import { LoadingState } from "./components/LoadingState";
import { MobileBottomNav } from "./components/MobileBottomNav";
import { PromptInput } from "./components/PromptInput";
import { ResultList } from "./components/ResultList";
import { useLocalStorage } from "./hooks/useLocalStorage";

const FALLBACK_CATEGORIES = [
  { id: "local-default", name: "Default" },
  { id: "local-trending", name: "Trending" },
];

function mergeById(localItems, remoteItems) {
  const merged = new Map(localItems.map((item) => [item.id, item]));
  remoteItems.forEach((item) => merged.set(item.id, item));
  return [...merged.values()];
}

function mergeCategories(localItems, remoteItems) {
  const merged = new Map(
    localItems.map((item) => [item.name.toLowerCase(), item]),
  );
  remoteItems.forEach((item) => merged.set(item.name.toLowerCase(), item));
  return [...merged.values()].sort((a, b) => a.name.localeCompare(b.name));
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [tab, setTab] = useState("search");
  const [prompt, setPrompt] = useState("");
  const [categories, setCategories] = useLocalStorage(
    "fts.categories",
    FALLBACK_CATEGORIES,
  );
  const [history, setHistory] = useLocalStorage("fts.history", []);
  const [selectedCategory, setSelectedCategory] = useLocalStorage(
    "fts.selectedCategory",
    "Default",
  );
  const [current, setCurrent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [fieldError, setFieldError] = useState("");
  const [appError, setAppError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.allSettled([api.getCategories(), api.getHistory()]).then(
      ([categoriesResult, historyResult]) => {
        if (!active) return;

        if (categoriesResult.status === "fulfilled") {
          setCategories((items) =>
            mergeCategories(items, categoriesResult.value),
          );
        }
        if (historyResult.status === "fulfilled") {
          setHistory((items) =>
            mergeById(items, historyResult.value).sort(
              (a, b) => new Date(b.searched_at) - new Date(a.searched_at),
            ),
          );
        }

        if (
          categoriesResult.status === "rejected" &&
          historyResult.status === "rejected"
        ) {
          setAppError(
            "Backend sync is unavailable. Saved local data is still accessible.",
          );
        } else {
          setAppError("");
        }
      },
    );
    return () => {
      active = false;
    };
  }, [setCategories, setHistory]);

  useEffect(() => {
    if (!categories.some((item) => item.name === selectedCategory)) {
      setSelectedCategory(categories[0]?.name || "Default");
    }
  }, [categories, selectedCategory, setSelectedCategory]);

  const recentHistory = useMemo(
    () =>
      [...history].sort(
        (a, b) => new Date(b.searched_at) - new Date(a.searched_at),
      ),
    [history],
  );

  async function handleSubmit(event) {
    event.preventDefault();
    const cleanPrompt = prompt.trim();
    if (!cleanPrompt) {
      setFieldError("Enter a topic or research prompt.");
      return;
    }
    setFieldError("");
    setAppError("");
    setLoading(true);
    try {
      const response = await api.scrape({
        prompt: cleanPrompt,
        category: selectedCategory,
        days: 30,
      });
      const record = response.history;
      setCurrent(record);
      setHistory((items) => [
        record,
        ...items.filter((item) => item.id !== record.id),
      ]);
    } catch (error) {
      setAppError(error.message);
    } finally {
      setLoading(false);
    }
  }

  function openHistory(item) {
    setCurrent(item);
    setPrompt(item.prompt);
    setSelectedCategory(item.category);
    setTab("search");
  }

  async function deleteHistory(item) {
    try {
      await api.deleteHistory(item.id);
    } catch (error) {
      if (!item.id.startsWith("local-")) {
        setAppError(error.message);
        return;
      }
    }
    setHistory((items) => items.filter((entry) => entry.id !== item.id));
    if (current?.id === item.id) setCurrent(null);
  }

  async function addCategory(name) {
    let category;
    try {
      category = await api.createCategory(name);
    } catch (error) {
      if (!appError) throw error;
      category = { id: `local-${crypto.randomUUID()}`, name };
    }
    setCategories((items) => [...items, category]);
  }

  async function editCategory(category, name) {
    let updated = { ...category, name };
    if (!category.id.startsWith("local-")) {
      updated = await api.updateCategory(category.id, name);
    }
    setCategories((items) =>
      items.map((item) => (item.id === category.id ? updated : item)),
    );
    setHistory((items) =>
      items.map((item) =>
        item.category === category.name
          ? {
              ...item,
              category: name,
              results: item.results.map((result) => ({
                ...result,
                category: name,
              })),
            }
          : item,
      ),
    );
    if (selectedCategory === category.name) setSelectedCategory(name);
  }

  async function deleteCategory(category) {
    if (!category.id.startsWith("local-")) {
      await api.deleteCategory(category.id);
    }
    setCategories((items) => items.filter((item) => item.id !== category.id));
  }

  async function exportCurrent(format) {
    if (!current) return;
    setExporting(true);
    setAppError("");
    try {
      const blob = await api.exportResults(format, {
        prompt: current.prompt,
        category: current.category,
        searched_at: current.searched_at,
        results: current.results,
      });
      downloadBlob(blob, `feed-tren-scrapper.${format}`);
    } catch (error) {
      setAppError(error.message);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="page">
        <Header />
        <main>
          <ErrorMessage message={appError} />
          {tab === "search" ? (
            <>
              <PromptInput
                prompt={prompt}
                setPrompt={setPrompt}
                category={selectedCategory}
                setCategory={setSelectedCategory}
                categories={categories}
                onSubmit={handleSubmit}
                loading={loading}
                error={fieldError}
              />
              {loading ? <LoadingState /> : null}
              {!loading && current ? (
                <section className="results-section">
                  <div className="section-heading results-heading">
                    <div>
                      <p className="eyebrow">Latest research</p>
                      <h2>{current.prompt}</h2>
                      <span>
                        {current.result_count} results · Last 30 days
                      </span>
                    </div>
                    <ExportButtons
                      onExport={exportCurrent}
                      disabled={!current.results.length}
                      exporting={exporting}
                    />
                  </div>
                  {current.warnings?.map((warning) => (
                    <p className="warning-message" key={warning}>
                      {warning}
                    </p>
                  ))}
                  <ResultList results={current.results} />
                </section>
              ) : null}
            </>
          ) : null}
          {tab === "history" ? (
            <section className="panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Saved locally and remotely</p>
                  <h2>Search history</h2>
                </div>
                <span>{recentHistory.length} searches</span>
              </div>
              <HistoryList
                history={recentHistory}
                onOpen={openHistory}
                onDelete={deleteHistory}
              />
            </section>
          ) : null}
          {tab === "categories" ? (
            <CategoryManager
              categories={categories}
              history={history}
              onAdd={addCategory}
              onEdit={editCategory}
              onDelete={deleteCategory}
            />
          ) : null}
        </main>
      </div>
      <MobileBottomNav active={tab} onChange={setTab} />
    </div>
  );
}
