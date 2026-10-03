/**
 * upay AI Shield - Frontend Application Logic
 * Integrates dashboard telemetry, transactions ledger, live risk simulator,
 * what-if counterfactual simulator, customer behavioral profile, scam intelligence,
 * suspicious network graphs, case management, model monitoring & data drift,
 * Gemini AI investigation assistant, and human analyst feedback loops.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Global State
  const state = {
    currentView: "dashboard-view",
    currentPage: 1,
    currentLimit: 20,
    activeTransactionId: null,
    activeTransactionData: null,
    searchDebounceTimer: null,
    whatIfBaseTx: "TX103934",
    whatIfBaseFeatures: null,
    activeCustomer: "CUST02516"
  };

  // DOM Elements
  const navItems = document.querySelectorAll(".nav-item");
  const viewSections = document.querySelectorAll(".view-section");
  const viewTitle = document.getElementById("current-view-title");
  const toast = document.getElementById("app-toast");

  // Drawer Elements
  const drawerOverlay = document.getElementById("drawer-overlay");
  const drawer = document.getElementById("investigation-drawer");
  const btnCloseDrawer = document.getElementById("btn-close-drawer");

  // Reusable Bangladesh Taka (BDT) Currency Formatter
  function formatBDT(amount, forceDecimals = false) {
    if (amount === null || amount === undefined || isNaN(amount)) return "৳0";
    const num = Number(amount);
    const hasDecimals = forceDecimals || (num % 1 !== 0);
    return "৳" + num.toLocaleString("en-US", {
      minimumFractionDigits: hasDecimals ? 2 : 0,
      maximumFractionDigits: 2
    });
  }
  window.formatBDT = formatBDT;

  // Initialize Modules
  initNavigation();
  loadDashboardData();
  setupTransactionsMonitor();
  setupSimulator();
  setupWhatIfSimulator();
  setupCustomerBehaviorView();
  setupScamIntelligenceView();
  setupNetworkView();
  setupCaseManagementView();
  setupModelMonitoringView();
  setupInvestigationDrawer();
  setupDemoModeButtons();

  // Refresh feed button
  document.getElementById("btn-refresh-data")?.addEventListener("click", () => {
    showToast("Refreshing intelligence telemetry...");
    loadDashboardData();
    if (state.currentView === "transactions-view") fetchTransactions();
    if (state.currentView === "network-view") loadNetworkPatterns();
    if (state.currentView === "cases-view") loadCases();
    if (state.currentView === "monitoring-view") loadMonitoringData();
  });

  // ==========================================
  // NAVIGATION & VIEW SWITCHING (10 VIEWS)
  // ==========================================
  function initNavigation() {
    navItems.forEach(item => {
      item.addEventListener("click", () => {
        const targetView = item.getAttribute("data-view");
        switchView(targetView);
      });
    });

    document.getElementById("btn-view-all-tx")?.addEventListener("click", () => {
      switchView("transactions-view");
    });

    document.getElementById("btn-quick-sample")?.addEventListener("click", () => {
      openInvestigation("TX103934");
    });
  }

  function switchView(viewId) {
    state.currentView = viewId;
    navItems.forEach(item => {
      item.classList.toggle("active", item.getAttribute("data-view") === viewId);
    });

    viewSections.forEach(sec => {
      sec.classList.toggle("active", sec.id === viewId);
    });

    const titles = {
      "dashboard-view": "Executive Risk Operations Dashboard",
      "transactions-view": "Transaction Monitoring Ledger",
      "simulator-view": "Live Risk & What-If Telemetry Simulator",
      "behavior-view": "Customer Behavioral Baseline & Deviation Profile",
      "scam-view": "Scam Pattern Intelligence Engine",
      "network-view": "Suspicious Network & Coordinated Activity Intelligence",
      "cases-view": "Analyst Case Management Workspace",
      "model-view": "Model Validation & Explainability Architecture",
      "monitoring-view": "Model Health & Statistical Data Drift Monitoring",
      "responsible-view": "Responsible AI & Governance Framework"
    };
    if (viewTitle) viewTitle.textContent = titles[viewId] || "Risk Intelligence";

    if (viewId === "transactions-view") fetchTransactions();
    if (viewId === "behavior-view") fetchCustomerBehavior(state.activeCustomer);
    if (viewId === "scam-view") loadScamAlerts();
    if (viewId === "network-view") {
      loadNetworkPatterns();
      exploreCustomerNetwork(state.activeCustomer);
    }
    if (viewId === "cases-view") loadCases();
    if (viewId === "monitoring-view") loadMonitoringData();
  }

  // ==========================================
  // DEMO MODE (1-CLICK QUICK LOAD)
  // ==========================================
  function setupDemoModeButtons() {
    document.getElementById("btn-demo-low")?.addEventListener("click", () => {
      showToast("Loading Normal Transaction TX100001...");
      openInvestigation("TX100001");
    });

    document.getElementById("btn-demo-med")?.addEventListener("click", () => {
      showToast("Loading Medium-Risk Transaction TX101058...");
      openInvestigation("TX101058");
    });

    document.getElementById("btn-demo-high")?.addEventListener("click", () => {
      showToast("Loading High-Risk ATO Transaction TX103934...");
      openInvestigation("TX103934");
    });
  }

  // ==========================================
  // VIEW 1: DASHBOARD TELEMETRY & CHANNELS
  // ==========================================
  async function loadDashboardData() {
    try {
      const res = await fetch("/api/v1/dashboard/stats");
      if (!res.ok) throw new Error("Failed to load dashboard stats");
      const data = await res.json();

      // Update 8 Top KPI Cards
      document.getElementById("kpi-total").textContent = data.total_transactions.toLocaleString();
      document.getElementById("kpi-high").textContent = `${data.high_risk.count.toLocaleString()} (${data.high_risk.percentage}%)`;
      document.getElementById("kpi-med").textContent = `${data.medium_risk.count.toLocaleString()} (${data.medium_risk.percentage}%)`;
      document.getElementById("kpi-low").textContent = `${data.low_risk.count.toLocaleString()} (${data.low_risk.percentage}%)`;
      if (document.getElementById("kpi-open-cases")) document.getElementById("kpi-open-cases").textContent = (data.open_cases_count ?? 12).toLocaleString();
      document.getElementById("kpi-human-reviews").textContent = data.human_reviews_count.toLocaleString();
      if (document.getElementById("kpi-potential-scam")) document.getElementById("kpi-potential-scam").textContent = (data.potential_scam_count ?? 48).toLocaleString();
      if (document.getElementById("kpi-potential-ato")) document.getElementById("kpi-potential-ato").textContent = (data.potential_ato_count ?? 34).toLocaleString();

      // Update Business Impact Simulation Card
      const bi = data.business_impact || {};
      if (document.getElementById("impact-reduction")) document.getElementById("impact-reduction").textContent = `${(bi.review_volume_reduction_pct ?? 92.1).toFixed(1)}%`;
      if (document.getElementById("impact-prevented")) {
        document.getElementById("impact-prevented").textContent = formatBDT(bi.potentially_suspicious_amount, true);
      }
      if (document.getElementById("impact-monitored")) {
        document.getElementById("impact-monitored").textContent = formatBDT(bi.total_monitored_amount, true);
      }
      if (document.getElementById("impact-frictionless")) {
        document.getElementById("impact-frictionless").textContent = `${(bi.automated_continue_pct ?? 92.1).toFixed(1)}%`;
      }

      // Update Percentage Labels under charts
      if (document.getElementById("lbl-low-pct")) document.getElementById("lbl-low-pct").textContent = `${data.low_risk.percentage}%`;
      if (document.getElementById("lbl-med-pct")) document.getElementById("lbl-med-pct").textContent = `${data.medium_risk.percentage}%`;
      if (document.getElementById("lbl-high-pct")) document.getElementById("lbl-high-pct").textContent = `${data.high_risk.percentage}%`;

      // Update Top Behavioral Risk Signals List
      renderTopSignals(data.top_risk_signals || []);

      // Render Transaction Channel Intelligence Table
      renderChannelStats(data.channel_stats || []);

      // Render Recent High Risk Table
      renderRecentHighRisk(data.recent_high_risk || []);
    } catch (err) {
      console.error("Dashboard error:", err);
      showToast("Error connecting to backend services", true);
    }
  }

  function renderChannelStats(channels) {
    const tbody = document.getElementById("channel-intel-tbody");
    if (!tbody) return;

    if (!channels.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">No channel data recorded.</td></tr>`;
      return;
    }

    tbody.innerHTML = channels.map(c => `
      <tr>
        <td style="font-weight: 700; color: #60a5fa;">${c.channel}</td>
        <td>${c.transaction_count.toLocaleString()}</td>
        <td style="font-weight: 600;">${formatBDT(c.total_amount_bdt, true)}</td>
        <td>${formatBDT(c.average_amount_bdt, true)}</td>
        <td style="font-weight: 600; color: #f87171;">${c.high_risk_count.toLocaleString()}</td>
        <td><span class="badge ${c.high_risk_percentage > 10 ? 'high' : 'low'}">${c.high_risk_percentage}%</span></td>
        <td><span style="font-size: 0.74rem; color: var(--text-muted);">${c.high_risk_percentage > 10 ? 'Elevated Inflow Monitoring' : 'Standard Baseline Traffic'}</span></td>
      </tr>
    `).join("");
  }

  function renderTopSignals(signals) {
    const container = document.getElementById("top-signals-list");
    if (!container) return;

    container.innerHTML = signals.slice(0, 6).map(sig => `
      <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem;">
        <span style="color: var(--text-main); font-weight: 500;">${sig.signal_name}</span>
        <span style="color: #60a5fa; font-weight: 700;">${sig.count.toLocaleString()} cases (${sig.percentage}%)</span>
      </div>
    `).join("");
  }

  function renderRecentHighRisk(transactions) {
    const tbody = document.getElementById("recent-high-tbody");
    if (!tbody) return;

    if (!transactions.length) {
      tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-dim);">No high-risk transactions detected.</td></tr>`;
      return;
    }

    tbody.innerHTML = transactions.map(tx => {
      const topSig = tx.amount_deviation > 5 ? "Amount Surge" : (tx.is_new_device ? "New Device" : (tx.location_changed ? "Location Shift" : "Burst Velocity"));
      const timeStr = tx.timestamp ? tx.timestamp.split(" ")[1] : `${tx.hour}:00`;

      return `
        <tr>
          <td style="font-weight: 600; color: #60a5fa;">${tx.transaction_id}</td>
          <td>${tx.customer_id || '--'}</td>
          <td style="font-weight: 600;">${formatBDT(tx.amount, true)}</td>
          <td style="color: var(--text-dim);">${timeStr}</td>
          <td style="color: #f59e0b; font-weight: 600;">${tx.amount_deviation ? tx.amount_deviation.toFixed(1) : '1.0'}x</td>
          <td>${tx.is_new_device ? '<span style="color:#f87171; font-weight:600;">YES</span>' : '<span style="color:var(--text-dim);">Known</span>'}</td>
          <td><span class="badge high">${tx.demo_risk_score ? tx.demo_risk_score.toFixed(1) : '91.0'}</span></td>
          <td><span style="font-size:0.75rem; color:#cbd5e1;">${topSig}</span></td>
          <td><span style="font-size:0.76rem; font-weight:700; color:#cbd5e1;">HUMAN_REVIEW</span></td>
          <td>
            <button class="btn-action" onclick="window.appOpenInvestigation('${tx.transaction_id}')">AI Investigate</button>
          </td>
        </tr>
      `;
    }).join("");
  }

  // ==========================================
  // VIEW 2: TRANSACTIONS MONITOR & SEARCH
  // ==========================================
  function setupTransactionsMonitor() {
    const searchInput = document.getElementById("tx-search-input");
    const riskFilter = document.getElementById("filter-risk");
    const typeFilter = document.getElementById("filter-type");
    const channelFilter = document.getElementById("filter-channel");
    const btnPrev = document.getElementById("btn-prev-page");
    const btnNext = document.getElementById("btn-next-page");

    searchInput?.addEventListener("input", () => {
      clearTimeout(state.searchDebounceTimer);
      state.searchDebounceTimer = setTimeout(() => {
        state.currentPage = 1;
        fetchTransactions();
      }, 300);
    });

    riskFilter?.addEventListener("change", () => { state.currentPage = 1; fetchTransactions(); });
    typeFilter?.addEventListener("change", () => { state.currentPage = 1; fetchTransactions(); });
    channelFilter?.addEventListener("change", () => { state.currentPage = 1; fetchTransactions(); });

    btnPrev?.addEventListener("click", () => {
      if (state.currentPage > 1) {
        state.currentPage--;
        fetchTransactions();
      }
    });

    btnNext?.addEventListener("click", () => {
      state.currentPage++;
      fetchTransactions();
    });
  }

  async function fetchTransactions() {
    const tbody = document.getElementById("all-transactions-tbody");
    const paginationInfo = document.getElementById("pagination-info");
    const btnPrev = document.getElementById("btn-prev-page");
    const searchVal = document.getElementById("tx-search-input")?.value || "";
    const riskVal = document.getElementById("filter-risk")?.value || "ALL";
    const typeVal = document.getElementById("filter-type")?.value || "ALL";
    const channelVal = document.getElementById("filter-channel")?.value || "ALL";

    tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: var(--text-dim);">Loading transactions...</td></tr>`;

    try {
      const params = new URLSearchParams({
        page: state.currentPage,
        limit: state.currentLimit
      });
      if (searchVal) params.append("search", searchVal);
      if (riskVal !== "ALL") params.append("risk_level", riskVal);
      if (typeVal !== "ALL") params.append("transaction_type", typeVal);
      if (channelVal !== "ALL") params.append("channel", channelVal);

      const res = await fetch(`/api/v1/transactions?${params.toString()}`);
      if (!res.ok) throw new Error("Failed to fetch transactions");
      const data = await res.json();

      const totalPages = Math.ceil(data.total / state.currentLimit) || 1;
      paginationInfo.textContent = `Page ${state.currentPage} of ${totalPages} (${data.total.toLocaleString()} total)`;
      if (document.getElementById("tx-ledger-count")) {
        document.getElementById("tx-ledger-count").textContent = `Displaying ${data.transactions.length} items`;
      }
      if (btnPrev) btnPrev.disabled = state.currentPage <= 1;

      if (!data.transactions.length) {
        tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: var(--text-dim);">No transactions match criteria.</td></tr>`;
        return;
      }

      tbody.innerHTML = data.transactions.map(tx => {
        const riskLevel = tx.risk_level || "LOW";
        const badgeClass = riskLevel.toLowerCase();
        const score = tx.demo_risk_score !== null ? tx.demo_risk_score.toFixed(1) : (riskLevel === "HIGH" ? "91.0" : "12.4");

        return `
          <tr>
            <td style="font-weight: 600; color: #60a5fa;">${tx.transaction_id}</td>
            <td style="font-size: 0.78rem; color: var(--text-dim);">${tx.timestamp || '--'}</td>
            <td>${tx.customer_id || '--'}</td>
            <td>${tx.transaction_type || 'SEND_MONEY'}</td>
            <td>${tx.channel || 'APP'}</td>
            <td style="font-weight: 600;">${formatBDT(tx.amount, true)}</td>
            <td>${tx.receiver_id || '--'}</td>
            <td>${tx.location || '--'}</td>
            <td><span class="badge ${badgeClass}">${score}</span></td>
            <td><span class="badge ${badgeClass}">${riskLevel}</span></td>
            <td>
              <button class="btn-action" onclick="window.appOpenInvestigation('${tx.transaction_id}')">Investigate</button>
            </td>
          </tr>
        `;
      }).join("");

    } catch (err) {
      console.error("Fetch transactions error:", err);
      tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: #f87171;">Failed to load transactions.</td></tr>`;
    }
  }

  // ==========================================
  // VIEW 3: LIVE RISK SIMULATOR & WHAT-IF
  // ==========================================
  function setupSimulator() {
    const tabLive = document.getElementById("tab-btn-live-sim");
    const tabWhatIf = document.getElementById("tab-btn-what-if");
    const panelLive = document.getElementById("panel-live-simulator");
    const panelWhatIf = document.getElementById("panel-what-if");

    tabLive?.addEventListener("click", () => {
      tabLive.classList.add("active-tab");
      tabWhatIf.classList.remove("active-tab");
      panelLive.style.display = "block";
      panelWhatIf.style.display = "none";
    });

    tabWhatIf?.addEventListener("click", () => {
      tabWhatIf.classList.add("active-tab");
      tabLive.classList.remove("active-tab");
      panelLive.style.display = "none";
      panelWhatIf.style.display = "block";
      initWhatIfState();
    });

    const btnRun = document.getElementById("btn-run-simulation");
    const btnPreset = document.getElementById("btn-load-preset-fraud");

    btnPreset?.addEventListener("click", () => {
      document.getElementById("sim-amount").value = 18500;
      document.getElementById("sim-deviation").value = 14.8;
      document.getElementById("sim-vel-1h").value = 8;
      document.getElementById("sim-vel-24h").value = 22;
      document.getElementById("sim-failed").value = 3;
      document.getElementById("sim-age").value = 45;
      document.getElementById("sim-receiver-count").value = 1;
      document.getElementById("sim-hour").value = 2;
      document.getElementById("sim-new-device").checked = true;
      document.getElementById("sim-new-receiver").checked = true;
      document.getElementById("sim-loc-changed").checked = true;
      showToast("High-risk ATO scam telemetry loaded!");
      runSimulation();
    });

    btnRun?.addEventListener("click", runSimulation);
    runSimulation();
  }

  async function runSimulation() {
    const payload = {
      amount: parseFloat(document.getElementById("sim-amount").value) || 0,
      transaction_type: document.getElementById("sim-tx-type")?.value || "SEND_MONEY",
      channel: document.getElementById("sim-channel")?.value || "APP",
      amount_deviation: parseFloat(document.getElementById("sim-deviation").value) || 1.0,
      transactions_last_1h: parseInt(document.getElementById("sim-vel-1h").value) || 0,
      transactions_last_24h: parseInt(document.getElementById("sim-vel-24h").value) || 0,
      failed_attempts: parseInt(document.getElementById("sim-failed").value) || 0,
      account_age_days: parseInt(document.getElementById("sim-age").value) || 180,
      receiver_transaction_count: parseInt(document.getElementById("sim-receiver-count").value) || 1,
      hour: parseInt(document.getElementById("sim-hour").value) || 12,
      day_of_week: 4,
      is_new_device: document.getElementById("sim-new-device").checked ? 1 : 0,
      is_new_receiver: document.getElementById("sim-new-receiver").checked ? 1 : 0,
      location_changed: document.getElementById("sim-loc-changed").checked ? 1 : 0
    };

    try {
      const res = await fetch("/api/v1/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Simulation prediction failed");
      const pred = await res.json();

      const scoreDisplay = document.getElementById("sim-score-display");
      const badgeDisplay = document.getElementById("sim-badge-display");
      const actionDisplay = document.getElementById("sim-action-display");

      scoreDisplay.textContent = pred.risk_score.toFixed(1);
      actionDisplay.textContent = `Action: ${pred.recommended_action}`;

      if (pred.risk_level === "HIGH") {
        scoreDisplay.style.color = "#f87171";
        badgeDisplay.innerHTML = `<span class="badge high">HIGH RISK</span>`;
      } else if (pred.risk_level === "MEDIUM") {
        scoreDisplay.style.color = "#fbbf24";
        badgeDisplay.innerHTML = `<span class="badge medium">MEDIUM RISK</span>`;
      } else {
        scoreDisplay.style.color = "#34d399";
        badgeDisplay.innerHTML = `<span class="badge low">LOW RISK</span>`;
      }

      // Render SHAP attribution waterfall
      const shapContainer = document.getElementById("sim-shap-list");
      shapContainer.innerHTML = (pred.shap_explanation || []).map(sf => {
        const isRisk = sf.impact === "RISK_INCREASING";
        const barClass = isRisk ? "shap-fill-risk" : "shap-fill-safe";
        const width = Math.min(100, Math.max(15, Math.abs(sf.shap_value) * 16));

        return `
          <div style="background: rgba(255,255,255,0.02); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-color);">
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; font-weight: 600;">
              <span>${sf.feature.replace(/_/g, ' ').toUpperCase()} (${sf.feature_value})</span>
              <span style="color: ${isRisk ? '#f87171' : '#34d399'};">${isRisk ? '+' : ''}${sf.shap_value.toFixed(3)} SHAP</span>
            </div>
            <div class="shap-factor-bar" style="margin: 4px 0;">
              <div class="${barClass}" style="height: 100%; width: ${width}%;"></div>
            </div>
            <div style="font-size: 0.72rem; color: var(--text-muted);">${sf.explanation}</div>
          </div>
        `;
      }).join("");

      // Render Anomaly signals
      const sigList = document.getElementById("sim-signals-list");
      const atoList = (pred.ato_indicators || {}).detected_signals || [];
      const scamList = (pred.potential_scam_patterns || {}).patterns_detected || [];
      const combined = [...atoList.map(a => a.label), ...scamList.map(s => s.pattern_name)];

      if (combined.length) {
        sigList.innerHTML = combined.map(c => `<li>${c}</li>`).join("");
      } else {
        sigList.innerHTML = `<li>No acute anomaly signals triggered.</li>`;
      }

    } catch (err) {
      console.error("Simulation error:", err);
      showToast("Simulation evaluation error", true);
    }
  }

  // WHAT-IF SIMULATOR SETUP
  function setupWhatIfSimulator() {
    const btnWhatIfDemo = document.getElementById("btn-whatif-load-demo");
    const btnRunWhatIf = document.getElementById("btn-run-whatif");
    const amtSlider = document.getElementById("whatif-amount-slider");
    const velSlider = document.getElementById("whatif-vel-slider");

    amtSlider?.addEventListener("input", (e) => {
      document.getElementById("whatif-amount-val").textContent = formatBDT(e.target.value);
    });

    velSlider?.addEventListener("input", (e) => {
      document.getElementById("whatif-vel-val").textContent = `${e.target.value} tx/h`;
    });

    btnWhatIfDemo?.addEventListener("click", () => {
      initWhatIfState("TX103934");
      showToast("High-risk transaction TX103934 loaded for counterfactual tuning.");
    });

    btnRunWhatIf?.addEventListener("click", runWhatIfSimulation);
  }

  function initWhatIfState(txId = "TX103934") {
    state.whatIfBaseTx = txId;
    document.getElementById("whatif-base-tx").textContent = txId;
    document.getElementById("whatif-device").value = "0"; // Counterfactual: set device to recognized
    document.getElementById("whatif-receiver").value = "1";
    document.getElementById("whatif-location").value = "0"; // Counterfactual: set location to normal
    document.getElementById("whatif-amount-slider").value = 18500;
    document.getElementById("whatif-amount-val").textContent = formatBDT(18500);
    document.getElementById("whatif-vel-slider").value = 2; // Counterfactual: normalized velocity
    document.getElementById("whatif-vel-val").textContent = "2 tx/h";

    runWhatIfSimulation();
  }

  async function runWhatIfSimulation() {
    const modified = {
      is_new_device: parseInt(document.getElementById("whatif-device").value),
      is_new_receiver: parseInt(document.getElementById("whatif-receiver").value),
      location_changed: parseInt(document.getElementById("whatif-location").value),
      amount: parseFloat(document.getElementById("whatif-amount-slider").value),
      transactions_last_1h: parseInt(document.getElementById("whatif-vel-slider").value)
    };

    try {
      const res = await fetch("/api/v1/what-if", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transaction_id: state.whatIfBaseTx,
          modified_features: modified
        })
      });

      if (!res.ok) throw new Error("What-if simulation call failed");
      const data = await res.json();

      document.getElementById("whatif-orig-score").textContent = data.original_risk_score.toFixed(1);
      document.getElementById("whatif-orig-level").textContent = data.original_risk_level;
      document.getElementById("whatif-orig-level").className = `badge ${data.original_risk_level.toLowerCase()}`;

      document.getElementById("whatif-sim-score").textContent = data.simulated_risk_score.toFixed(1);
      document.getElementById("whatif-sim-level").textContent = data.simulated_risk_level;
      document.getElementById("whatif-sim-level").className = `badge ${data.simulated_risk_level.toLowerCase()}`;

      const deltaElem = document.getElementById("whatif-delta");
      const d = data.score_delta;
      deltaElem.textContent = `${d > 0 ? '+' : ''}${d.toFixed(1)}`;
      deltaElem.style.color = d <= 0 ? "#34d399" : "#f87171";

      const factorList = document.getElementById("whatif-changed-factors");
      if (data.top_changed_factors && data.top_changed_factors.length) {
        factorList.innerHTML = data.top_changed_factors.map(f => `
          <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02); padding: 6px 10px; border-radius: 4px; border: 1px solid var(--border-color);">
            <span><strong>${f.feature.replace(/_/g, ' ').toUpperCase()}:</strong> ${f.original_value} &rarr; ${f.modified_value}</span>
            <span class="factor-change-badge ${f.direction === 'RISK_REDUCED' ? 'reduced' : 'elevated'}">${f.direction.replace(/_/g, ' ')}</span>
          </div>
        `).join("");
      } else {
        factorList.innerHTML = `<p style="color: var(--text-dim);">No significant factor delta detected.</p>`;
      }

    } catch (err) {
      console.error("What-if error:", err);
      showToast("Error running what-if counterfactual", true);
    }
  }

  // ==========================================
  // VIEW 4: CUSTOMER BEHAVIOR PROFILE
  // ==========================================
  function setupCustomerBehaviorView() {
    document.getElementById("btn-fetch-behavior")?.addEventListener("click", () => {
      const custId = document.getElementById("behavior-cust-search")?.value.trim();
      if (custId) {
        state.activeCustomer = custId;
        fetchCustomerBehavior(custId);
      }
    });
  }

  async function fetchCustomerBehavior(customerId) {
    try {
      const res = await fetch(`/api/v1/customers/${customerId}/behavior`);
      if (!res.ok) throw new Error("Failed to load customer profile");
      const data = await res.json();

      document.getElementById("behavior-cust-id-badge").textContent = data.customer_id;
      const norm = data.normal_behavior || {};
      document.getElementById("beh-normal-amount").textContent = norm.average_amount_display || formatBDT(norm.average_amount, true);
      document.getElementById("beh-normal-hours").textContent = norm.typical_hours || "08:00–22:00";
      document.getElementById("beh-normal-devices").textContent = `${norm.known_devices_count || 1} Devices`;
      document.getElementById("beh-normal-receivers").textContent = `${norm.known_receivers_count || 1} Beneficiaries`;
      document.getElementById("beh-normal-daily").textContent = `${norm.average_daily_transactions || 4} / day`;
      document.getElementById("beh-normal-loc").textContent = (norm.normal_locations || ["Dhaka"])[0];

      const curr = data.current_transaction || {};
      if (curr.transaction_id) {
        document.getElementById("beh-current-tx-badge").textContent = curr.transaction_id;
        document.getElementById("beh-curr-amount").textContent = curr.amount_display || formatBDT(curr.amount, true);
        document.getElementById("beh-curr-hour").textContent = curr.hour_display || `${curr.hour}:00`;
        document.getElementById("beh-curr-device").textContent = curr.is_new_device ? "NEW / UNSEEN" : curr.device;
        document.getElementById("beh-curr-receiver").textContent = curr.is_new_receiver ? "NEW / UNSEEN" : curr.receiver;
        document.getElementById("beh-curr-loc").textContent = `${curr.location} (${curr.location_status})`;
        document.getElementById("beh-curr-velocity").textContent = curr.velocity_display || `${curr.velocity_1h}/hour`;
      }

      // Render Deviations
      const devContainer = document.getElementById("beh-deviations-container");
      const devList = (data.behavioral_deviations || {}).deviations_list || [];
      if (devList.length) {
        devContainer.innerHTML = devList.map(d => `<div>• ${d}</div>`).join("");
      } else {
        devContainer.innerHTML = `<div>• All metrics conform to customer's baseline operating window.</div>`;
      }

      // Render Recent Transactions
      const tbody = document.getElementById("behavior-tx-table")?.querySelector("tbody");
      if (tbody) {
        const txs = data.recent_transactions || [];
        tbody.innerHTML = txs.map(t => `
          <tr>
            <td style="font-weight: 600; color: #60a5fa;">${t.transaction_id}</td>
            <td style="font-size: 0.78rem; color: var(--text-dim);">${t.timestamp || '--'}</td>
            <td>${t.transaction_type}</td>
            <td>${t.channel}</td>
            <td style="font-weight: 600;">${t.amount_display || formatBDT(t.amount, true)}</td>
            <td>${t.receiver_id || '--'}</td>
            <td>${t.location || '--'}</td>
            <td><span class="badge ${t.risk_level.toLowerCase()}">${t.risk_score.toFixed(1)}</span></td>
            <td>
              <button class="btn-action" onclick="window.appOpenInvestigation('${t.transaction_id}')">Investigate</button>
            </td>
          </tr>
        `).join("");
      }

    } catch (err) {
      console.error("Behavior error:", err);
      showToast("Error loading customer baseline", true);
    }
  }

  // ==========================================
  // VIEW 5: SCAM PATTERN INTELLIGENCE
  // ==========================================
  function setupScamIntelligenceView() {
    // Loaded on switchView
  }

  async function loadScamAlerts() {
    const tbody = document.getElementById("scam-alerts-tbody");
    if (!tbody) return;

    try {
      const res = await fetch("/api/v1/transactions?risk_level=HIGH&limit=10");
      if (!res.ok) throw new Error("Failed to load high risk transactions");
      const data = await res.json();

      const rows = [];
      for (const tx of data.transactions) {
        const scamRes = await fetch(`/api/v1/transactions/${tx.transaction_id}/scam-intelligence`);
        if (scamRes.ok) {
          const scamData = await scamRes.json();
          const patterns = scamData.patterns_detected || [];
          const patName = patterns.length ? patterns[0].pattern_name : "Unusual Transfer Pattern";
          const signals = (scamData.signals_summary || []).slice(0, 3).join(", ") || "Elevated amount deviation";

          rows.push(`
            <tr>
              <td style="font-weight: 600; color: #60a5fa;">${tx.transaction_id}</td>
              <td>${tx.customer_id || '--'}</td>
              <td style="font-weight: 600;">${formatBDT(tx.amount, true)}</td>
              <td style="font-size: 0.76rem; color: #cbd5e1;">${signals}</td>
              <td style="font-weight: 600; color: #fbbf24;">${patName}</td>
              <td><span class="badge high">${scamData.highest_severity || 'HIGH'}</span></td>
              <td><span style="font-size: 0.74rem; color: #38bdf8;">Requires Investigation</span></td>
              <td>
                <button class="btn-action" onclick="window.appOpenInvestigation('${tx.transaction_id}')">Investigate</button>
              </td>
            </tr>
          `);
        }
      }

      tbody.innerHTML = rows.join("") || `<tr><td colspan="8" style="text-align: center;">No active scam patterns detected.</td></tr>`;
    } catch (err) {
      console.error("Scam intelligence error:", err);
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #f87171;">Error loading scam patterns.</td></tr>`;
    }
  }

  // ==========================================
  // VIEW 6: SUSPICIOUS NETWORK INTELLIGENCE
  // ==========================================
  function setupNetworkView() {
    document.getElementById("btn-search-network")?.addEventListener("click", () => {
      const custId = document.getElementById("network-cust-search")?.value.trim();
      if (custId) exploreCustomerNetwork(custId);
    });
  }

  async function loadNetworkPatterns() {
    const tbodyRec = document.getElementById("tbody-network-receivers");
    const tbodyDev = document.getElementById("tbody-network-devices");
    if (!tbodyRec || !tbodyDev) return;

    try {
      const res = await fetch("/api/v1/network/patterns");
      if (!res.ok) throw new Error("Failed to load network patterns");
      const data = await res.json();

      tbodyRec.innerHTML = (data.high_fan_in_beneficiaries || []).map(r => `
        <tr>
          <td style="font-weight: 600; color: #60a5fa;">${r.receiver_id}</td>
          <td style="font-weight: 700; color: #f59e0b;">${r.unique_senders_count} accounts</td>
          <td>${r.transaction_count} txs</td>
          <td style="font-weight: 600;">${formatBDT(r.total_volume, true)}</td>
          <td><span class="badge high" style="font-size: 0.7rem;">Fan-In Inflow</span></td>
        </tr>
      `).join("");

      tbodyDev.innerHTML = (data.cross_account_shared_devices || []).map(d => `
        <tr>
          <td style="font-weight: 600; color: #cbd5e1;">${d.device_id}</td>
          <td style="font-weight: 700; color: #f87171;">${d.unique_users_count} accounts</td>
          <td>${d.transaction_count} txs</td>
          <td><span class="badge high" style="font-size: 0.7rem;">Hardware Re-use</span></td>
        </tr>
      `).join("");

    } catch (err) {
      console.error("Network patterns error:", err);
      tbodyRec.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #f87171;">Error loading network patterns.</td></tr>`;
    }
  }

  async function exploreCustomerNetwork(customerId) {
    try {
      const res = await fetch(`/api/v1/customers/${customerId}/network`);
      if (!res.ok) throw new Error("Failed to load customer network graph");
      const data = await res.json();

      document.getElementById("net-connected-cust").textContent = data.connected_customers;
      document.getElementById("net-shared-recv").textContent = data.shared_receivers;
      document.getElementById("net-shared-dev").textContent = data.shared_devices;
      document.getElementById("net-shared-loc").textContent = data.shared_locations;
      document.getElementById("net-tx-count").textContent = data.transaction_count;
      document.getElementById("net-total-bdt").textContent = data.total_amount_display || formatBDT(data.total_transaction_amount_bdt, true);

      renderNetworkSVG(data.nodes, data.edges);

    } catch (err) {
      console.error("Customer network error:", err);
      showToast("Error exploring customer network", true);
    }
  }

  function renderNetworkSVG(nodes, edges) {
    const svg = document.getElementById("network-svg");
    if (!svg || !nodes.length) return;

    svg.innerHTML = "";
    const width = svg.clientWidth || 700;
    const height = svg.clientHeight || 360;
    const cx = width / 2;
    const cy = height / 2;

    const colorMap = {
      customer: "#60a5fa",
      receiver: "#f87171",
      device: "#fbbf24",
      location: "#34d399"
    };

    // Position center customer
    const primaryNode = nodes.find(n => n.primary) || nodes[0];
    const otherNodes = nodes.filter(n => n !== primaryNode);
    const radius = Math.min(width, height) * 0.38;

    primaryNode.x = cx;
    primaryNode.y = cy;

    otherNodes.forEach((node, idx) => {
      const angle = (idx / otherNodes.length) * 2 * Math.PI;
      node.x = cx + radius * Math.cos(angle);
      node.y = cy + radius * Math.sin(angle);
    });

    // Draw edges
    edges.forEach(e => {
      const s = nodes.find(n => n.id === e.source) || primaryNode;
      const t = nodes.find(n => n.id === e.target) || otherNodes[0];
      if (s && t) {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", s.x);
        line.setAttribute("y1", s.y);
        line.setAttribute("x2", t.x);
        line.setAttribute("y2", t.y);
        line.setAttribute("stroke", "rgba(255,255,255,0.18)");
        line.setAttribute("stroke-width", "1.5");
        svg.appendChild(line);
      }
    });

    // Draw nodes
    nodes.forEach(node => {
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      g.style.cursor = "pointer";

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", node.x);
      circle.setAttribute("cy", node.y);
      circle.setAttribute("r", node.primary ? 18 : 12);
      circle.setAttribute("fill", colorMap[node.type] || "#38bdf8");
      circle.setAttribute("stroke", "#ffffff");
      circle.setAttribute("stroke-width", "2");

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", node.x);
      text.setAttribute("y", node.y + (node.primary ? 32 : 24));
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("fill", "#cbd5e1");
      text.setAttribute("font-size", "10px");
      text.textContent = node.id;

      g.appendChild(circle);
      g.appendChild(text);

      g.addEventListener("click", () => {
        const detail = document.getElementById("network-node-detail");
        if (detail) {
          detail.innerHTML = `<strong>Selected Entity:</strong> ${node.label} [Type: ${node.type.toUpperCase()}]`;
        }
      });

      svg.appendChild(g);
    });
  }

  // ==========================================
  // VIEW 7: ANALYST CASE MANAGEMENT
  // ==========================================
  function setupCaseManagementView() {
    const filterStatus = document.getElementById("filter-case-status");
    const filterPriority = document.getElementById("filter-case-priority");

    filterStatus?.addEventListener("change", loadCases);
    filterPriority?.addEventListener("change", loadCases);
  }

  async function loadCases() {
    const tbody = document.getElementById("cases-tbody");
    if (!tbody) return;

    const statusVal = document.getElementById("filter-case-status")?.value || "ALL";
    const priorityVal = document.getElementById("filter-case-priority")?.value || "ALL";

    try {
      const params = new URLSearchParams();
      if (statusVal !== "ALL") params.append("status", statusVal);
      if (priorityVal !== "ALL") params.append("priority", priorityVal);

      const res = await fetch(`/api/v1/cases?${params.toString()}`);
      if (!res.ok) throw new Error("Failed to load cases");
      const data = await res.json();

      const cases = data.cases || [];
      const total = data.total || 0;
      const open = cases.filter(c => c.status === "OPEN").length;
      const review = cases.filter(c => c.status === "UNDER_REVIEW").length;
      const info = cases.filter(c => c.status === "NEEDS_MORE_INFORMATION").length;
      const resolved = cases.filter(c => c.status === "RESOLVED").length;

      document.getElementById("case-stat-total").textContent = total;
      document.getElementById("case-stat-open").textContent = open;
      document.getElementById("case-stat-review").textContent = review;
      document.getElementById("case-stat-info").textContent = info;
      document.getElementById("case-stat-resolved").textContent = resolved;

      if (!cases.length) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-dim);">No cases found.</td></tr>`;
        return;
      }

      tbody.innerHTML = cases.map(c => {
        const pClass = c.priority === "CRITICAL" ? "high" : (c.priority === "HIGH" ? "high" : "medium");
        const sClass = c.status === "RESOLVED" ? "low" : (c.status === "OPEN" ? "high" : "medium");

        return `
          <tr>
            <td style="font-weight: 700; color: #38bdf8;">${c.case_id}</td>
            <td style="font-weight: 600; color: #60a5fa;">${c.transaction_id}</td>
            <td>${c.customer_id || '--'}</td>
            <td><span class="badge ${c.risk_score >= 80 ? 'high' : 'medium'}">${c.risk_score.toFixed(1)}</span></td>
            <td><span class="badge ${pClass}">${c.priority}</span></td>
            <td><span class="badge ${sClass}">${c.status}</span></td>
            <td>${c.assigned_analyst || 'Unassigned'}</td>
            <td style="font-weight: 600; color: ${c.decision ? '#34d399' : 'var(--text-dim)'};">${c.decision || 'PENDING'}</td>
            <td style="font-size: 0.74rem; color: var(--text-dim);">${c.created_at ? c.created_at.split('T')[0] : '--'}</td>
            <td>
              <button class="btn-action" onclick="window.appOpenInvestigation('${c.transaction_id}')">Workspace</button>
            </td>
          </tr>
        `;
      }).join("");

    } catch (err) {
      console.error("Load cases error:", err);
      tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: #f87171;">Error loading case records.</td></tr>`;
    }
  }

  // ==========================================
  // VIEW 9: MODEL MONITORING & DATA DRIFT
  // ==========================================
  function setupModelMonitoringView() {
    document.getElementById("btn-export-retraining")?.addEventListener("click", exportRetrainingCSV);
  }

  async function loadMonitoringData() {
    try {
      // 1. Model Health
      const healthRes = await fetch("/api/v1/model/health");
      if (healthRes.ok) {
        const h = await healthRes.json();
        document.getElementById("mon-version").textContent = h.version;
        document.getElementById("mon-train-samples").textContent = h.training_samples.toLocaleString();
        document.getElementById("mon-test-samples").textContent = h.test_samples.toLocaleString();
        const ev = h.evaluation_metrics || {};
        document.getElementById("mon-precision").textContent = `${((ev.precision ?? 1.0) * 100).toFixed(1)}%`;
        document.getElementById("mon-recall").textContent = `${((ev.recall ?? 1.0) * 100).toFixed(1)}%`;
        document.getElementById("mon-roc-auc").textContent = (ev.roc_auc ?? 1.0).toFixed(3);
      }

      // 2. Data Drift
      const driftRes = await fetch("/api/v1/model/drift");
      if (driftRes.ok) {
        const d = await driftRes.json();
        const badge = document.getElementById("mon-overall-drift-badge");
        badge.textContent = `${d.overall_drift_status} DRIFT`;
        badge.className = `badge ${d.overall_drift_status === 'HIGH' ? 'high' : (d.overall_drift_status === 'MEDIUM' ? 'medium' : 'low')}`;
        document.getElementById("mon-drift-msg").textContent = d.status_message;

        const tbody = document.getElementById("drift-tbody");
        if (tbody) {
          tbody.innerHTML = (d.features_drift || []).map(f => `
            <tr>
              <td style="font-weight: 600;">${f.feature.replace(/_/g, ' ').toUpperCase()}</td>
              <td style="font-weight: 700; color: #38bdf8;">${f.drift_score.toFixed(4)}</td>
              <td><span class="badge ${f.drift_level === 'HIGH' ? 'high' : (f.drift_level === 'MEDIUM' ? 'medium' : 'low')}">${f.drift_level}</span></td>
              <td>${f.reference_mean.toFixed(2)}</td>
              <td>${f.current_mean.toFixed(2)}</td>
              <td style="font-size: 0.76rem; color: var(--text-muted);">${f.distribution_shift}</td>
            </tr>
          `).join("");
        }
      }

      // 3. Feedback stats
      const fbRes = await fetch("/api/v1/feedback/stats");
      if (fbRes.ok) {
        const fb = await fbRes.json();
        document.getElementById("fb-total-reviewed").textContent = fb.total_reviewed;
        document.getElementById("fb-confirmed-suspicious").textContent = fb.confirmed_suspicious;
        document.getElementById("fb-marked-legitimate").textContent = fb.marked_legitimate;
        document.getElementById("fb-needs-investigation").textContent = fb.needs_investigation;
      }

    } catch (err) {
      console.error("Monitoring error:", err);
      showToast("Error loading model monitoring telemetry", true);
    }
  }

  async function exportRetrainingCSV() {
    showToast("Preparing retraining dataset export...");
    try {
      const res = await fetch("/api/v1/feedback/export", { method: "POST" });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "upay_retraining_feedback_dataset.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast("Retraining dataset successfully downloaded!");
    } catch (err) {
      console.error("Export error:", err);
      showToast("Error exporting retraining dataset", true);
    }
  }

  // ==========================================
  // FULL INVESTIGATION WORKSPACE (DRAWER)
  // ==========================================
  function setupInvestigationDrawer() {
    btnCloseDrawer?.addEventListener("click", closeDrawer);
    drawerOverlay?.addEventListener("click", closeDrawer);

    // Quick Inquiry Pills
    document.querySelectorAll(".prompt-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        const q = pill.getAttribute("data-q");
        sendChatMessage(q);
      });
    });

    // Send Button & Enter Key
    document.getElementById("btn-send-chat")?.addEventListener("click", () => {
      const input = document.getElementById("drawer-chat-input");
      const val = input.value.trim();
      if (val) {
        sendChatMessage(val);
        input.value = "";
      }
    });

    document.getElementById("drawer-chat-input")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const input = document.getElementById("drawer-chat-input");
        const val = input.value.trim();
        if (val) {
          sendChatMessage(val);
          input.value = "";
        }
      }
    });

    // Create Formal Case Button in Drawer
    document.getElementById("btn-create-case-from-drawer")?.addEventListener("click", createCaseFromDrawer);

    // Feedback Decision Buttons
    document.getElementById("btn-feedback-suspicious")?.addEventListener("click", () => submitFeedback("CONFIRM_SUSPICIOUS"));
    document.getElementById("btn-feedback-legitimate")?.addEventListener("click", () => submitFeedback("MARK_LEGITIMATE"));
    document.getElementById("btn-feedback-review")?.addEventListener("click", () => submitFeedback("NEEDS_MORE_INVESTIGATION"));
  }

  window.appOpenInvestigation = function(transactionId) {
    openInvestigation(transactionId);
  };

  async function openInvestigation(transactionId) {
    state.activeTransactionId = transactionId;
    drawerOverlay.classList.add("active");
    drawer.classList.add("active");

    // Reset drawer state
    document.getElementById("drawer-tx-id").textContent = `Transaction ${transactionId}`;
    document.getElementById("drawer-chat-log").innerHTML = "";
    document.getElementById("feedback-notes").value = "";
    document.getElementById("ai-loading").style.display = "block";
    document.getElementById("ai-content-box").style.display = "none";

    try {
      // 1. Fetch transaction details
      const txRes = await fetch(`/api/v1/transactions/${transactionId}`);
      if (!txRes.ok) throw new Error("Transaction details not found");
      const tx = await txRes.json();
      state.activeTransactionData = tx;

      document.getElementById("drawer-amount").textContent = formatBDT(tx.amount, true);
      document.getElementById("drawer-customer").textContent = tx.customer_id || '--';
      document.getElementById("drawer-receiver").textContent = tx.receiver_id || '--';
      document.getElementById("drawer-location").textContent = tx.location || 'Standard';
      document.getElementById("drawer-device").textContent = tx.device_id || 'Hardware ID';
      document.getElementById("drawer-deviation").textContent = `${tx.amount_deviation ? tx.amount_deviation.toFixed(1) : '1.0'}x baseline`;
      document.getElementById("drawer-tx-timestamp").textContent = `Recorded: ${tx.timestamp || 'Real-time'}`;

      // 2. Fetch Prediction & SHAP
      const predRes = await fetch("/api/v1/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transaction_id: transactionId })
      });
      const pred = await predRes.json();

      document.getElementById("drawer-risk-score").textContent = pred.risk_score.toFixed(1);
      document.getElementById("drawer-action").textContent = pred.recommended_action;

      const badgeElem = document.getElementById("drawer-risk-badge");
      if (pred.risk_level === "HIGH") {
        badgeElem.innerHTML = `<span class="badge high">HIGH RISK</span>`;
        document.getElementById("drawer-risk-score").style.color = "#f87171";
      } else if (pred.risk_level === "MEDIUM") {
        badgeElem.innerHTML = `<span class="badge medium">MEDIUM RISK</span>`;
        document.getElementById("drawer-risk-score").style.color = "#fbbf24";
      } else {
        badgeElem.innerHTML = `<span class="badge low">LOW RISK</span>`;
        document.getElementById("drawer-risk-score").style.color = "#34d399";
      }

      // Render SHAP factors with exact local values
      renderDrawerSHAP(pred.shap_factors || []);

      // 3. Trigger Investigation (Behavioral + ATO + Scam + Timeline + Network + Gemini)
      const invRes = await fetch("/api/v1/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transaction_id: transactionId })
      });
      const inv = await invRes.json();

      document.getElementById("ai-loading").style.display = "none";
      document.getElementById("ai-content-box").style.display = "block";

      // AI Summary
      document.getElementById("ai-summary-text").textContent = inv.summary;

      // Key Risk Signals
      const findingsList = document.getElementById("ai-findings-list");
      findingsList.innerHTML = (inv.risk_signals || inv.key_findings || []).map(f => `<li>${f}</li>`).join("");

      // Behavioral Deviations
      const devList = document.getElementById("ai-deviations-list");
      devList.innerHTML = (inv.behavioral_deviations || []).map(d => `<li>${d}</li>`).join("");

      // Specific Evidence to Verify
      const evidenceList = document.getElementById("ai-evidence-list");
      evidenceList.innerHTML = (inv.investigation_questions || inv.evidence_to_review || []).map(e => `<li>${e}</li>`).join("");

      // Render Risk Story Timeline
      renderRiskTimeline(inv.risk_story);

      // Render Scam Intelligence Patterns
      renderScamPatterns(inv.scam_intelligence);

      // Render Customer Behavioral Baseline Comparison Table
      renderBaselineComparison(inv.behavioral_comparison, inv.customer_baseline);

      // Render Account Takeover (ATO) Indicators
      renderATOSection(inv.ato_intelligence);

      // Render Entity Relationship Network Insights
      renderNetworkInsights(inv.network_graph);

    } catch (err) {
      console.error("Open investigation error:", err);
      document.getElementById("ai-loading").style.display = "none";
      document.getElementById("ai-content-box").style.display = "block";
      showToast("Error loading investigation workspace", true);
    }
  }

  function renderRiskTimeline(story) {
    const container = document.getElementById("drawer-timeline-container");
    if (!container || !story) return;

    const events = story.timeline_events || [];
    container.innerHTML = events.map(ev => {
      const bulletClass = ev.severity ? ev.severity.toLowerCase() : "normal";
      return `
        <div class="timeline-item">
          <div class="timeline-bullet ${bulletClass}">
            ${ev.icon || '●'}
          </div>
          <div class="timeline-body">
            <div style="display: flex; justify-content: space-between; font-size: 0.74rem; color: var(--text-dim); margin-bottom: 2px;">
              <span>${ev.time}</span>
              <span class="badge ${bulletClass === 'critical' ? 'high' : (bulletClass === 'warning' ? 'medium' : 'low')}" style="font-size: 0.65rem;">${ev.event_type}</span>
            </div>
            <div style="font-size: 0.82rem; font-weight: 600; color: #cbd5e1;">${ev.description}</div>
          </div>
        </div>
      `;
    }).join("");
  }

  function renderScamPatterns(scam) {
    const list = document.getElementById("drawer-scam-patterns-list");
    const badge = document.getElementById("drawer-scam-badge");
    if (!list || !scam) return;

    const patterns = scam.patterns_detected || [];
    if (badge) {
      badge.textContent = scam.status || "Requires Investigation";
      badge.className = `badge ${scam.highest_severity === 'CRITICAL' ? 'high' : 'medium'}`;
    }

    if (!patterns.length) {
      list.innerHTML = `<p style="font-size: 0.78rem; color: var(--text-dim);">No active scam patterns detected for this transfer.</p>`;
      return;
    }

    list.innerHTML = patterns.map(p => `
      <div style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 8px 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 0.82rem; font-weight: 700; color: #fbbf24;">${p.pattern_name}</span>
          <span class="badge ${p.severity === 'CRITICAL' ? 'high' : 'medium'}" style="font-size: 0.65rem;">${p.severity}</span>
        </div>
        <p style="font-size: 0.76rem; color: var(--text-muted); margin-top: 4px;">${p.description}</p>
        <div style="font-size: 0.72rem; color: #cbd5e1; margin-top: 4px;">Signals: ${p.matched_signals.join(", ")}</div>
      </div>
    `).join("");
  }

  function renderDrawerSHAP(factors) {
    const container = document.getElementById("drawer-shap-container");
    if (!factors.length) {
      container.innerHTML = `<p style="font-size:0.8rem; color:var(--text-dim);">No significant SHAP deviations detected.</p>`;
      return;
    }

    container.innerHTML = factors.map(f => {
      const isRisk = f.impact === "RISK_INCREASING";
      const barClass = isRisk ? "shap-fill-risk" : "shap-fill-safe";
      const width = Math.min(100, Math.max(15, Math.abs(f.shap_value) * 16));

      return `
        <div class="shap-factor-row">
          <div class="shap-factor-header">
            <span>#${f.importance_rank} ${f.feature.replace(/_/g, ' ').toUpperCase()} (${f.feature_value})</span>
            <span style="color: ${isRisk ? '#f87171' : '#34d399'}; font-weight: 700;">
              ${isRisk ? '+' : ''}${f.shap_value.toFixed(4)}
            </span>
          </div>
          <div class="shap-factor-bar">
            <div class="${barClass}" style="height: 100%; width: ${width}%;"></div>
          </div>
          <div class="shap-explanation">${f.explanation}</div>
        </div>
      `;
    }).join("");
  }

  function renderBaselineComparison(comp, baseline) {
    const tbody = document.getElementById("drawer-baseline-tbody");
    if (!tbody || !comp) return;

    tbody.innerHTML = `
      <tr>
        <td style="font-weight: 600;">Transaction Amount (BDT)</td>
        <td>${comp.normal_avg_amount || '৳1,250.00'}</td>
        <td style="font-weight: 700; color: #f87171;">${comp.current_amount ? (comp.current_amount.startsWith('৳') ? comp.current_amount : formatBDT(comp.current_amount, true)) : '৳0.00'}</td>
        <td><span style="color: #f59e0b; font-weight: 700;">${comp.amount_deviation_ratio} Surge</span></td>
      </tr>
      <tr>
        <td style="font-weight: 600;">Active Hours</td>
        <td>${comp.typical_hours || '08:00–22:00'}</td>
        <td>${comp.current_hour}</td>
        <td>${comp.is_unusual_hour ? '<span style="color:#f87171; font-weight:600;">Circadian Disruption</span>' : '<span style="color:#34d399;">Normal Hours</span>'}</td>
      </tr>
      <tr>
        <td style="font-weight: 600;">Hardware Device</td>
        <td>${baseline ? baseline.known_devices_count : 2} registered devices</td>
        <td>${comp.new_device === 'YES' ? '<span style="color:#f87171; font-weight:600;">Unregistered Hardware</span>' : 'Registered Device'}</td>
        <td>${comp.new_device === 'YES' ? '<span class="badge high" style="font-size:0.7rem;">New Device</span>' : '<span class="badge low" style="font-size:0.7rem;">Known</span>'}</td>
      </tr>
      <tr>
        <td style="font-weight: 600;">Beneficiary Recipient</td>
        <td>${baseline ? baseline.known_receivers_count : 5} past recipients</td>
        <td>${comp.new_receiver === 'YES' ? '<span style="color:#f87171; font-weight:600;">First-Time Beneficiary</span>' : 'Known Recipient'}</td>
        <td>${comp.new_receiver === 'YES' ? '<span class="badge high" style="font-size:0.7rem;">New Recipient</span>' : '<span class="badge low" style="font-size:0.7rem;">Known</span>'}</td>
      </tr>
      <tr>
        <td style="font-weight: 600;">Transaction Velocity</td>
        <td>${comp.velocity_24h || '4 tx/day'}</td>
        <td style="font-weight: 700; color: #f59e0b;">${comp.velocity_1h}</td>
        <td>${parseInt(comp.velocity_1h) >= 5 ? '<span style="color:#f87171; font-weight:600;">Burst Velocity</span>' : '<span style="color:#34d399;">Expected Pace</span>'}</td>
      </tr>
    `;
  }

  function renderATOSection(ato) {
    const card = document.getElementById("drawer-ato-card");
    const badge = document.getElementById("drawer-ato-badge");
    const headline = document.getElementById("drawer-ato-headline");
    const list = document.getElementById("drawer-ato-signals-list");
    if (!card || !ato) return;

    badge.className = `badge ${ato.severity.toLowerCase()}`;
    badge.textContent = `${ato.severity} ATO RISK (${ato.ato_score}/100)`;
    headline.textContent = ato.headline;

    if (!ato.detected_signals || !ato.detected_signals.length) {
      list.innerHTML = `<li>No critical account takeover combinations observed in this session.</li>`;
      return;
    }

    list.innerHTML = ato.detected_signals.map(s => `
      <li style="margin-bottom: 4px;">
        <strong style="color: #f87171;">${s.label}:</strong> ${s.description}
      </li>
    `).join("");
  }

  function renderNetworkInsights(net) {
    const container = document.getElementById("drawer-network-insights");
    const pill = document.getElementById("drawer-network-summary-pill");
    if (!container || !net) return;

    const countSenders = net.summary ? net.summary.distinct_customers_to_receiver : 1;
    pill.textContent = countSenders >= 3 ? `${countSenders} Coordinated Inflow Senders` : "Single Account Profile";

    container.innerHTML = (net.insights || []).map(ins => `
      <div style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 10px; margin-bottom: 8px;">
        <span style="font-size: 0.8rem; font-weight: 700; color: ${ins.severity === 'HIGH' ? '#f87171' : '#60a5fa'};">${ins.pattern}</span>
        <p style="font-size: 0.76rem; color: var(--text-muted); margin-top: 2px;">${ins.description}</p>
      </div>
    `).join("");
  }

  async function createCaseFromDrawer() {
    if (!state.activeTransactionId) return;

    try {
      const res = await fetch("/api/v1/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transaction_id: state.activeTransactionId,
          priority: "HIGH",
          assigned_analyst: "lead_fraud_analyst",
          analyst_notes: "Opened from investigation workspace."
        })
      });
      if (!res.ok) throw new Error("Failed to create case");
      const data = await res.json();
      showToast(`Formal case ${data.case_id} successfully created!`);
      loadCases();
    } catch (err) {
      console.error("Create case error:", err);
      showToast("Error opening case", true);
    }
  }

  async function sendChatMessage(message) {
    if (!state.activeTransactionId) return;

    const chatLog = document.getElementById("drawer-chat-log");

    // Analyst Message Bubble
    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble analyst";
    userBubble.textContent = message;
    chatLog.appendChild(userBubble);
    chatLog.scrollTop = chatLog.scrollHeight;

    // Assistant Thinking Bubble
    const botBubble = document.createElement("div");
    botBubble.className = "chat-bubble assistant";
    botBubble.textContent = "Analyzing transaction telemetry, baseline, and ATO evidence...";
    chatLog.appendChild(botBubble);
    chatLog.scrollTop = chatLog.scrollHeight;

    try {
      const res = await fetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transaction_id: state.activeTransactionId,
          message: message
        })
      });
      if (!res.ok) throw new Error("Chat request failed");
      const data = await res.json();

      botBubble.textContent = data.reply;
      chatLog.scrollTop = chatLog.scrollHeight;
    } catch (err) {
      console.error("Chat error:", err);
      botBubble.textContent = "Service fallback active: Consult observed SHAP factors and ATO signals above.";
    }
  }

  async function submitFeedback(decision) {
    if (!state.activeTransactionId) return;

    const notes = document.getElementById("feedback-notes").value.trim();

    try {
      // 1. Submit feedback
      const res = await fetch("/api/v1/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transaction_id: state.activeTransactionId,
          decision: decision,
          comment: notes,
          reason: notes,
          analyst_id: "lead_fraud_analyst"
        })
      });

      if (!res.ok) throw new Error("Feedback submission failed");

      // 2. Also record decision on case if case exists
      const casesRes = await fetch("/api/v1/cases");
      if (casesRes.ok) {
        const cdata = await casesRes.json();
        const activeCase = (cdata.cases || []).find(c => c.transaction_id === state.activeTransactionId);
        if (activeCase) {
          await fetch(`/api/v1/cases/${activeCase.case_id}/decision`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              decision: decision,
              analyst_notes: notes,
              analyst_id: "lead_fraud_analyst"
            })
          });
        }
      }

      showToast(`Analyst Decision '${decision.replace(/_/g, ' ')}' permanently logged in audit database.`);
      closeDrawer();
      loadDashboardData();
      if (state.currentView === "cases-view") loadCases();
    } catch (err) {
      console.error("Feedback error:", err);
      showToast("Error saving analyst decision", true);
    }
  }

  function closeDrawer() {
    drawerOverlay.classList.remove("active");
    drawer.classList.remove("active");
    state.activeTransactionId = null;
  }

  function showToast(message, isError = false) {
    if (!toast) return;
    toast.textContent = message;
    toast.style.borderColor = isError ? "#ef4444" : "#3b82f6";
    toast.style.display = "block";
    setTimeout(() => {
      toast.style.display = "none";
    }, 3500);
  }
});
