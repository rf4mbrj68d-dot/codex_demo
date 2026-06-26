(function () {
  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    })[char]);
  }

  function inferMarket(value, fallback = "US") {
    const text = String(value || "").trim().toUpperCase();
    if (/^\d{1,5}(\.HK)?$/.test(text)) return "HK";
    if (/^\d{6}$/.test(text)) return "CN";
    if (/^[A-Z.]+$/.test(text)) return "US";
    return fallback === "US" ? "ALL" : fallback;
  }

  function pageBase() {
    return window.location.protocol === "file:" ? "http://localhost:8765" : "";
  }

  function toFinancialUrl(ticker, market) {
    return `${pageBase()}/index.html?${new URLSearchParams({ ticker, market }).toString()}`;
  }

  function toProfileUrl(query, market, documentType = "auto") {
    return `${pageBase()}/profile.html?${new URLSearchParams({ query, market, document_type: documentType }).toString()}`;
  }

  function toSummaryUrl(ticker, market) {
    return `${pageBase()}/summary.html?${new URLSearchParams({ ticker, market }).toString()}`;
  }

  function renderStatus(title, message, options = {}) {
    const level = options.level === "error" ? "error" : "";
    return `
      <div class="fm-status ${level}">
        <h3>${escapeHtml(title)}</h3>
        <p>${escapeHtml(message)}</p>
      </div>
    `;
  }

  window.FinancialMiningUI = {
    escapeHtml,
    inferMarket,
    pageBase,
    toFinancialUrl,
    toProfileUrl,
    toSummaryUrl,
    renderStatus
  };
  document.documentElement.dataset.fmUi = "ready";
})();
