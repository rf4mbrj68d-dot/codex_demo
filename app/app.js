const API_BASE = "";

const fallbackCompany = {
  id: "US-AAPL",
  cik: "0000320193",
  ticker: "AAPL",
  name: "Apple Inc.",
  market: "US",
  industry: "科技",
  source: "Fallback Demo"
};

let TOP_COMPANIES = [
  { id: "US-AAPL", ticker: "AAPL", name: "Apple Inc.", market: "US", industry: "科技" },
  { id: "US-MSFT", ticker: "MSFT", name: "Microsoft", market: "US", industry: "科技" },
  { id: "US-NVDA", ticker: "NVDA", name: "NVIDIA", market: "US", industry: "科技" },
  { id: "US-BIDU", ticker: "BIDU", name: "Baidu, Inc.", market: "US", industry: "互联网" },
  { id: "US-TSLA", ticker: "TSLA", name: "Tesla", market: "US", industry: "汽车" },
  { id: "CN-SZSE-000001", ticker: "000001", name: "平安银行", market: "CN", industry: "金融" },
  { id: "CN-SSE-600519", ticker: "600519", name: "贵州茅台", market: "CN", industry: "白酒" },
  { id: "CN-SZSE-300750", ticker: "300750", name: "宁德时代", market: "CN", industry: "动力电池" }
];

const SUGGESTED_QUESTIONS = [
  "这家公司主要靠什么赚钱？",
  "现金流质量怎么样？",
  "最大的风险是什么？",
  "和同行相比强不强？"
];

const METRIC_FALLBACKS = {
  revenue: {
    plain: "公司卖产品或提供服务收到的总业务规模。",
    how_to_read: "收入增长通常代表业务规模扩大，但还要结合利润和现金流一起看。"
  },
  net_profit: {
    plain: "扣除成本、费用和税费后，最终留给股东的钱。",
    how_to_read: "净利润增长说明赚钱结果变好，但要警惕一次性收益带来的波动。"
  },
  gross_margin: {
    plain: "卖出产品后，扣除直接成本，还能留下多少钱。",
    how_to_read: "毛利率越高，通常说明产品定价能力或成本控制越强。"
  },
  operating_cashflow: {
    plain: "公司日常经营真正流入或流出的现金。",
    how_to_read: "经营现金流长期为正，通常说明利润更容易落袋为安。"
  },
  receivables: {
    plain: "已经卖出产品或服务，但还没有收回来的钱。",
    how_to_read: "应收账款增长太快，可能说明回款变慢，需要结合收入增速看。"
  },
  inventory: {
    plain: "还没有卖出去的商品、原材料或在产品。",
    how_to_read: "存货过快增加可能意味着销售压力，也可能是公司提前备货。"
  },
  net_margin: {
    plain: "每 100 元收入最终能留下多少净利润。",
    how_to_read: "净利率越高，说明公司整体赚钱效率越强。"
  },
  debt_ratio: {
    plain: "公司资产中有多少是靠负债支撑的。",
    how_to_read: "负债率过高会增加偿债压力，但金融等行业需要结合行业特征判断。"
  }
};

const METRIC_FORMULAS = {
  revenue: "营业收入通常来自利润表，是公司主营业务和其他经营活动形成的收入总额。",
  net_profit: "净利润 = 利润总额 - 所得税费用。",
  gross_margin: "毛利率 = (营业收入 - 营业成本) / 营业收入。",
  operating_cashflow: "经营现金流来自现金流量表，反映经营活动产生的现金流入与流出净额。",
  receivables: "应收账款是公司已经确认收入但尚未收回的客户款项。",
  inventory: "存货包括原材料、在产品、库存商品等。",
  net_margin: "净利率 = 净利润 / 营业收入。",
  debt_ratio: "资产负债率 = 总负债 / 总资产。"
};

const state = {
  backendReady: false,
  market: "ALL",
  launchTicker: "",
  launchMarket: "US",
  company: null,
  companies: [],
  periodType: "annual",
  periods: { annual: [], quarterly: [], reports: [] },
  analysis: null,
  analysisStatus: "idle",
  analysisMessage: "请输入股票代码开始分析。",
  analysisError: null,
  metricDictionary: {},
  activeMetricKey: null,
  metricFormulaVisible: false,
  periodChangeTimer: null,
  analysisRequestSeq: 0,
  intent: ""
};

const nodeIds = [
  "sidebarCompanyName",
  "sidebarCompanyMeta",
  "backendStatus",
  "companyMarket",
  "sidebarSearchInput",
  "sidebarSearchButton",
  "sidebarSearchMessage",
  "annualButton",
  "quarterlyButton",
  "periodSelect",
  "onlineAnalyzeButton",
  "watchButton",
  "recentAnalyses",
  "reportPeriod",
  "companyTitle",
  "companyIndustry",
  "stanceBadge",
  "oneLineSummary",
  "healthScore",
  "peValue",
  "pbValue",
  "marketCapValue",
  "metricsGrid",
  "sourceTag",
  "reportCard",
  "riskRadar",
  "periodCompare",
  "trendCharts",
  "suggestedQuestions",
  "chatLog",
  "questionInput",
  "askButton",
  "metricPopover",
  "metricPopoverClose",
  "metricPopoverTitle",
  "metricPopoverPlain",
  "metricPopoverCurrent",
  "metricFormulaBlock",
  "metricAskButton",
  "metricFormulaButton",
  "industryAnalyzeButton",
  "industryInsight",
  "industryCompare",
  "refreshReportsButton",
  "reportList",
  "refreshWatchlistButton",
  "addAlertButton",
  "watchlist",
  "alertList"
];

const nodes = {};
nodeIds.forEach((id) => {
  nodes[id] = document.querySelector(`#${id}`);
});

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `请求失败：${response.status}`);
  }
  return response.json();
}

async function boot() {
  const launch = getLaunchCompany();
  state.launchTicker = launch.ticker;
  state.launchMarket = launch.market;
  state.market = launch.market;
  state.intent = launch.intent;
  bindEvents();
  renderRecentAnalyses();
  renderSuggestedQuestions();
  hydrateSearchInput(launch.ticker);
  renderAnalysisEmpty();

  try {
    await api("/api/health");
    state.backendReady = true;
    setStatus("后端已连接", "ok");
    await loadMetricDictionary();
    await refreshWatchlist();
    if (launch.ticker) {
      await loadCompany(launch.ticker, launch.market);
    } else {
      setStatus("等待输入", "ok");
    }
  } catch (error) {
    state.backendReady = false;
    setStatus("后端未运行，显示本地 Demo", "error");
    if (launch.ticker) {
      setAnalysisReady(fallbackAnalysis());
      renderSelectedCompany(fallbackCompany);
      renderPeriodOptions(["2022-FY", "2023-FY", "2024-FY"]);
      resetChat();
    }
  }
}

function bindEvents() {
  nodes.annualButton?.addEventListener("click", () => setPeriodType("annual"));
  nodes.quarterlyButton?.addEventListener("click", () => setPeriodType("quarterly"));
  nodes.periodSelect?.addEventListener("change", scheduleAnalysis);
  nodes.onlineAnalyzeButton?.addEventListener("click", analyzeOnline);
  nodes.watchButton?.addEventListener("click", addCurrentToWatchlist);
  nodes.askButton?.addEventListener("click", () => askQuestion());
  nodes.questionInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") askQuestion();
  });
  nodes.sidebarSearchButton?.addEventListener("click", startSidebarSearch);
  nodes.sidebarSearchInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") startSidebarSearch();
  });
  nodes.industryAnalyzeButton?.addEventListener("click", analyzeIndustry);
  nodes.refreshReportsButton?.addEventListener("click", refreshReports);
  nodes.refreshWatchlistButton?.addEventListener("click", refreshWatchlist);
  nodes.addAlertButton?.addEventListener("click", addDefaultAlert);
  nodes.metricPopoverClose?.addEventListener("click", hideMetricPopover);
  nodes.metricAskButton?.addEventListener("click", askActiveMetric);
  nodes.metricFormulaButton?.addEventListener("click", toggleMetricFormula);
  document.addEventListener("click", handleOutsideMetricPopover);
  document.addEventListener("keydown", handleMetricPopoverKeydown);
}

function hydrateSearchInput(ticker) {
  if (nodes.sidebarSearchInput) nodes.sidebarSearchInput.value = ticker || "";
}

function startSidebarSearch() {
  const query = nodes.sidebarSearchInput?.value.trim();
  if (!query) {
    setSidebarMessage("请输入股票代码或公司名。", "error");
    return;
  }
  const market = inferMarket(query);
  const url = new URL(window.location.href);
  url.searchParams.set("ticker", query.toUpperCase());
  url.searchParams.set("market", market);
  url.searchParams.delete("intent");
  window.location.href = url.toString();
}

function setSidebarMessage(text, type = "ok") {
  if (!nodes.sidebarSearchMessage) return;
  nodes.sidebarSearchMessage.textContent = text;
  nodes.sidebarSearchMessage.className = `side-hint ${type === "error" ? "status-error" : "status-ok"}`;
}

function setStatus(text, type) {
  if (!nodes.backendStatus) return;
  nodes.backendStatus.textContent = text;
  nodes.backendStatus.className = type === "ok" ? "status-ok" : "status-error";
}

async function searchCompany() {
  const query = state.launchTicker;
  if (!query) return;
  if (!state.backendReady) {
    state.companies = [fallbackCompany];
    renderSelectedCompany(fallbackCompany);
    return;
  }
  setStatus("搜索中", "ok");
  try {
    const data = await api(`/api/companies/search?q=${encodeURIComponent(query)}&market=${state.market}`);
    state.companies = data.items || [];
    const exact = state.companies.find((item) => item.ticker?.toLowerCase() === query.toLowerCase());
    if (exact || state.companies.length) {
      setStatus("已匹配公司，正在加载财报", "ok");
      await selectCompany(exact || state.companies[0]);
      return;
    }
    setStatus("未找到公司", "error");
    setAnalysisFailed("没有找到可分析的公司，请确认股票代码是否在支持列表内。");
  } catch (error) {
    setStatus(error.message, "error");
    setAnalysisFailed(error.message);
  }
}

async function selectCompany(company) {
  state.company = company;
  setAnalysisLoading("正在切换公司并读取报告期...", true);
  renderSelectedCompany(company);
  await loadPeriods(company.ticker, company.market);
  await refreshReports();
  await analyzeOnline();
}

async function loadCompany(ticker, market) {
  state.launchTicker = ticker;
  state.launchMarket = market;
  state.market = market;
  setAnalysisLoading("正在识别公司并载入披露资料...", true);
  await searchCompany();
}

async function loadPeriods(ticker, market) {
  if (!state.backendReady) return;
  setAnalysisLoading("正在获取可分析的报告期...", true);
  setStatus("获取报告期", "ok");
  try {
    const data = await api(`/api/reports/options?ticker=${encodeURIComponent(ticker)}&market=${market || "US"}`);
    state.company = data.company;
    state.periods = data.periods || { annual: [], quarterly: [], reports: [] };
    renderSelectedCompany(state.company);
    renderPeriodOptions(state.periods[state.periodType] || []);
    renderReports(state.periods.reports || []);
    setStatus("报告期已加载", "ok");
  } catch (error) {
    setStatus(error.message, "error");
    setAnalysisFailed(error.message);
    throw error;
  }
}

async function analyzeOnline() {
  if (!state.company?.ticker && !state.launchTicker) {
    setAnalysisEmptyWithMessage("请输入股票代码后再开始分析。");
    return;
  }
  if (!state.backendReady) {
    setAnalysisReady(fallbackAnalysis());
    return;
  }
  const selected = Array.from(nodes.periodSelect?.selectedOptions || []).map((option) => option.value);
  const requestSeq = ++state.analysisRequestSeq;
  const originalButtonText = nodes.onlineAnalyzeButton?.textContent || "联网获取并分析";
  const periodText = selected.length ? selected.join("、") : "默认报告期";
  setAnalysisLoading(`正在读取 ${state.company?.ticker || state.launchTicker} · ${periodText} 的披露数据并生成分析...`);
  setStatus("财报 Agent 正在准备披露证据", "ok");
  if (nodes.onlineAnalyzeButton) {
    nodes.onlineAnalyzeButton.textContent = "AI 分析中...";
    nodes.onlineAnalyzeButton.disabled = true;
  }
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 210000);
  try {
    const task = await api("/api/financial-agent/analyses", {
      method: "POST",
      signal: controller.signal,
      body: JSON.stringify({
        ticker: state.company?.ticker || state.launchTicker,
        market: state.company?.market || state.launchMarket || "US",
        period_type: state.periodType,
        periods: selected
      })
    });
    const data = await waitForFinancialAnalysis(task.task_id, controller.signal);
    if (requestSeq !== state.analysisRequestSeq) return;
    state.company = data.company || state.company;
    setStatus("分析完成", "ok");
    setAnalysisReady(data);
    resetChat();
    handleWatchIntent();
  } catch (error) {
    if (requestSeq !== state.analysisRequestSeq) return;
    const message = error.name === "AbortError"
      ? "解析超时，请减少选择的报告期或稍后重试"
      : error.message;
    setStatus(message, "error");
    setAnalysisFailed(message);
  } finally {
    window.clearTimeout(timeout);
    if (nodes.onlineAnalyzeButton) {
      nodes.onlineAnalyzeButton.textContent = originalButtonText;
      nodes.onlineAnalyzeButton.disabled = false;
    }
  }
}

async function waitForFinancialAnalysis(taskId, signal) {
  while (true) {
    const task = await api(`/api/financial-agent/tasks/${encodeURIComponent(taskId)}`, { signal });
    if (task.current_step) setStatus(task.current_step, "ok");
    if (task.status === "COMPLETED") {
      return api(`/api/financial-agent/analyses/${encodeURIComponent(task.analysis_id)}`, { signal });
    }
    if (task.status === "FAILED") {
      throw new Error(task.error?.message || "财报 Agent 分析失败");
    }
    await delay(1200, signal);
  }
}

function delay(milliseconds, signal) {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(resolve, milliseconds);
    signal?.addEventListener("abort", () => {
      window.clearTimeout(timer);
      reject(new DOMException("请求已取消", "AbortError"));
    }, { once: true });
  });
}

async function analyzeIndustry() {
  if (!state.backendReady || !state.company) return;
  nodes.industryInsight.textContent = "正在生成行业对比...";
  try {
    const data = await api("/api/analysis/industry-comparison", {
      method: "POST",
      body: JSON.stringify({
        ticker: state.company.ticker,
        market: state.company.market || "US",
        period: state.analysis?.latest_period
      })
    });
    nodes.industryInsight.textContent = data.insight;
    renderIndustryTable(data.rows || []);
  } catch (error) {
    nodes.industryInsight.textContent = error.message;
  }
}

async function refreshReports() {
  if (!state.backendReady || !state.company?.ticker) return;
  try {
    const data = await api(`/api/reports/list?ticker=${encodeURIComponent(state.company.ticker)}&market=${state.company.market || "US"}`);
    renderReports(data.reports || []);
  } catch (error) {
    nodes.reportList.innerHTML = `<div class="source-item"><strong>资料列表暂不可用</strong><p>${escapeHtml(error.message)}</p></div>`;
  }
}

async function loadMetricDictionary() {
  if (!state.backendReady) return;
  const data = await api("/api/metrics/dictionary");
  state.metricDictionary = data.items || {};
  renderMetricDictionary();
}

async function addCurrentToWatchlist() {
  if (!state.backendReady || !state.company) return;
  try {
    await api("/api/watchlists", {
      method: "POST",
      body: JSON.stringify({ company: state.company })
    });
    setStatus("已加入自选", "ok");
    if (nodes.watchButton) nodes.watchButton.textContent = "已加入自选";
    await refreshWatchlist();
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function refreshWatchlist() {
  if (!state.backendReady) return;
  const data = await api("/api/watchlists");
  nodes.watchlist.innerHTML = (data.items || [])
    .map((item) => {
      const company = item.company || {};
      return `
        <button type="button" class="watch-item" data-ticker="${escapeHtml(company.ticker)}" data-market="${escapeHtml(company.market || inferMarket(company.ticker || ""))}">
          <strong>${escapeHtml(company.name || company.ticker)} (${escapeHtml(company.ticker || "--")})</strong>
          <small>${escapeHtml(company.market || "--")} · ${escapeHtml(company.industry || "待识别行业")}</small>
        </button>
      `;
    })
    .join("") || '<div class="source-item"><strong>暂无自选</strong><p>可将当前公司加入自选，后续用于财报更新和风险变化提醒。</p></div>';
  nodes.watchlist.querySelectorAll("[data-ticker]").forEach((item) => {
    item.addEventListener("click", () => navigateToCompany(item.dataset.ticker, item.dataset.market));
  });
  const alerts = await api("/api/watchlists/alerts");
  nodes.alertList.innerHTML = (alerts.items || [])
    .map(
      (item) => `
        <div class="source-item">
          <strong>提醒：${escapeHtml(item.metric)}</strong>
          <small>${escapeHtml(item.company_id)} · ${escapeHtml(item.condition)} ${escapeHtml(item.threshold ?? "")}</small>
        </div>
      `
    )
    .join("");
}

async function addDefaultAlert() {
  if (!state.backendReady || !state.company) return;
  try {
    await api("/api/watchlists/alerts", {
      method: "POST",
      body: JSON.stringify({
        company_id: state.company.id,
        metric: "风险雷达",
        condition: "出现黄色或红色风险时提醒",
        threshold: null
      })
    });
    setStatus("提醒已创建", "ok");
    await refreshWatchlist();
  } catch (error) {
    setStatus(error.message, "error");
  }
}

function renderPeriodOptions(periods) {
  const selected = periods.slice(0, Math.min(2, periods.length));
  nodes.periodSelect.innerHTML = periods
    .map((period) => `<option value="${escapeHtml(period)}" ${selected.includes(period) ? "selected" : ""}>${escapeHtml(period)}</option>`)
    .join("");
}

function setPeriodType(type) {
  state.periodType = type;
  nodes.annualButton.classList.toggle("active", type === "annual");
  nodes.quarterlyButton.classList.toggle("active", type === "quarterly");
  renderPeriodOptions(state.periods[type] || []);
  scheduleAnalysis();
}

function scheduleAnalysis() {
  if (!state.company?.ticker) return;
  window.clearTimeout(state.periodChangeTimer);
  setAnalysisLoading("报告期已变化，正在准备重新分析...", true);
  state.periodChangeTimer = window.setTimeout(() => {
    analyzeOnline();
  }, 350);
}

function render() {
  if (state.analysisStatus === "loading") {
    renderAnalysisLoading(state.analysisMessage);
    return;
  }
  if (state.analysisStatus === "failed") {
    renderAnalysisFailed(state.analysisError);
    return;
  }
  if (!state.analysis) {
    renderAnalysisEmpty();
    return;
  }
  const analysis = state.analysis;
  const company = state.company || analysis.company || fallbackCompany;
  renderCompanyHeader(company, analysis);
  renderMetrics(analysis.metrics || {});
  renderReportCard(company, analysis);
  renderRisks(analysis.risks || []);
  renderComparison(analysis.comparison?.rows || []);
  renderTrendCharts(analysis.comparison?.rows || [], analysis.metrics || {});
}

function setAnalysisLoading(message, invalidateRequests = false) {
  if (invalidateRequests) state.analysisRequestSeq += 1;
  state.analysis = null;
  state.analysisStatus = "loading";
  state.analysisMessage = message || "正在读取披露数据并生成分析...";
  state.analysisError = null;
  render();
}

function setAnalysisReady(analysis) {
  state.analysis = analysis;
  state.analysisStatus = "ready";
  state.analysisMessage = "";
  state.analysisError = null;
  render();
}

function setAnalysisFailed(message) {
  state.analysis = null;
  state.analysisStatus = "failed";
  state.analysisMessage = "";
  state.analysisError = message || "披露资料、网络或模型服务暂时不可用，请稍后重试。";
  render();
}

function setAnalysisEmptyWithMessage(message) {
  state.analysis = null;
  state.analysisStatus = "idle";
  state.analysisMessage = message;
  renderAnalysisEmpty(message);
}

function renderCompanyHeader(company, analysis = {}) {
  const generation = analysis.generation_meta || {};
  const sourceText = generation.llm_model
    ? `DeepSeek Agent · ${generation.cache_status || "已生成"}`
    : (company.source || "公开披露数据");
  nodes.reportPeriod.textContent = analysis.latest_period || "多期分析";
  nodes.companyTitle.textContent = `${company.name || "当前公司"} ${company.ticker ? `(${company.ticker})` : ""}`;
  nodes.oneLineSummary.textContent = analysis.summary || "正在读取公开披露数据、校验财务事实，并生成通俗分析。";
  nodes.healthScore.textContent = analysis.score ?? "--";
  nodes.sourceTag.textContent = sourceText;
  nodes.companyIndustry.textContent = company.industry || "行业待识别";
  nodes.companyMarket.textContent = company.market || state.launchMarket || "待识别";
  nodes.peValue.textContent = analysis.market_data?.pe || "--";
  nodes.pbValue.textContent = analysis.market_data?.pb || "--";
  nodes.marketCapValue.textContent = analysis.market_data?.market_cap || "--";
  renderStance(analysis.stance);
}

function renderAnalysisLoading(message) {
  const company = state.company || { name: "正在识别公司", ticker: state.launchTicker, market: state.launchMarket };
  const selected = Array.from(nodes.periodSelect.selectedOptions || []).map((option) => option.value);
  renderCompanyHeader(company, {
    latest_period: selected.length ? selected.join(" / ") : "报告期载入中",
    summary: message || "正在读取公开披露数据、校验财务事实，并生成通俗分析...",
    score: "--",
    stance: "neutral",
    generation_meta: { llm_model: "DeepSeek Agent", cache_status: "正在联网分析" }
  });
  nodes.stanceBadge.textContent = "分析中";
  renderMetricsSkeleton();
  nodes.reportCard.innerHTML = `
    <div class="analysis-state">
      <h3>正在联网分析</h3>
      <p>${escapeHtml(message || "正在读取公开披露数据、校验财务事实，并生成通俗分析...")}</p>
      <small>当前对象：${escapeHtml(company.ticker || state.launchTicker || "--")} · ${escapeHtml(selected.join("、") || "默认报告期")}</small>
      <div class="analysis-skeleton-lines"><i></i><i></i><i></i></div>
    </div>
  `;
  nodes.riskRadar.innerHTML = skeletonItems(4);
  nodes.periodCompare.innerHTML = `<div class="skeleton-chart"></div>`;
  nodes.trendCharts.innerHTML = `<div class="skeleton-chart"></div>`;
}

function renderAnalysisFailed(message) {
  const company = state.company || { name: "当前公司", ticker: state.launchTicker, market: state.launchMarket };
  renderCompanyHeader(company, {
    latest_period: "分析失败",
    summary: "本次分析没有生成可展示结果。",
    score: "--",
    stance: "cautious"
  });
  nodes.stanceBadge.textContent = "需重试";
  renderMetricsSkeleton();
  nodes.reportCard.innerHTML = `
    <div class="analysis-state failed">
      <h3>分析暂时失败</h3>
      <p>${escapeHtml(message || "披露资料、网络或模型服务暂时不可用，请稍后重试。")}</p>
      <button type="button" class="ghost-button" data-retry-analysis>重新分析</button>
    </div>
  `;
  nodes.reportCard.querySelector("[data-retry-analysis]")?.addEventListener("click", analyzeOnline);
  nodes.riskRadar.innerHTML = `<div class="analysis-state failed"><p>风险雷达暂无本次分析结果。</p></div>`;
  nodes.periodCompare.innerHTML = "本次分析失败，暂无可对比数据。";
  nodes.trendCharts.innerHTML = `<div class="empty-trend">暂无趋势图。</div>`;
}

function renderAnalysisEmpty(message) {
  const company = state.company || { name: "请输入股票代码开始分析", ticker: state.launchTicker, market: state.launchMarket };
  renderCompanyHeader(company, {
    latest_period: "等待分析",
    summary: message || state.analysisMessage || "系统会自动读取披露资料，生成财务指标、AI 体检报告和可追问的问答结果。",
    score: "--",
    stance: "neutral"
  });
  nodes.stanceBadge.textContent = "待分析";
  nodes.metricsGrid.innerHTML = emptyCards();
  nodes.reportCard.innerHTML = `<div class="analysis-state"><p>暂无分析结果。请输入股票代码，或从左侧最近分析选择一家公司。</p></div>`;
  nodes.riskRadar.innerHTML = "";
  nodes.periodCompare.innerHTML = "";
  nodes.trendCharts.innerHTML = `<div class="empty-trend">开始分析后，这里会展示收入、利润和现金流趋势。</div>`;
}

function renderMetricsSkeleton() {
  nodes.metricsGrid.innerHTML = Array.from({ length: 8 }, () => `
    <article class="metric-card skeleton-card">
      <i></i><i></i><i></i>
    </article>
  `).join("");
}

function skeletonItems(count) {
  return Array.from({ length: count }, () => `
    <div class="risk-item skeleton-risk">
      <span class="risk-dot"></span>
      <div><i></i><i></i></div>
    </div>
  `).join("");
}

function emptyCards() {
  return ["营业收入", "净利润", "毛利率", "经营现金流", "应收账款", "存货", "净利率", "资产负债率"]
    .map((label) => `
      <article class="metric-card empty-metric">
        <span>${label}</span>
        <strong>--</strong>
        <small>等待分析</small>
      </article>
    `).join("");
}

function renderStance(stance) {
  const labels = { positive: "偏积极", neutral: "中性", cautious: "偏谨慎" };
  nodes.stanceBadge.className = `stance-badge ${stance || "neutral"}`;
  nodes.stanceBadge.textContent = labels[stance] || "中性";
}

function renderMetrics(metrics) {
  const visible = ["revenue", "net_profit", "gross_margin", "operating_cashflow", "receivables", "inventory", "net_margin", "debt_ratio"];
  nodes.metricsGrid.innerHTML = visible
    .map((key) => {
      const metric = metrics[key] || { label: labelForMetric(key), display: "待补充", yoy: null };
      return `
        <article class="metric-card" data-metric="${key}">
          <span>${escapeHtml(metric.label || labelForMetric(key))}</span>
          <strong>${escapeHtml(metric.display || "待补充")}</strong>
          <small>${metric.yoy === null || metric.yoy === undefined ? "同比待补充" : `同比${pctText(metric.yoy)}`}</small>
          ${renderSparkline(metric.trend || [])}
        </article>
      `;
    })
    .join("");
  nodes.metricsGrid.querySelectorAll("[data-metric]").forEach((card) => {
    card.addEventListener("click", (event) => {
      event.stopPropagation();
      showMetricPopover(card.dataset.metric, card);
    });
  });
}

function renderSparkline(values = []) {
  const nums = values.map((item) => Number(item)).filter((item) => Number.isFinite(item));
  if (nums.length < 2) {
    return '<div class="sparkline muted-spark"><span></span><span></span><span></span></div>';
  }
  const max = Math.max(...nums);
  const min = Math.min(...nums);
  const range = max - min || 1;
  const points = nums.map((value, index) => {
    const x = (index / (nums.length - 1)) * 100;
    const y = 30 - ((value - min) / range) * 24;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return `<svg class="sparkline-svg" viewBox="0 0 100 34" preserveAspectRatio="none"><polyline points="${points}" /></svg>`;
}

function renderReportCard(company, analysis) {
  const sources = analysis.sources || [];
  const sourceText = sources.length
    ? sources.map((item) => item.url
      ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.form)} ${escapeHtml(item.filing_date || "")}</a>`
      : `${escapeHtml(item.form)} ${escapeHtml(item.filing_date || "")}`
    ).join(" · ")
    : "当前分析来自结构化财务数据或本地知识整理层。";
  const factOpinion = analysis.fact_opinion || { facts: [], inferences: [] };
  const rows = [
    ["赚钱能力", analysis.business_model || "待补充业务模式文本。"],
    ["本期表现", analysis.summary],
    ["主要亮点", (analysis.highlights || []).join(" ") || "待补充"],
    ["风险提醒", (analysis.risks || []).filter((risk) => risk.level !== "green").map((risk) => risk.reason).join(" ") || "暂未识别到突出风险。"],
    ["事实依据", (factOpinion.facts || []).join("；") || "待补充"],
    ["后续关注", (analysis.watch_metrics || []).join("、") || "收入、利润、现金流"],
    ["信息来源", sourceText]
  ];
  nodes.reportCard.innerHTML = rows
    .map(([label, value]) => `<div class="card-row"><strong>${escapeHtml(label)}</strong><div>${value}</div></div>`)
    .join("");
}

function renderRisks(risks) {
  nodes.riskRadar.innerHTML = risks.length
    ? risks.map(
      (risk) => `
        <div class="risk-item ${escapeHtml(risk.level || "")}">
          <span class="risk-dot"></span>
          <div>
            <h3>${escapeHtml(risk.name || "风险项")}</h3>
            <p>${escapeHtml(risk.reason || "待补充")}</p>
          </div>
        </div>
      `
    ).join("")
    : '<div class="analysis-state"><p>暂未识别到突出风险。</p></div>';
}

function renderComparison(rows) {
  if (!rows.length) {
    nodes.periodCompare.innerHTML = "请选择多个年份或季度后点击联网分析。";
    return;
  }
  nodes.periodCompare.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>报告期</th><th>收入</th><th>收入同比</th><th>净利润</th><th>净利同比</th>
          <th>毛利率</th><th>净利率</th><th>ROE</th><th>经营现金流</th><th>负债率</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map((row) => `
          <tr>
            <td>${escapeHtml(row.period)}</td><td>${escapeHtml(row.revenue)}</td>
            <td>${escapeHtml(valueOrPct(row.revenue_yoy))}</td><td>${escapeHtml(row.net_profit)}</td>
            <td>${escapeHtml(valueOrPct(row.net_profit_yoy))}</td><td>${escapeHtml(row.gross_margin)}</td>
            <td>${escapeHtml(row.net_margin || "待补充")}</td><td>${escapeHtml(row.roe || "待补充")}</td>
            <td>${escapeHtml(row.operating_cashflow)}</td><td>${escapeHtml(row.debt_ratio)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderTrendCharts(rows, metrics) {
  const trendDefs = [
    ["revenue", "营业收入"],
    ["net_profit", "净利润"],
    ["operating_cashflow", "经营现金流"]
  ];
  if (!rows.length) {
    nodes.trendCharts.innerHTML = trendDefs.map(([key, label]) => {
      const metric = metrics[key] || {};
      return `
        <div class="trend-tile">
          <span>${label}</span>
          <strong>${escapeHtml(metric.display || "--")}</strong>
          ${renderSparkline(metric.trend || [])}
        </div>
      `;
    }).join("");
    return;
  }
  nodes.trendCharts.innerHTML = trendDefs.map(([key, label]) => {
    const values = rows.map((row) => parseMetricNumber(row[key]));
    return `
      <div class="trend-tile">
        <span>${label}</span>
        <strong>${escapeHtml(rows[0]?.[key] || "--")}</strong>
        ${renderSparkline(values)}
      </div>
    `;
  }).join("");
}

function renderIndustryTable(rows) {
  if (!rows.length) {
    nodes.industryCompare.innerHTML = "暂无同行样本。";
    return;
  }
  nodes.industryCompare.innerHTML = `
    <table>
      <thead><tr><th>公司</th><th>报告期</th><th>收入</th><th>收入同比</th><th>净利润</th><th>毛利率</th><th>ROE</th><th>负债率</th></tr></thead>
      <tbody>
        ${rows.map((row) => `
          <tr>
            <td>${escapeHtml(row.name)}</td><td>${escapeHtml(row.period)}</td><td>${escapeHtml(row.revenue)}</td><td>${escapeHtml(valueOrPct(row.revenue_yoy))}</td>
            <td>${escapeHtml(row.net_profit)}</td><td>${escapeHtml(row.gross_margin ?? "待补充")}%</td><td>${escapeHtml(row.roe ?? "待补充")}%</td><td>${escapeHtml(row.debt_ratio ?? "待补充")}%</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderReports(reports) {
  nodes.reportList.innerHTML = (reports || [])
    .slice(0, 24)
    .map(
      (report) => `
        <div class="source-item">
          <strong>${escapeHtml(report.period)} · ${escapeHtml(report.report_type)}</strong>
          <small>${escapeHtml(report.parse_status || "pending")} ${escapeHtml(report.publish_date || "")}</small>
          <p>${report.source_url ? `<a href="${escapeHtml(report.source_url)}" target="_blank" rel="noreferrer">查看来源</a>` : "来源链接待补充或来自结构化接口。"}</p>
        </div>
      `
    )
    .join("") || '<div class="source-item"><strong>暂无报告列表</strong><p>可先通过联网分析生成资料来源。</p></div>';
}

function renderMetricDictionary() {
  // 指标解释改为点击指标卡片时弹出，不再渲染独立区块。
}

function showMetricPopover(metricKey, anchorEl) {
  if (!metricKey || !nodes.metricPopover) return;
  state.activeMetricKey = metricKey;
  state.metricFormulaVisible = false;
  document.querySelectorAll(".metric-card.active-metric").forEach((card) => {
    card.classList.remove("active-metric");
  });
  anchorEl?.classList.add("active-metric");
  renderMetricPopover(metricKey, anchorEl);
}

function renderMetricPopover(metricKey, anchorEl) {
  const explanation = getMetricExplanation(metricKey);
  const metric = getCurrentMetric(metricKey);
  const formula = getMetricFormula(metricKey);
  nodes.metricPopoverTitle.textContent = `${explanation.name}是什么？`;
  nodes.metricPopoverPlain.textContent = explanation.how_to_read
    ? `${explanation.plain} ${explanation.how_to_read}`
    : explanation.plain;
  nodes.metricPopoverCurrent.innerHTML = `
    <div>
      <span>当前值</span>
      <strong>${escapeHtml(metric.display || "待补充")}</strong>
    </div>
    <div>
      <span>同比变化</span>
      <strong>${metric.yoy === null || metric.yoy === undefined ? "待补充" : `同比${escapeHtml(pctText(metric.yoy))}`}</strong>
    </div>
  `;
  nodes.metricFormulaBlock.textContent = formula;
  nodes.metricFormulaBlock.classList.toggle("hidden", !state.metricFormulaVisible);
  nodes.metricFormulaButton.textContent = state.metricFormulaVisible ? "收起计算口径" : "查看计算口径";
  nodes.metricPopover.classList.remove("hidden");
  positionMetricPopover(anchorEl);
}

function positionMetricPopover(anchorEl) {
  if (!nodes.metricPopover || !anchorEl) return;
  if (window.matchMedia("(max-width: 640px)").matches) {
    nodes.metricPopover.style.left = "";
    nodes.metricPopover.style.top = "";
    return;
  }
  const rect = anchorEl.getBoundingClientRect();
  const popoverWidth = Math.min(360, window.innerWidth - 32);
  let left = rect.left + window.scrollX;
  let top = rect.bottom + window.scrollY + 12;
  if (left + popoverWidth > window.scrollX + window.innerWidth - 16) {
    left = window.scrollX + window.innerWidth - popoverWidth - 16;
  }
  if (left < window.scrollX + 16) left = window.scrollX + 16;
  nodes.metricPopover.style.left = `${left}px`;
  nodes.metricPopover.style.top = `${top}px`;
}

function hideMetricPopover() {
  state.activeMetricKey = null;
  state.metricFormulaVisible = false;
  nodes.metricPopover?.classList.add("hidden");
  document.querySelectorAll(".metric-card.active-metric").forEach((card) => {
    card.classList.remove("active-metric");
  });
}

function handleOutsideMetricPopover(event) {
  if (!nodes.metricPopover || nodes.metricPopover.classList.contains("hidden")) return;
  const target = event.target;
  if (nodes.metricPopover.contains(target) || target.closest?.(".metric-card[data-metric]")) return;
  hideMetricPopover();
}

function handleMetricPopoverKeydown(event) {
  if (event.key === "Escape") hideMetricPopover();
}

function toggleMetricFormula(event) {
  event?.stopPropagation();
  if (!state.activeMetricKey) return;
  state.metricFormulaVisible = !state.metricFormulaVisible;
  const activeCard = document.querySelector(`.metric-card[data-metric="${state.activeMetricKey}"]`);
  renderMetricPopover(state.activeMetricKey, activeCard);
}

function askActiveMetric(event) {
  event?.stopPropagation();
  if (!state.activeMetricKey) return;
  const explanation = getMetricExplanation(state.activeMetricKey);
  const question = `请解释一下${explanation.name}，并结合当前公司本期表现说明它意味着什么？`;
  askQuestion(question);
  document.querySelector(".qa-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function getMetricExplanation(metricKey) {
  const dictionaryItem = state.metricDictionary?.[metricKey] || {};
  const fallback = METRIC_FALLBACKS[metricKey] || {};
  return {
    name: dictionaryItem.name || labelForMetric(metricKey),
    plain: dictionaryItem.plain || fallback.plain || "这个指标用于辅助理解公司的经营和财务状况。",
    how_to_read: dictionaryItem.how_to_read || fallback.how_to_read || ""
  };
}

function getCurrentMetric(metricKey) {
  return state.analysis?.metrics?.[metricKey] || {
    label: labelForMetric(metricKey),
    display: "待补充",
    yoy: null
  };
}

function getMetricFormula(metricKey) {
  const dictionaryItem = state.metricDictionary?.[metricKey] || {};
  return dictionaryItem.formula
    || METRIC_FORMULAS[metricKey]
    || "该指标计算口径暂未标准化，当前展示来自披露数据或模型结构化结果。";
}

function renderRecentAnalyses() {
  if (!nodes.recentAnalyses) return;
  nodes.recentAnalyses.innerHTML = TOP_COMPANIES.slice(0, 5).map((company) => `
    <button type="button" class="recent-item" data-ticker="${escapeHtml(company.ticker)}" data-market="${escapeHtml(company.market)}">
      <strong>${escapeHtml(company.name)}</strong>
      <small>${escapeHtml(company.ticker)} · ${escapeHtml(company.industry || company.market)}</small>
    </button>
  `).join("");
  nodes.recentAnalyses.querySelectorAll("[data-ticker]").forEach((item) => {
    item.addEventListener("click", () => navigateToCompany(item.dataset.ticker, item.dataset.market));
  });
}

function renderSuggestedQuestions() {
  nodes.suggestedQuestions.innerHTML = SUGGESTED_QUESTIONS.map((question) => `
    <button type="button" class="question-chip" data-question="${escapeHtml(question)}">${escapeHtml(question)}</button>
  `).join("");
  nodes.suggestedQuestions.querySelectorAll("[data-question]").forEach((button) => {
    button.addEventListener("click", () => askQuestion(button.dataset.question));
  });
}

async function explainMetricInChat(metricKey) {
  const meta = state.metricDictionary[metricKey] || { name: labelForMetric(metricKey), plain: "暂无解释。", how_to_read: "" };
  appendMessage(`解释一下${meta.name}`, "user");
  appendMessage(`先说结论：${meta.name}是${meta.plain}${meta.how_to_read ? ` 怎么看：${meta.how_to_read}` : ""}<small>依据：指标解释库。本内容仅用于财报理解，不构成投资建议。</small>`, "agent");
}

async function askQuestion(questionOverride) {
  const question = (questionOverride || nodes.questionInput.value).trim();
  if (!question) return;
  appendMessage(question, "user");
  nodes.questionInput.value = "";
  if (!state.backendReady) {
    appendMessage(`${state.analysis?.summary || "请先完成一次财报分析。"}<small>本内容仅用于财报理解，不构成投资建议。</small>`, "agent");
    return;
  }
  try {
    const data = await api("/api/qa", {
      method: "POST",
      body: JSON.stringify({ question, analysis: state.analysis, company_id: state.company?.id })
    });
    const citations = (data.citations || []).map((item) => item.title).join("、");
    appendMessage(`${escapeHtml(data.answer)}<small>依据：${escapeHtml(citations || "当前分析结果")}。${escapeHtml(data.disclaimer || "")}</small>`, "agent");
  } catch (error) {
    appendMessage(`问答服务暂时不可用：${escapeHtml(error.message)}`, "agent");
  }
}

function resetChat() {
  nodes.chatLog.innerHTML = "";
  appendMessage("我已经准备好。你可以问：现金流怎么样、风险在哪里、行业里强不强、毛利率是什么意思。", "agent");
}

function appendMessage(content, role) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.innerHTML = content;
  nodes.chatLog.appendChild(item);
  nodes.chatLog.scrollTop = nodes.chatLog.scrollHeight;
}

function fallbackAnalysis() {
  return {
    company: fallbackCompany,
    period_type: "annual",
    latest_period: "2024-FY",
    selected_periods: ["2022-FY", "2023-FY", "2024-FY"],
    score: 82,
    stance: "positive",
    summary: "Apple Inc. 收入和利润保持较大规模，经营现金流为正，但仍需要关注增长节奏和产品周期变化。",
    business_model: "公司主要通过硬件产品、服务订阅和生态系统变现。",
    highlights: ["经营现金流为正，利润质量较好。"],
    watch_metrics: ["营业收入", "净利润", "经营现金流", "毛利率"],
    metrics: {
      revenue: { label: "营业收入", display: "383.29B USD", yoy: -2.8 },
      net_profit: { label: "净利润", display: "97.00B USD", yoy: -2.8 },
      gross_margin: { label: "毛利率", display: "44.1%" },
      operating_cashflow: { label: "经营现金流", display: "110.54B USD" },
      receivables: { label: "应收账款", display: "待补充", yoy: null },
      inventory: { label: "存货", display: "待补充", yoy: null },
      net_margin: { label: "净利率", display: "25.3%" },
      debt_ratio: { label: "资产负债率", display: "82.4%" }
    },
    risks: [{ name: "收入增长", level: "yellow", reason: "收入同比下降，增长动能需要观察。" }],
    comparison: { rows: [] },
    sources: [],
    rag_chunks: [],
    disclaimer: "本内容仅用于财报信息理解和研究辅助，不构成任何投资建议。"
  };
}

function handleWatchIntent() {
  if (state.intent !== "watch" || !nodes.watchButton) return;
  nodes.watchButton.classList.add("attention");
  nodes.watchButton.textContent = "点击加入自选";
  nodes.watchButton.scrollIntoView({ behavior: "smooth", block: "center" });
}

function navigateToCompany(ticker, market) {
  if (!ticker) return;
  const url = new URL(window.location.href);
  url.searchParams.set("ticker", ticker.toUpperCase());
  url.searchParams.set("market", market || inferMarket(ticker));
  url.searchParams.delete("intent");
  window.location.href = url.toString();
}

function valueOrPct(value) {
  return value === null || value === undefined ? "待补充" : pctText(value);
}

function pctText(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  return `${number >= 0 ? "增长" : "下降"}${Math.abs(number)}%`;
}

function parseMetricNumber(value) {
  const text = String(value ?? "").replace(/,/g, "");
  const match = text.match(/-?\d+(\.\d+)?/);
  return match ? Number(match[0]) : null;
}

function labelForMetric(key) {
  return {
    revenue: "营业收入",
    net_profit: "净利润",
    gross_margin: "毛利率",
    operating_cashflow: "经营现金流",
    receivables: "应收账款",
    inventory: "存货",
    net_margin: "净利率",
    debt_ratio: "资产负债率"
  }[key] || key;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

function getLaunchCompany() {
  const params = new URLSearchParams(window.location.search);
  const rawTicker = (params.get("ticker") || "").trim();
  const ticker = rawTicker ? rawTicker.toUpperCase() : "";
  const inferred = ticker ? inferMarket(ticker) : "US";
  const market = (params.get("market") || inferred).trim().toUpperCase();
  return {
    ticker,
    market: market === "A" ? "CN" : market,
    intent: (params.get("intent") || "").trim()
  };
}

function inferMarket(ticker) {
  if (window.FinancialMiningUI?.inferMarket) return window.FinancialMiningUI.inferMarket(ticker);
  return /^\d{6}$/.test(ticker) ? "CN" : "US";
}

function renderSelectedCompany(company) {
  if (!company) return;
  nodes.sidebarCompanyName.textContent = company.name || company.ticker || "等待载入";
  nodes.sidebarCompanyMeta.textContent = `${company.ticker || state.launchTicker || "--"} · ${company.market || state.launchMarket || "--"} · ${company.industry || "待识别行业"}`;
  nodes.companyMarket.textContent = company.market || state.launchMarket || "待识别";
  hydrateSearchInput(company.ticker || state.launchTicker);
}

boot();
