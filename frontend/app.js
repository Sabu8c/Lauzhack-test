document.addEventListener("DOMContentLoaded", () => {
  const apiBase = window.API_BASE || "http://127.0.0.1:8000";
  const form = document.getElementById("item-form");
  const input = document.getElementById("item-input");
  const submitBtn = document.getElementById("submit-btn");
  const itemList = document.getElementById("item-list");
  const statusEl = document.getElementById("status-message");
  const footerApiEl = document.getElementById("footer-api-base");

  if (footerApiEl) {
    footerApiEl.textContent = apiBase;
  }

  function setStatus(message, isError = false) {
    if (!statusEl) return;
    statusEl.textContent = message;
    statusEl.className = isError ? "status-message error" : "status-message success";
  }

  function clearStatus() {
    if (!statusEl) return;
    statusEl.textContent = "";
    statusEl.className = "status-message";
  }

  function renderItems(items) {
    itemList.textContent = "";
    if (!items || items.length === 0) {
      const emptyLi = document.createElement("li");
      emptyLi.className = "empty-state";
      emptyLi.textContent = "No items yet.";
      itemList.appendChild(emptyLi);
      return;
    }

    items.forEach((item) => {
      const li = document.createElement("li");
      li.className = "item-row";

      const nameSpan = document.createElement("span");
      nameSpan.className = "item-name";
      nameSpan.textContent = item.name != null ? String(item.name) : "";

      const dateSpan = document.createElement("span");
      dateSpan.className = "item-date";
      if (item.created_at) {
        try {
          dateSpan.textContent = new Date(item.created_at).toLocaleString();
        } catch {
          dateSpan.textContent = String(item.created_at);
        }
      }

      li.appendChild(nameSpan);
      li.appendChild(dateSpan);
      itemList.appendChild(li);
    });
  }

  async function fetchItems() {
    clearStatus();
    try {
      const res = await fetch(`${apiBase}/items`);
      if (!res.ok) {
        throw new Error(`Failed to load items (${res.status} ${res.statusText || ""})`.trim());
      }
      const data = await res.json();
      renderItems(data.items || []);
    } catch (err) {
      setStatus(`Failed to fetch items: ${err.message}`, true);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const name = input.value.trim();
    if (!name) {
      setStatus("Please enter an item name.", true);
      return;
    }

    submitBtn.disabled = true;
    clearStatus();

    try {
      const res = await fetch(`${apiBase}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });

      if (res.status === 422) {
        const errorData = await res.json().catch(() => null);
        const detail = errorData && errorData.detail
          ? (typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail))
          : "Invalid item name (422)";
        throw new Error(detail);
      }

      if (!res.ok) {
        throw new Error(`Failed to create item (${res.status} ${res.statusText || ""})`.trim());
      }

      input.value = "";
      await fetchItems();
    } catch (err) {
      setStatus(`Error: ${err.message}`, true);
    } finally {
      submitBtn.disabled = false;
    }
  }

  if (form) {
    form.addEventListener("submit", handleSubmit);
  }

  fetchItems();
});
