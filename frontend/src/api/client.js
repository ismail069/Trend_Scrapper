const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let message = "The request could not be completed.";
    try {
      const body = await response.json();
      message = body.detail || body.message || message;
    } catch {
      // Keep the generic message for non-JSON failures.
    }
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

export const api = {
  scrape: (payload) =>
    request("/api/scrape", { method: "POST", body: JSON.stringify(payload) }),
  getHistory: () => request("/api/history"),
  deleteHistory: (id) => request(`/api/history/${id}`, { method: "DELETE" }),
  getCategories: () => request("/api/categories"),
  createCategory: (name) =>
    request("/api/categories", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),
  updateCategory: (id, name) =>
    request(`/api/categories/${id}`, {
      method: "PUT",
      body: JSON.stringify({ name }),
    }),
  deleteCategory: (id) =>
    request(`/api/categories/${id}`, { method: "DELETE" }),
  exportResults: async (format, payload) => {
    const response = await fetch(`${API_URL}/api/export/${format}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Could not create the ${format.toUpperCase()} export.`);
    }
    return response.blob();
  },
};

