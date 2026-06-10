import { useState } from "react";
import { Check, Pencil, Plus, Trash2, X } from "lucide-react";
import { ErrorMessage } from "./ErrorMessage";

const LOCKED = new Set(["Default", "Trending"]);

export function CategoryManager({
  categories,
  history,
  onAdd,
  onEdit,
  onDelete,
}) {
  const [newName, setNewName] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editingName, setEditingName] = useState("");
  const [error, setError] = useState("");

  async function addCategory(event) {
    event.preventDefault();
    if (!newName.trim()) {
      setError("Enter a category name.");
      return;
    }
    try {
      await onAdd(newName.trim());
      setNewName("");
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function saveEdit(category) {
    if (!editingName.trim()) {
      setError("Category name cannot be empty.");
      return;
    }
    try {
      await onEdit(category, editingName.trim());
      setEditingId(null);
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function removeCategory(category) {
    const used = history.some((item) => item.category === category.name);
    if (used) {
      setError("Reassign or delete history using this category first.");
      return;
    }
    try {
      await onDelete(category);
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Organize searches</p>
          <h2>Categories</h2>
        </div>
        <span>{categories.length} total</span>
      </div>
      <form className="inline-form" onSubmit={addCategory}>
        <input
          value={newName}
          onChange={(event) => setNewName(event.target.value)}
          placeholder="New category"
          maxLength={40}
          aria-label="New category name"
        />
        <button className="primary-button compact" type="submit">
          <Plus size={18} /> Add
        </button>
      </form>
      <ErrorMessage message={error} />
      <div className="category-list">
        {categories.map((category) => {
          const locked = LOCKED.has(category.name);
          const used = history.some((item) => item.category === category.name);
          return (
            <div className="category-row" key={category.id}>
              {editingId === category.id ? (
                <input
                  value={editingName}
                  onChange={(event) => setEditingName(event.target.value)}
                  aria-label={`Edit ${category.name}`}
                  autoFocus
                />
              ) : (
                <div>
                  <strong>{category.name}</strong>
                  <small>
                    {used ? "Used in search history" : "No saved searches"}
                  </small>
                </div>
              )}
              <div className="row-actions">
                {editingId === category.id ? (
                  <>
                    <button
                      className="icon-button"
                      type="button"
                      onClick={() => saveEdit(category)}
                      aria-label="Save category"
                    >
                      <Check size={17} />
                    </button>
                    <button
                      className="icon-button"
                      type="button"
                      onClick={() => setEditingId(null)}
                      aria-label="Cancel edit"
                    >
                      <X size={17} />
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      className="icon-button"
                      type="button"
                      onClick={() => {
                        setEditingId(category.id);
                        setEditingName(category.name);
                      }}
                      aria-label={`Edit ${category.name}`}
                    >
                      <Pencil size={17} />
                    </button>
                    <button
                      className="icon-button danger"
                      type="button"
                      onClick={() => removeCategory(category)}
                      disabled={locked || used}
                      title={
                        locked
                          ? "Default categories cannot be deleted"
                          : used
                            ? "Category is used by history"
                            : "Delete category"
                      }
                      aria-label={`Delete ${category.name}`}
                    >
                      <Trash2 size={17} />
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

