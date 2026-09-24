const state = {
  userId: 1,
  categories: [],
  transactions: [],
  period: new Date().toISOString().slice(0, 7),
};

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dateFormat = new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" });

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join("; ")
      : data.detail;
    throw new Error(detail || "Não foi possível concluir a operação.");
  }
  return data;
}

function notify(message, isError = false) {
  const notice = document.querySelector("#notice");
  notice.textContent = message;
  notice.classList.toggle("error", isError);
  notice.hidden = false;
  clearTimeout(notice.timer);
  notice.timer = setTimeout(() => { notice.hidden = true; }, 4500);
}

function periodParts() {
  const [year, month] = state.period.split("-").map(Number);
  return { year, month };
}

function periodBounds() {
  const { year, month } = periodParts();
  const end = new Date(Date.UTC(year, month, 0));
  return {
    start: `${state.period}-01`,
    end: end.toISOString().slice(0, 10),
  };
}

function switchView(viewName) {
  document.querySelectorAll(".view").forEach((view) => {
    const active = view.id === viewName;
    view.classList.toggle("active", active);
    view.hidden = !active;
  });
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewName);
  });
  const titles = {
    dashboard: "Visão geral",
    transactions: "Movimentações",
    categories: "Categorias",
    assistant: "Assistente",
  };
  document.querySelector("#page-title").textContent = titles[viewName];
}

async function loadCategories() {
  state.categories = await api("/categories");
  renderCategories();
  updateTransactionCategoryOptions();
}

function renderCategories() {
  const list = document.querySelector("#category-list");
  if (!state.categories.length) {
    list.innerHTML = '<p class="empty">Nenhuma categoria cadastrada.</p>';
    return;
  }
  list.innerHTML = state.categories.map((category) => `
    <div class="category-item">
      <div><strong>${escapeHtml(category.name)}</strong><small>${category.type === "EXPENSE" ? "Despesa" : "Receita"}</small></div>
      <div>
        <button class="icon-button" data-edit-category="${category.id}">Editar</button>
        <button class="icon-button danger" data-delete-category="${category.id}">Excluir</button>
      </div>
    </div>`).join("");
}

function updateTransactionCategoryOptions() {
  const type = document.querySelector("#transaction-type").value;
  const select = document.querySelector("#transaction-category");
  const selected = select.value;
  const matching = state.categories.filter((category) => category.type === type);
  select.innerHTML = matching.map((category) =>
    `<option value="${category.id}">${escapeHtml(category.name)}</option>`
  ).join("");
  if (matching.some((category) => String(category.id) === selected)) select.value = selected;
}

async function loadTransactions() {
  const bounds = periodBounds();
  const type = document.querySelector("#transaction-filter").value;
  const query = new URLSearchParams({ start_date: bounds.start, end_date: bounds.end, limit: "100" });
  if (type) query.set("type", type);
  const page = await api(`/users/${state.userId}/transactions?${query}`);
  state.transactions = page.items;
  renderTransactionTable();
  renderRecentTransactions();
}

function transactionAmount(transaction) {
  const sign = transaction.type === "EXPENSE" ? "−" : "+";
  const css = transaction.type === "EXPENSE" ? "expense" : "income";
  return `<span class="amount ${css}">${sign} ${money.format(Number(transaction.amount))}</span>`;
}

function renderTransactionTable() {
  const body = document.querySelector("#transaction-table");
  if (!state.transactions.length) {
    body.innerHTML = '<tr><td colspan="5" class="empty">Nenhuma movimentação no período.</td></tr>';
    return;
  }
  body.innerHTML = state.transactions.map((transaction) => `
    <tr>
      <td>${dateFormat.format(new Date(`${transaction.transaction_date}T00:00:00Z`))}</td>
      <td>${escapeHtml(transaction.description)}</td>
      <td>${escapeHtml(transaction.category)}</td>
      <td>${transactionAmount(transaction)}</td>
      <td class="actions">
        <button class="icon-button" data-edit-transaction="${transaction.id}">Editar</button>
        <button class="icon-button danger" data-delete-transaction="${transaction.id}">Excluir</button>
      </td>
    </tr>`).join("");
}

function renderRecentTransactions() {
  const container = document.querySelector("#recent-transactions");
  if (!state.transactions.length) {
    container.innerHTML = '<p class="empty">Nenhuma movimentação no período.</p>';
    return;
  }
  container.innerHTML = state.transactions.slice(0, 5).map((transaction) => `
    <div class="activity">
      <div><p>${escapeHtml(transaction.description)}</p><small>${escapeHtml(transaction.category)} · ${dateFormat.format(new Date(`${transaction.transaction_date}T00:00:00Z`))}</small></div>
      ${transactionAmount(transaction)}
    </div>`).join("");
}

async function loadSummary() {
  const { year, month } = periodParts();
  const summary = await api(`/users/${state.userId}/financial-summary?year=${year}&month=${month}&average_months=6`);
  document.querySelector("#income-value").textContent = money.format(Number(summary.income));
  document.querySelector("#expense-value").textContent = money.format(Number(summary.expenses));
  document.querySelector("#balance-value").textContent = money.format(Number(summary.balance));
  document.querySelector("#average-value").textContent = money.format(Number(summary.monthly_expense_average));
  renderCategoryChart(summary.expenses_by_category);
}

function renderCategoryChart(items) {
  const chart = document.querySelector("#category-chart");
  if (!items.length) {
    chart.innerHTML = '<p class="empty">Nenhuma despesa no período.</p>';
    return;
  }
  const maximum = Math.max(...items.map((item) => Number(item.total)));
  chart.innerHTML = items.map((item) => `
    <div class="bar-row">
      <div class="bar-meta"><span>${escapeHtml(item.category)}</span><span>${money.format(Number(item.total))}</span></div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max(4, Number(item.total) / maximum * 100)}%"></div></div>
    </div>`).join("");
}

async function refreshAll() {
  try {
    await loadCategories();
    await Promise.all([loadSummary(), loadTransactions()]);
  } catch (error) {
    notify(error.message, true);
  }
}

function resetTransactionForm() {
  document.querySelector("#transaction-form").reset();
  document.querySelector("#transaction-id").value = "";
  document.querySelector("#transaction-date").value = new Date().toISOString().slice(0, 10);
  document.querySelector("#transaction-form-title").textContent = "Nova movimentação";
  document.querySelector("#cancel-transaction").hidden = true;
  updateTransactionCategoryOptions();
}

function resetCategoryForm() {
  document.querySelector("#category-form").reset();
  document.querySelector("#category-id").value = "";
  document.querySelector("#category-form-title").textContent = "Nova categoria";
  document.querySelector("#cancel-category").hidden = true;
}

document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
document.querySelectorAll("[data-go]").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.go)));

document.querySelector("#user-id").addEventListener("change", async (event) => {
  state.userId = Number(event.target.value);
  await refreshAll();
});
document.querySelector("#period").addEventListener("change", async (event) => {
  state.period = event.target.value;
  await Promise.all([loadSummary(), loadTransactions()]).catch((error) => notify(error.message, true));
});
document.querySelector("#transaction-filter").addEventListener("change", () => loadTransactions().catch((error) => notify(error.message, true)));
document.querySelector("#transaction-type").addEventListener("change", updateTransactionCategoryOptions);
document.querySelector("#cancel-transaction").addEventListener("click", resetTransactionForm);
document.querySelector("#cancel-category").addEventListener("click", resetCategoryForm);

document.querySelector("#transaction-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = document.querySelector("#transaction-id").value;
  const payload = {
    type: document.querySelector("#transaction-type").value,
    description: document.querySelector("#transaction-description").value,
    amount: document.querySelector("#transaction-amount").value,
    transaction_date: document.querySelector("#transaction-date").value,
    category_id: Number(document.querySelector("#transaction-category").value),
  };
  try {
    await api(`/users/${state.userId}/transactions${id ? `/${id}` : ""}`, {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    resetTransactionForm();
    await Promise.all([loadSummary(), loadTransactions()]);
    notify(id ? "Movimentação atualizada." : "Movimentação cadastrada.");
  } catch (error) { notify(error.message, true); }
});

document.querySelector("#transaction-table").addEventListener("click", async (event) => {
  const editId = event.target.dataset.editTransaction;
  const deleteId = event.target.dataset.deleteTransaction;
  if (editId) {
    const item = state.transactions.find((transaction) => transaction.id === Number(editId));
    document.querySelector("#transaction-id").value = item.id;
    document.querySelector("#transaction-type").value = item.type;
    updateTransactionCategoryOptions();
    document.querySelector("#transaction-category").value = item.category_id;
    document.querySelector("#transaction-description").value = item.description;
    document.querySelector("#transaction-amount").value = item.amount;
    document.querySelector("#transaction-date").value = item.transaction_date;
    document.querySelector("#transaction-form-title").textContent = "Editar movimentação";
    document.querySelector("#cancel-transaction").hidden = false;
  }
  if (deleteId && confirm("Excluir esta movimentação?")) {
    try {
      await api(`/users/${state.userId}/transactions/${deleteId}`, { method: "DELETE" });
      await Promise.all([loadSummary(), loadTransactions()]);
      notify("Movimentação excluída.");
    } catch (error) { notify(error.message, true); }
  }
});

document.querySelector("#category-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = document.querySelector("#category-id").value;
  const payload = { name: document.querySelector("#category-name").value, type: document.querySelector("#category-type").value };
  try {
    await api(`/categories${id ? `/${id}` : ""}`, { method: id ? "PATCH" : "POST", body: JSON.stringify(payload) });
    resetCategoryForm();
    await loadCategories();
    notify(id ? "Categoria atualizada." : "Categoria cadastrada.");
  } catch (error) { notify(error.message, true); }
});

document.querySelector("#category-list").addEventListener("click", async (event) => {
  const editId = event.target.dataset.editCategory;
  const deleteId = event.target.dataset.deleteCategory;
  if (editId) {
    const item = state.categories.find((category) => category.id === Number(editId));
    document.querySelector("#category-id").value = item.id;
    document.querySelector("#category-name").value = item.name;
    document.querySelector("#category-type").value = item.type;
    document.querySelector("#category-form-title").textContent = "Editar categoria";
    document.querySelector("#cancel-category").hidden = false;
  }
  if (deleteId && confirm("Excluir esta categoria?")) {
    try {
      await api(`/categories/${deleteId}`, { method: "DELETE" });
      await loadCategories();
      notify("Categoria excluída.");
    } catch (error) { notify(error.message, true); }
  }
});

function addMessage(text, cssClass) {
  const message = document.createElement("div");
  message.className = `message ${cssClass}`;
  message.textContent = text;
  document.querySelector("#chat-messages").appendChild(message);
  message.scrollIntoView({ behavior: "smooth", block: "end" });
  return message;
}

async function askFinn(question) {
  const submit = document.querySelector("#chat-submit");
  addMessage(question, "user-message");
  const loading = addMessage("Consultando seus dados e a base de conhecimento…", "assistant-message loading");
  submit.disabled = true;
  try {
    const result = await api(`/users/${state.userId}/chat`, { method: "POST", body: JSON.stringify({ message: question }) });
    loading.remove();
    addMessage(result.answer, "assistant-message");
  } catch (error) {
    loading.textContent = `Não foi possível responder: ${error.message}`;
    loading.classList.remove("loading");
  } finally { submit.disabled = false; }
}

document.querySelector("#chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.querySelector("#chat-input");
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  await askFinn(question);
});
document.querySelectorAll("[data-question]").forEach((button) => button.addEventListener("click", () => askFinn(button.dataset.question)));

document.querySelector("#period").value = state.period;
resetTransactionForm();
refreshAll();
