// Weather-Driven Business Intelligence Platform - Standalone Web Client

const state = {
    city: "NYC",
    catalog: [],
    selectedKey: "nyc_taxi",
    selectedKeys: ["nyc_taxi"],
    customBusinesses: {},
    weather: null,
    activeTab: "tab1",
    inspectedDayIdx: 6,
    horizon: "Last 6 Months (180 Days)",
    simDow: 0,
    simHour: 12,
    simRain: 0.0,
    simTempAnom: 0.0,
    simWind: 12.0,
    isCustomSim: false
};

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", async () => {
    setupTabNavigation();
    setupEventListeners();
    await loadInitialState();
});

// Setup Tab Switching
function setupTabNavigation() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            const targetId = tab.getAttribute("data-tab");
            document.getElementById(targetId).classList.add("active");
            state.activeTab = targetId;

            // Trigger chart resize for any Plotly chart in the newly visible tab
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 60);

            // Fetch data for the active tab if needed
            if (targetId === "tab3") {
                loadDominoData();
            } else if (targetId === "tab4") {
                loadNowcastData();
            } else if (targetId === "tab5") {
                loadDiagnosticsData();
            }
        });
    });
}

// Setup Event Listeners
function setupEventListeners() {
    // City Selector (if present)
    const citySelect = document.getElementById("citySelect");
    if (citySelect) {
        citySelect.addEventListener("change", async (e) => {
            state.city = e.target.value;
            await refreshAllForNewCity();
        });
    }

    // Single Business Selector Dropdown
    const businessSelect = document.getElementById("businessSelect");
    if (businessSelect) {
        businessSelect.addEventListener("change", async (e) => {
            state.selectedKey = e.target.value;
            state.selectedKeys = [state.selectedKey];
            state.inspectedDayIdx = null;
            updateCadenceBadge(state.selectedKey);
            updateHorizonOptions(state.selectedKey);
            await loadPortfolioData();
            if (state.activeTab === "tab3") await loadDominoData();
            if (state.activeTab === "tab4") await loadNowcastData();
        });
    }

    // Day in Review Select
    document.getElementById("daySelect").addEventListener("change", async (e) => {
        state.inspectedDayIdx = parseInt(e.target.value);
        await loadPortfolioData();
    });

    // Horizon Select (Tab 2)
    document.getElementById("horizonSelect").addEventListener("change", async (e) => {
        state.horizon = e.target.value;
        await loadPortfolioData();
    });

    // What-If Sliders (Tab 4)
    const simHour = document.getElementById("simHour");
    const simRain = document.getElementById("simRain");
    const simTempAnom = document.getElementById("simTempAnom");
    const simDay = document.getElementById("simDay");

    simHour.addEventListener("input", (e) => {
        document.getElementById("simHourVal").textContent = `${String(e.target.value).padStart(2, '0')}:00`;
    });
    simRain.addEventListener("input", (e) => {
        document.getElementById("simRainVal").textContent = `${parseFloat(e.target.value).toFixed(1)} mm`;
    });
    simTempAnom.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        document.getElementById("simTempAnomVal").textContent = `${val >= 0 ? '+' : ''}${val.toFixed(1)}°C`;
    });
    simDay.addEventListener("change", (e) => {
        const dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
        document.getElementById("simDayVal").textContent = dayNames[e.target.value];
    });

    // Simulation Buttons
    document.getElementById("btnApplySim").addEventListener("click", () => {
        state.simDow = parseInt(simDay.value);
        state.simHour = parseInt(simHour.value);
        state.simRain = parseFloat(simRain.value);
        state.simTempAnom = parseFloat(simTempAnom.value);
        state.isCustomSim = true;
        loadNowcastData();
    });

    document.getElementById("btnResetLive").addEventListener("click", () => {
        resetSimulationToLive();
        loadNowcastData();
    });

    // Custom Business Modal (if present)
    const customModal = document.getElementById("customBizModal");
    const openCustomBtn = document.getElementById("openCustomBizModal");
    if (customModal && openCustomBtn) {
        openCustomBtn.addEventListener("click", () => customModal.classList.add("active"));
        document.getElementById("closeCustomBizModal")?.addEventListener("click", () => customModal.classList.remove("active"));
        document.getElementById("cancelCustomBiz")?.addEventListener("click", () => customModal.classList.remove("active"));

        document.getElementById("customBizForm")?.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name = document.getElementById("newBizName").value.trim();
            const category_hint = document.getElementById("newBizCategory").value;
            const custom_rev = parseFloat(document.getElementById("newBizRev").value);
            const custom_color = document.getElementById("newBizColor").value;
            const custom_rain = parseFloat(document.getElementById("newBizRain").value);
            const custom_temp = parseFloat(document.getElementById("newBizTemp").value);

            try {
                const resp = await fetch("/api/custom-business", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, category_hint, custom_rev, custom_color, custom_rain, custom_temp })
                });
                const res = await resp.json();
                if (res.success) {
                    state.customBusinesses[res.slug] = res.config;
                    if (!state.selectedKeys.includes(res.slug)) {
                        state.selectedKeys.push(res.slug);
                    }
                    customModal.classList.remove("active");
                    document.getElementById("customBizForm").reset();
                    await loadInitialState();
                }
            } catch (err) {
                alert("Error creating business: " + err);
            }
        });
    }

    // Upload CSV Modal (if present)
    const uploadModal = document.getElementById("uploadCsvModal");
    const openUploadBtn = document.getElementById("openUploadCsvModal");
    if (uploadModal && openUploadBtn) {
        openUploadBtn.addEventListener("click", () => uploadModal.classList.add("active"));
        document.getElementById("closeUploadCsvModal")?.addEventListener("click", () => uploadModal.classList.remove("active"));
        document.getElementById("cancelUploadCsv")?.addEventListener("click", () => uploadModal.classList.remove("active"));

        document.getElementById("uploadCsvForm")?.addEventListener("submit", async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById("csvFileInput");
            if (!fileInput.files.length) return;

            const formData = new FormData();
            formData.append("file", fileInput.files[0]);
            formData.append("store_name", document.getElementById("storeName").value);
            formData.append("city", state.city);

            const statusEl = document.getElementById("uploadStatusText");
            statusEl.innerHTML = "<span style='color:#38BDF8;'>Analyzing transaction history and computing weather regressions...</span>";

            try {
                const resp = await fetch("/api/upload-csv", {
                    method: "POST",
                    body: formData
                });
                const res = await resp.json();
                if (res.success) {
                    state.customBusinesses[res.slug] = res.config;
                    if (!state.selectedKeys.includes(res.slug)) {
                        state.selectedKeys.push(res.slug);
                    }
                    uploadModal.classList.remove("active");
                    document.getElementById("uploadCsvForm").reset();
                    statusEl.innerHTML = "";
                    await loadInitialState();
                } else {
                    statusEl.innerHTML = `<span style='color:#FF5252;'>Error: ${res.error}</span>`;
                }
            } catch (err) {
                statusEl.innerHTML = `<span style='color:#FF5252;'>Upload failed: ${err}</span>`;
            }
        });
    }
}

// --- DATA FETCHING & RENDERING ---

async function loadInitialState() {
    try {
        const resp = await fetch(`/api/initial-state?city=${state.city}`);
        const data = await resp.json();

        state.catalog = data.catalog;
        state.weather = data.weather;
        if (data.default_selected && data.default_selected.length > 0) {
            state.selectedKey = data.default_selected[0];
            state.selectedKeys = [state.selectedKey];
        } else if (state.catalog && state.catalog.length > 0) {
            state.selectedKey = state.catalog[0].key;
            state.selectedKeys = [state.selectedKey];
        }

        // Render Business Dropdown
        renderBusinessDropdown();

        // Update Weather Ribbon
        renderWeatherRibbon(data.weather);

        // Reset Nowcast Defaults
        resetSimulationToLive();

        // Load Tab 1 & Tab 2
        await loadPortfolioData();

        // If another tab was active, refresh it too
        if (state.activeTab === "tab3") await loadDominoData();
        if (state.activeTab === "tab4") await loadNowcastData();
        if (state.activeTab === "tab5") await loadDiagnosticsData();

    } catch (err) {
        console.error("Failed to load initial state:", err);
    }
}

async function refreshAllForNewCity() {
    try {
        const resp = await fetch(`/api/weather?city=${state.city}`);
        state.weather = await resp.json();
        renderWeatherRibbon(state.weather);
        resetSimulationToLive();
        await loadPortfolioData();
        if (state.activeTab === "tab3") await loadDominoData();
        if (state.activeTab === "tab4") await loadNowcastData();
        if (state.activeTab === "tab5") await loadDiagnosticsData();
    } catch (err) {
        console.error("Failed to refresh city:", err);
    }
}

function resetSimulationToLive() {
    const cur_w = state.weather?.current || {};
    const now = new Date();
    // Monday is 0 in Python
    const dow = (now.getDay() + 6) % 7;
    const hour = now.getHours();
    const rain = parseFloat(cur_w.precipitation_mm || 0.0);
    const tempAnom = Math.round((parseFloat(cur_w.temperature_c || 18.0) - 18.0) * 10) / 10;

    state.simDow = dow;
    state.simHour = hour;
    state.simRain = rain;
    state.simTempAnom = tempAnom;
    state.isCustomSim = false;

    // Update UI controls
    document.getElementById("simDay").value = dow;
    document.getElementById("simHour").value = hour;
    document.getElementById("simRain").value = rain;
    document.getElementById("simTempAnom").value = tempAnom;

    const dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    document.getElementById("simDayVal").textContent = dayNames[dow];
    document.getElementById("simHourVal").textContent = `${String(hour).padStart(2, '0')}:00`;
    document.getElementById("simRainVal").textContent = `${rain.toFixed(1)} mm`;
    document.getElementById("simTempAnomVal").textContent = `${tempAnom >= 0 ? '+' : ''}${tempAnom.toFixed(1)}°C`;
}

// Currency Formatter
function formatCurrency(val) {
    if (val === null || val === undefined || isNaN(val)) return "$0";
    const num = Number(val);
    const sign = num < 0 ? "-$" : "";
    const absVal = Math.abs(num);
    if (absVal >= 1e9) {
        return `${sign}${(absVal / 1e9).toFixed(2)}B`;
    }
    if (absVal >= 1e6) {
        return `${sign}${(absVal / 1e6).toFixed(2)}M`;
    }
    return `${sign}${Math.round(absVal).toLocaleString()}`;
}

// Update Cadence Badge Pill
function updateCadenceBadge(bKey) {
    const badge = document.getElementById("cadenceBadge");
    if (!badge) return;
    const item = state.catalog.find(c => c.key === bKey);
    const cadence = item?.cadence || "daily";
    badge.className = `cadence-badge cadence-${cadence}`;
    if (cadence === "quarterly") {
        badge.textContent = "Quarterly SEC 10-Q";
    } else if (cadence === "hourly") {
        badge.textContent = "Hourly TLC Stream";
    } else {
        badge.textContent = item?.cadence_label || "Daily Operations";
    }
}

// Render Single-Business Dropdown for Real-World Production Datasets
function renderBusinessDropdown() {
    const select = document.getElementById("businessSelect");
    if (!select) return;
    select.innerHTML = "";

    state.catalog.forEach(item => {
        const opt = document.createElement("option");
        opt.value = item.key;
        const cadLabel = item.cadence_label || (item.cadence === 'quarterly' ? 'Quarterly' : item.cadence === 'hourly' ? 'Hourly' : 'Daily');
        opt.textContent = `${item.clean_name} (${cadLabel})`;
        if (item.key === state.selectedKey) {
            opt.selected = true;
        }
        select.appendChild(opt);
    });

    select.value = state.selectedKey;
    updateCadenceBadge(state.selectedKey);
    updateHorizonOptions(state.selectedKey);
}

function updateHorizonOptions(bKey) {
    const sel = document.getElementById("horizonSelect");
    if (!sel) return;
    if (bKey === "nyc_taxi") {
        sel.innerHTML = `
            <option value="Last 7 Days (1 Week)">Last 7 Days (1 Week)</option>
            <option value="Last 14 Days (2 Weeks)">Last 14 Days (2 Weeks)</option>
            <option value="Full Month (All 31 Days)" selected>Full Month (All 31 Days)</option>
        `;
    } else if (bKey === "citibike_nyc") {
        sel.innerHTML = `
            <option value="Last 30 Days (1 Month)">Last 30 Days (1 Month)</option>
            <option value="Last 90 Days (3 Months)">Last 90 Days (3 Months)</option>
            <option value="Full Season (All 120 Days)" selected>Full Season (All 120 Days)</option>
        `;
    } else if (bKey === "online_retail") {
        sel.innerHTML = `
            <option value="Last 3 Months (90 Days)">Last 3 Months (90 Days)</option>
            <option value="Last 6 Months (180 Days)">Last 6 Months (180 Days)</option>
            <option value="Full Year (All 305 Days)" selected>Full Year (All 305 Days)</option>
        `;
    } else if (bKey === "chipotle_sec") {
        sel.innerHTML = `
            <option value="Last 1 Year (4 Quarters)">Last 1 Year (4 Quarters)</option>
            <option value="Last 2 Years (8 Quarters)" selected>Last 2 Years (8 Quarters)</option>
            <option value="Full History (All 27 Filings)">Full History (All 27 Filings)</option>
        `;
    } else {
        sel.innerHTML = `
            <option value="Last 3 Months (90 Days)">Last 3 Months (90 Days)</option>
            <option value="Last 6 Months (180 Days)" selected>Last 6 Months (180 Days)</option>
            <option value="Full 2 Years (All Data)">Full 2 Years (All Data)</option>
        `;
    }
    state.horizon = sel.value;
}

const renderPortfolioChips = renderBusinessDropdown;
const renderPortfolioDropdown = renderBusinessDropdown;

// Render Weather Ribbon
function renderWeatherRibbon(pkg) {
    if (!pkg) return;
    const cur = pkg.current || {};
    const nasa = pkg.nasa_power || {};

    const cityMap = { "NYC": "New York City", "ORD": "Chicago", "SEA": "Seattle", "PHX": "Phoenix" };
    document.getElementById("weatherCityTitle").textContent = `${cityMap[state.city] || state.city} Live Weather Intelligence`;
    document.getElementById("weatherCondition").textContent = cur.condition || "Clear Sky";
    document.getElementById("nasaWorldviewLink").href = pkg.nasa_worldview_url || "https://worldview.earthdata.nasa.gov/";

    document.getElementById("wGroundTemp").textContent = `${(cur.temperature_c || 0).toFixed(1)}°C`;
    document.getElementById("wNasaTemp").textContent = `${(nasa.temperature_c ?? cur.temperature_c ?? 0).toFixed(1)}°C`;
    document.getElementById("wPrecip").textContent = `${(cur.precipitation_mm || 0).toFixed(1)} mm/h`;
    document.getElementById("wHumidity").textContent = `${Math.round(cur.humidity_pct || 0)}%`;
    document.getElementById("wWind").textContent = `${(cur.wind_kmh || 0).toFixed(1)} km/h`;
    document.getElementById("wConsensus").textContent = pkg.consensus_rating || "Consensus Active";

    const dot = document.getElementById("weatherLiveDot");
    dot.style.background = cur.is_live ? "#00E676" : "#FFB300";
    dot.style.boxShadow = cur.is_live ? "0 0 10px #00E676" : "0 0 10px #FFB300";
}

// Load Tab 1 & Tab 2 Portfolio Data
async function loadPortfolioData() {
    try {
        const resp = await fetch("/api/portfolio-data", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                city: state.city,
                selected_keys: [state.selectedKey],
                custom_businesses: state.customBusinesses,
                horizon: state.horizon,
                inspected_day_idx: state.inspectedDayIdx
            })
        });

        const data = await resp.json();
        if (data.error) {
            console.error("Portfolio error:", data.error);
            return;
        }

        const cadence = data.cadence || "daily";
        updateCadenceBadge(state.selectedKey);

        // 1. KPI Cards
        const m = data.metrics;
        const impactEl = document.getElementById("kpiShift");
        impactEl.textContent = formatCurrency(m.total_week_impact);
        impactEl.className = `metric-number ${m.total_week_impact >= 0 ? 'status-positive' : 'status-negative'}`;

        document.getElementById("kpiShiftSub").innerHTML = `
            <span class="${m.total_week_impact >= 0 ? 'status-positive' : 'status-negative'}">
                ${m.total_week_impact >= 0 ? 'Extra Gain' : 'Lost Sales'}
            </span> vs baseline
        `;

        document.getElementById("kpiEarned").textContent = formatCurrency(m.total_week_actual).replace(/^\+/, '');
        document.getElementById("kpiEarnedSub").textContent = `Expected: ${formatCurrency(m.total_week_base).replace(/^\+/, '')}`;

        const unitsEl = document.getElementById("kpiUnits");
        const unitsSub = document.getElementById("kpiUnitsSub");
        if (unitsEl && unitsSub) {
            if (cadence === "quarterly") {
                unitsEl.textContent = "1 Enterprise";
                unitsSub.textContent = "Filing: SEC 10-Q";
            } else if (cadence === "hourly") {
                unitsEl.textContent = "1 Fleet";
                unitsSub.textContent = "Market: NYC TLC";
            } else {
                unitsEl.textContent = "1 Business";
                unitsSub.textContent = `Market: ${state.city}`;
            }
        }

        document.getElementById("kpiRain").textContent = `${m.total_rain_week.toFixed(1)} mm`;

        // 2. Render 7-Day Chart
        render7DayChart(data.chart_7d, cadence);

        // 3. Render Day in Review
        renderDayInReview(data.day_in_review, data.chart_7d, cadence);

        // 4. Render Historical Timeline Chart
        renderHistoricalChart(data.historical_timeline, cadence);

        // 5. Render Econometrics Comparison Table
        renderEconometricsTable(data.econometrics_table);

    } catch (err) {
        console.error("Failed to load portfolio data:", err);
    }
}

// Render Tab 1 Chart
function render7DayChart(chartData, cadence) {
    const traces = [];

    // Revenue traces for each business (Solid actual, dashed baseline)
    chartData.businesses.forEach(b => {
        traces.push({
            x: chartData.x_labels,
            y: b.actual,
            name: `${b.clean_label} — Actual`,
            mode: "lines+markers",
            legendgroup: b.key,
            line: { color: b.color, width: 2.8, shape: "linear" },
            marker: { size: 7, color: b.color, symbol: b.symbol },
            yaxis: "y1",
            hovertemplate: `<b>${b.name}</b><br>Actual Sales: $%{y:,.0f}<extra></extra>`
        });

        traces.push({
            x: chartData.x_labels,
            y: b.baseline,
            name: `${b.clean_label} — Baseline`,
            mode: "lines",
            legendgroup: b.key,
            line: { color: b.color, width: 1.8, dash: "dash" },
            opacity: 0.65,
            yaxis: "y1",
            hovertemplate: `<b>${b.name} (Baseline)</b><br>Expected Sales: $%{y:,.0f}<extra></extra>`
        });
    });

    // Rainfall trace on bottom subplot (y2)
    traces.push({
        x: chartData.x_labels,
        y: chartData.rainfall,
        name: "Rainfall (mm)",
        mode: "lines+markers",
        line: { color: "#38BDF8", width: 2.0 },
        marker: { size: 6, color: "#38BDF8", symbol: "circle-open" },
        fill: "tozeroy",
        fillcolor: "rgba(56, 189, 248, 0.12)",
        yaxis: "y2",
        showlegend: false,
        hovertemplate: "Rainfall: %{y:.1f} mm<extra></extra>"
    });

    const layout = {
        template: "plotly_white",
        paper_bgcolor: "#ffffff",
        plot_bgcolor: "#ffffff",
        font: { family: "Inter, -apple-system, sans-serif", size: 11, color: "#172f2b" },
        height: 520,
        margin: { l: 85, r: 25, t: 30, b: 120 },
        grid: { rows: 2, columns: 1, pattern: 'independent', roworder: 'top to bottom' },
        yaxis: {
            title: { text: "Revenue ($)", standoff: 18 },
            automargin: true,
            fixedrange: true,
            domain: [0.38, 1.0],
            gridcolor: "#e7ebe3",
            zeroline: false
        },
        yaxis2: {
            title: { text: "Rain (mm)", standoff: 18 },
            automargin: true,
            fixedrange: true,
            domain: [0.0, 0.26],
            gridcolor: "#e7ebe3",
            zeroline: false
        },
        xaxis: {
            fixedrange: true,
            gridcolor: "#e7ebe3",
            tickfont: { size: 10.5, color: "#64736c" }
        },
        legend: {
            orientation: "h",
            yanchor: "top",
            y: -0.28,
            xanchor: "center",
            x: 0.5,
            font: { size: 10.5, color: "#172f2b" },
            bgcolor: "#ffffff",
            bordercolor: "#dce2d8",
            borderwidth: 1
        }
    };

    Plotly.newPlot("chart7d", traces, layout, { responsive: true, displayModeBar: false, scrollZoom: false, doubleClick: false });
}

// Render Day in Review Section
function renderDayInReview(dayReview, chart7d, cadence) {
    const daySelect = document.getElementById("daySelect");
    daySelect.innerHTML = "";

    chart7d.dates.forEach((dt, idx) => {
        const opt = document.createElement("option");
        opt.value = idx;
        opt.textContent = `${chart7d.days[idx]} (${dt}) — ${chart7d.icons[idx]}`;
        if (idx === dayReview.inspected_idx) opt.selected = true;
        daySelect.appendChild(opt);
    });

    if (dayReview.inspected_idx !== undefined && dayReview.inspected_idx !== null) {
        daySelect.value = String(dayReview.inspected_idx);
    }

    document.getElementById("dayHeaderSummary").innerHTML = `
        <strong>Interval:</strong> ${dayReview.day_name} (${dayReview.date_str}) &nbsp;|&nbsp; 
        <strong>Atmospheric / Source:</strong> ${dayReview.weather_icon} (${dayReview.temperature}°C, ${dayReview.rain} mm rain)
    `;

    // Render Cards
    const grid = document.getElementById("dayInsightsGrid");
    grid.innerHTML = "";

    dayReview.insights.forEach(ins => {
        const delta = ins.delta ?? 0;
        const sign = delta >= 0 ? "+$" : "-$";
        const badgeCls = delta >= 0 ? "status-positive" : "status-negative";
        const actualRev = ins.actual_rev ?? 0;
        const baselineRev = ins.baseline_rev ?? 0;
        const pctChange = ins.pct_change ?? (baselineRev > 0 ? (delta / baselineRev * 100) : 0);
        const bullets = ins.bullets || [ins.trigger, ins.reaction, ins.financial, ins.linkage, ins.guidance].filter(Boolean);
        const name = ins.name || ins.b_name || "Business Intelligence";

        const card = document.createElement("div");
        card.className = "insight-box";
        card.innerHTML = `
            <div>
                <div class="insight-top">
                    <span class="insight-title">${name}</span>
                    <span class="${badgeCls}">${sign}${Math.abs(Math.round(delta)).toLocaleString()} (${pctChange >= 0 ? '+' : ''}${pctChange.toFixed(1)}%)</span>
                </div>
                <div style="font-size: 0.82rem; color: var(--ink); font-weight: 600; margin-bottom: 8px;">
                    Earned: ${formatCurrency(actualRev).replace(/^\+/, '')} &nbsp;|&nbsp; Normal: ${formatCurrency(baselineRev).replace(/^\+/, '')}
                </div>
                <div class="insight-content">
                    <strong style="color: var(--ink); font-size: 0.92rem; display: block; margin-bottom: 5px;">${ins.headline || ''}</strong>
                    ${bullets.map(b => `• ${b}`).join("<br/>")}
                </div>
            </div>
            <div class="insight-bottom">Category: ${ins.category || 'General'}</div>
        `;
        grid.appendChild(card);
    });

    // Update Details Summary Label and Table Headers
    const summaryTitle = document.querySelector("#tab1 details summary");
    const thead = document.querySelector("#tab1 details table thead");

    if (cadence === "quarterly") {
        if (summaryTitle) summaryTitle.textContent = "Quarterly Financial Filing Breakdown (SEC 10-Q)";
        if (thead) {
            thead.innerHTML = `
                <tr>
                    <th>#</th>
                    <th>Quarter</th>
                    <th>Avg Temp (°C)</th>
                    <th>Precip (mm)</th>
                    <th>Reported Revenue</th>
                    <th>Filing Format</th>
                    <th>Disclosure Type</th>
                    <th>Baseline Normal</th>
                    <th>YoY Variance</th>
                </tr>
            `;
        }
    } else if (state.selectedKey === "nyc_taxi") {
        if (summaryTitle) summaryTitle.textContent = "Hourly Operational Breakdown (NYC TLC Fare Stream)";
        if (thead) {
            thead.innerHTML = `
                <tr>
                    <th>#</th>
                    <th>Hour</th>
                    <th>Temp (°C)</th>
                    <th>Rainfall (mm)</th>
                    <th>Trip Volume</th>
                    <th>Avg Fare</th>
                    <th>Hourly Revenue</th>
                    <th>Completed Trips</th>
                    <th>Telemetry Source</th>
                </tr>
            `;
        }
    } else if (state.selectedKey === "citibike_nyc") {
        if (summaryTitle) summaryTitle.textContent = "Daily Ride Breakdown (Citi Bike NYC Micromobility)";
        if (thead) {
            thead.innerHTML = `
                <tr>
                    <th>#</th>
                    <th>Date</th>
                    <th>Temp (°C)</th>
                    <th>Rainfall (mm)</th>
                    <th>Total Rides</th>
                    <th>Member Rides</th>
                    <th>Avg Duration</th>
                    <th>Ride Volume</th>
                    <th>Estimated Revenue</th>
                </tr>
            `;
        }
    } else if (state.selectedKey === "online_retail") {
        if (summaryTitle) summaryTitle.textContent = "Daily Order Breakdown (UCI Commercial Online Retail)";
        if (thead) {
            thead.innerHTML = `
                <tr>
                    <th>#</th>
                    <th>Date</th>
                    <th>Temp (°C)</th>
                    <th>Rainfall (mm)</th>
                    <th>Order Count</th>
                    <th>Items Sold</th>
                    <th>Avg Order Value</th>
                    <th>Order Volume</th>
                    <th>Daily Revenue</th>
                </tr>
            `;
        }
    } else {
        if (summaryTitle) summaryTitle.textContent = "Hourly Analysis for Selected Day";
        if (thead) {
            thead.innerHTML = `
                <tr>
                    <th>#</th>
                    <th>Time</th>
                    <th>Temperature (°C)</th>
                    <th>Rainfall (mm)</th>
                    <th>Food Orders</th>
                    <th>Price Surge</th>
                    <th>Wait Time</th>
                    <th>Bike Trips</th>
                    <th>Traffic Jam</th>
                </tr>
            `;
        }
    }

    // Render Table Rows
    const tbody = document.getElementById("hourlyTableBody");
    tbody.innerHTML = "";
    dayReview.hourly_table.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${row.num}</td>
            <td>${row.time}</td>
            <td>${row.temp}°C</td>
            <td>${row.rain} mm</td>
            <td>${row.food_orders}</td>
            <td>${row.price_surge}</td>
            <td>${row.wait_time}</td>
            <td>${row.bike_trips}</td>
            <td>${row.traffic_jam}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Render Tab 2 Historical Timeline Chart
function renderHistoricalChart(hist, cadence) {
    const traces = [];

    hist.businesses.forEach(b => {
        // Actual Solid Line
        traces.push({
            x: hist.dates,
            y: b.actual,
            name: `${b.clean_label} — Actual`,
            mode: "lines+markers",
            legendgroup: b.key,
            line: { color: b.color, width: 2.8 },
            marker: { size: 6, color: b.color, symbol: b.symbol || "circle" },
            yaxis: "y1",
            hovertemplate: `<b>${b.name}</b><br>Date: %{x}<br>Actual Sales: $%{y:,.0f}<extra></extra>`
        });

        // Baseline Dashed Line
        if (b.baseline && b.baseline.length) {
            traces.push({
                x: hist.dates,
                y: b.baseline,
                name: `${b.clean_label} — Baseline`,
                mode: "lines",
                legendgroup: b.key,
                line: { color: b.color, width: 1.8, dash: "dash" },
                opacity: 0.65,
                yaxis: "y1",
                hovertemplate: `<b>${b.name} (Baseline)</b><br>Date: %{x}<br>Expected Sales: $%{y:,.0f}<extra></extra>`
            });
        }
    });

    traces.push({
        x: hist.dates,
        y: hist.rainfall,
        name: "Rainfall (mm)",
        mode: "lines",
        line: { color: "#38BDF8", width: 1.8 },
        fill: "tozeroy",
        fillcolor: "rgba(56, 189, 248, 0.12)",
        yaxis: "y2",
        showlegend: false,
        hovertemplate: "Rainfall: %{y:.1f} mm<extra></extra>"
    });

    const layout = {
        template: "plotly_white",
        paper_bgcolor: "#ffffff",
        plot_bgcolor: "#ffffff",
        font: { family: "Inter, -apple-system, sans-serif", size: 11, color: "#172f2b" },
        height: 520,
        margin: { l: 85, r: 25, t: 30, b: 130 },
        grid: { rows: 2, columns: 1, pattern: 'independent', roworder: 'top to bottom' },
        yaxis: {
            title: { text: "Revenue ($)", standoff: 18 },
            automargin: true,
            fixedrange: true,
            domain: [0.38, 1.0],
            gridcolor: "#e7ebe3",
            zeroline: false
        },
        yaxis2: {
            title: { text: "Rain (mm)", standoff: 18 },
            automargin: true,
            fixedrange: true,
            domain: [0.0, 0.26],
            gridcolor: "#e7ebe3",
            zeroline: false
        },
        xaxis: {
            type: "date",
            fixedrange: true,
            gridcolor: "#e7ebe3",
            tickfont: { size: 10.5, color: "#64736c" }
        },
        legend: {
            orientation: "h",
            yanchor: "top",
            y: -0.32,
            xanchor: "center",
            x: 0.5,
            font: { size: 10.5, color: "#172f2b" },
            bgcolor: "#ffffff",
            bordercolor: "#dce2d8",
            borderwidth: 1
        }
    };

    Plotly.newPlot("chartHistorical", traces, layout, { responsive: true, displayModeBar: false, scrollZoom: false, doubleClick: false });
}

// Render Econometrics Table (Tab 2)
function renderEconometricsTable(records) {
    const tbody = document.getElementById("econometricTableBody");
    tbody.innerHTML = "";
    records.forEach(r => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${r.num}</td>
            <td><strong>${r.metric}</strong></td>
            <td>${r.baseline}</td>
            <td>${r.raw_temp_corr}</td>
            <td>${r.adj_temp_impact}</td>
            <td>${r.raw_rain_corr}</td>
            <td>${r.adj_rain_impact}</td>
            <td>${r.r2}</td>
            <td><span class="${r.reliability.includes('Significant') ? 'status-positive' : 'status-neutral'}">${r.reliability}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// Load Tab 3 Domino Data
async function loadDominoData() {
    try {
        const resp = await fetch("/api/domino-data", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                city: state.city,
                selected_keys: [state.selectedKey],
                custom_businesses: state.customBusinesses
            })
        });
        const data = await resp.json();

        // 1. Domino Cascade Steps
        const cascade = data.cascade;
        document.getElementById("dominoChainTitle").textContent =
            `Multi-Hop Domino Chain — ${cascade.city_name} (${cascade.regime})`;

        const stepsContainer = document.getElementById("dominoSteps");
        stepsContainer.innerHTML = cascade.steps.map(s => `
            <div class="domino-step">
                <span class="domino-num">${s.num}</span>
                <span>${s.text}</span>
            </div>
        `).join("");

        // 2. Tipping Point Card
        const tp = cascade.tipping_point;
        document.getElementById("tippingPointCard").innerHTML = `
            <div class="ripple-title" style="color: var(--orange);">${tp.title}</div>
            <div style="font-size: 0.86rem; color: var(--ink); line-height: 1.6; margin-top: 8px;">
                When weather conditions cross operational thresholds in <strong>${cascade.city_name}</strong>, economic channels fracture non-linearly:<br/>
                • <strong>Customer Demand:</strong> ${tp.demand}<br/>
                • <strong>Courier & Service Supply:</strong> ${tp.supply}<br/>
                • <strong>Operational Outcome:</strong> ${tp.consequence}
            </div>
        `;

        // 3. Per-Business Domino Cards
        const bizGrid = document.getElementById("bizDominosGrid");
        bizGrid.innerHTML = data.biz_dominos.map(b => {
            const sign = b.delta >= 0 ? "+$" : "-$";
            const badgeCls = b.delta >= 0 ? "status-positive" : "status-negative";
            return `
                <div class="biz-domino-card">
                    <div class="biz-domino-header">
                        <div>
                            <div class="biz-domino-title">${b.name}</div>
                            <div class="biz-domino-category">${b.category}</div>
                        </div>
                        <span class="biz-domino-badge ${badgeCls}">${sign}${Math.abs(Math.round(b.delta)).toLocaleString()} (${b.pct >= 0 ? '+' : ''}${b.pct.toFixed(1)}%)</span>
                    </div>
                    <div class="biz-chain-step"><strong>1. Weather Trigger:</strong> ${b.trigger}</div>
                    <div class="biz-chain-step"><strong>2. Consumer Reaction:</strong> ${b.behavior}</div>
                    <div class="biz-chain-step"><strong>3. Financial Effect:</strong> ${b.financial}</div>
                    <div class="biz-downstream-box"><strong>Downstream Effects:</strong> ${b.downstream}</div>
                    <div class="biz-countermeasure-box"><strong>Operational Countermeasure:</strong> ${b.action}</div>
                </div>
            `;
        }).join("");

        // 4. Cross-Channel Demand Shifts
        const substContainer = document.getElementById("substitutionLinksContainer");
        if (data.substitution_links && data.substitution_links.length > 0) {
            substContainer.innerHTML = data.substitution_links.map(link => `
                <div class="ripple-box">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="ripple-title">${link.title}</span>
                        <span class="status-neutral">${link.type}</span>
                    </div>
                    <div style="font-size: 0.90rem; font-weight: 700; color: #38BDF8; margin: 6px 0 10px 0;">${link.summary}</div>
                    <div style="margin-top: 8px;">
                        ${(link.chain_steps || []).map(s => `<div class="chain-step">${s}</div>`).join("")}
                    </div>
                </div>
            `).join("");
        } else {
            substContainer.innerHTML = `<div style="color: var(--muted); font-size:0.85rem; padding:8px 0;">Select complementary businesses (e.g., Square POS and Stripe, or Restaurants and Food Delivery) to view substitution flows.</div>`;
        }

        // 5. Past 30 Days Net Shift Chart
        render30DayShiftChart(data.chart_30d);

    } catch (err) {
        console.error("Failed to load domino data:", err);
    }
}

function render30DayShiftChart(c30) {
    const traces = c30.series.map(b => ({
        x: c30.dates,
        y: b.net_shifts,
        name: b.clean_label,
        mode: "lines+markers",
        line: { color: b.color, width: 2.8 },
        marker: { size: 6, color: b.color, symbol: b.symbol },
        hovertemplate: `<b>${b.name}</b><br>Date: %{x}<br>Net Shift: $%{y:+,.0f}<extra></extra>`
    }));

    const layout = {
        template: "plotly_white",
        paper_bgcolor: "#ffffff",
        plot_bgcolor: "#ffffff",
        font: { family: "Inter, -apple-system, sans-serif", size: 11, color: "#172f2b" },
        height: 480,
        margin: { l: 85, r: 25, t: 20, b: 110 },
        yaxis: {
            title: { text: "Sales Shift ($ USD)", standoff: 18 },
            automargin: true,
            fixedrange: true,
            gridcolor: "#e7ebe3",
            zeroline: true,
            zerolinecolor: "#dce2d8"
        },
        xaxis: {
            fixedrange: true,
            gridcolor: "#e7ebe3",
            tickfont: { size: 10, color: "#64736c" }
        },
        legend: {
            orientation: "h",
            yanchor: "top",
            y: -0.26,
            xanchor: "center",
            x: 0.5,
            font: { size: 10.5, color: "#172f2b" },
            bgcolor: "#ffffff",
            bordercolor: "#dce2d8",
            borderwidth: 1
        }
    };

    Plotly.newPlot("chart30d", traces, layout, { responsive: true, displayModeBar: false, scrollZoom: false, doubleClick: false });
}

// Load Tab 4 Nowcast Data
async function loadNowcastData() {
    try {
        const resp = await fetch("/api/nowcast", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                city: state.city,
                selected_keys: [state.selectedKey],
                custom_businesses: state.customBusinesses,
                sim_dow: state.simDow,
                sim_hour: state.simHour,
                sim_rain: state.simRain,
                sim_temp_anom: state.simTempAnom,
                sim_wind: state.simWind
            })
        });

        const data = await resp.json();
        const p = data.sim_params;

        // 1. Banner
        const customBadge = data.is_custom ? `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span class="live-dot" style="background:#38BDF8; box-shadow:0 0 8px #38BDF8;"></span>
                <span style="font-size: 0.78rem; font-weight: 700; color: #38BDF8;">CUSTOM SIMULATION PARAMETERS ACTIVE</span>
            </div>
        ` : "";

        document.getElementById("nowcastBanner").innerHTML = `
            <div>
                <span style="font-weight: 700; color: var(--ink); font-size: 0.92rem;">Nowcasting Conditions:</span>
                <span style="color: var(--teal); font-weight: 600; margin-left: 6px;">${p.day_name} at ${String(p.hour).padStart(2, '0')}:00</span> &bull; 
                <span style="color: var(--ink);">${p.live_condition}</span> 
                (<strong style="color: var(--ink);">${p.rain.toFixed(1)} mm/h rain</strong>, <strong style="color: var(--ink);">${p.temp_anom >= 0 ? '+' : ''}${p.temp_anom.toFixed(1)}°C anomaly</strong>)
            </div>
            ${customBadge}
        `;

        // 2. Sector Prediction Cards
        const sectorGrid = document.getElementById("sectorPredictionsGrid");
        sectorGrid.innerHTML = "";
        Object.entries(data.sector_predictions).forEach(([secName, metrics]) => {
            const card = document.createElement("div");
            card.className = "sector-grid-card";
            card.innerHTML = `
                <div class="sector-title">${secName}</div>
                ${metrics.map(m => `
                    <div class="metric-row">
                        <span style="font-weight:600; color:var(--ink);">${m.display_name}</span>
                        <span>${typeof m.weather_impacted === 'number' ? m.weather_impacted.toLocaleString() : m.weather_impacted} ${m.unit} <span class="${m.delta_pct >= 0 ? 'status-positive' : 'status-negative'}">${m.delta_pct >= 0 ? '+' : ''}${m.delta_pct.toFixed(1)}%</span></span>
                    </div>
                `).join("")}
            `;
            sectorGrid.appendChild(card);
        });

        // 3. 7-Day Forecast Weather Strip
        const strip = document.getElementById("forecastStrip");
        strip.innerHTML = data.daily_forecast_strip.map(day => `
            <div class="forecast-day-card">
                <div style="font-size: 0.84rem; font-weight: 700; color: var(--teal);">${day.day_name}</div>
                <div style="font-size: 0.70rem; color: var(--muted); margin-bottom: 4px;">${day.date.slice(-5)}</div>
                <div style="font-size: 0.88rem; font-weight: 700; color: var(--ink);">${Math.round(day.temp_max)}° / ${Math.round(day.temp_min)}°</div>
                <div style="font-size: 0.74rem; color: var(--muted); margin-top: 4px;">${day.condition}</div>
                <div style="font-size: 0.74rem; color: ${day.precip_mm > 0 ? 'var(--teal)' : 'var(--muted)'}; font-weight: 600; margin-top: 2px;">
                    ${day.precip_mm > 0 ? `${day.precip_mm.toFixed(1)} mm` : '0 mm'}
                </div>
            </div>
        `).join("");

        // 4. Forecast Chart
        renderForecastChart(data.forecast_chart);

        // 5. Strategic Guidance Cards
        const advContainer = document.getElementById("strategicAdviceContainer");
        advContainer.innerHTML = data.strategic_advice.map(adv => `
            <div class="ripple-box" style="margin-bottom: 10px; font-size: 0.86rem; color: var(--ink); line-height: 1.55;">
                ${adv}
            </div>
        `).join("");

    } catch (err) {
        console.error("Failed to load nowcast data:", err);
    }
}

function renderForecastChart(fc) {
    const traces = [];

    fc.series.forEach(b => {
        traces.push({
            x: fc.days,
            y: b.actual_projected,
            name: `${b.clean_label} — Projected`,
            mode: "lines+markers",
            legendgroup: b.key,
            line: { color: b.color, width: 2.8 },
            marker: { size: 7, color: b.color, symbol: b.symbol },
            hovertemplate: `<b>${b.name}</b><br>Day: %{x}<br>Projected: $%{y:,.0f}<extra></extra>`
        });

        traces.push({
            x: fc.days,
            y: b.baseline,
            name: `${b.clean_label} — Normal`,
            mode: "lines",
            legendgroup: b.key,
            line: { color: b.color, width: 1.8, dash: "dash" },
            opacity: 0.65,
            hovertemplate: `<b>${b.name} (Normal)</b><br>Normal: $%{y:,.0f}<extra></extra>`
        });
    });

    const layout = {
        template: "plotly_white",
        paper_bgcolor: "#ffffff",
        plot_bgcolor: "#ffffff",
        font: { family: "Inter, -apple-system, sans-serif", size: 11, color: "#172f2b" },
        height: 500,
        margin: { l: 85, r: 25, t: 20, b: 130 },
        yaxis: {
            title: { text: "Projected Daily Sales ($)", standoff: 18 },
            automargin: true,
            fixedrange: true,
            gridcolor: "#e7ebe3",
            zeroline: false
        },
        xaxis: {
            fixedrange: true,
            gridcolor: "#e7ebe3",
            tickfont: { size: 11, color: "#64736c" }
        },
        legend: {
            orientation: "h",
            yanchor: "top",
            y: -0.26,
            xanchor: "center",
            x: 0.5,
            font: { size: 10.5, color: "#172f2b" },
            bgcolor: "#ffffff",
            bordercolor: "#dce2d8",
            borderwidth: 1
        }
    };

    Plotly.newPlot("chartForecast", traces, layout, { responsive: true, displayModeBar: false, scrollZoom: false, doubleClick: false });
}

// Load Tab 5 Pipeline Diagnostics Data
async function loadDiagnosticsData() {
    try {
        const resp = await fetch(`/api/diagnostics?city=${state.city}`);
        const data = await resp.json();

        const tbody = document.getElementById("pipelineTableBody");
        tbody.innerHTML = "";

        data.table_rows.forEach(r => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${r.num}</td>
                <td>${r.time}</td>
                <td>${r.city}</td>
                <td>${r.temp}°C</td>
                <td>${r.temp_anom}°C</td>
                <td>${r.rain} mm</td>
                <td>${r.delivery_orders}</td>
                <td>${r.price_surge}</td>
                <td>${r.bike_trips}</td>
                <td>${r.rideshare_trips}</td>
                <td>${r.dinein_guests}</td>
                <td>${r.mall_footfall}</td>
                <td>${r.grid_load}</td>
                <td>${r.freight_delay}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed to load diagnostics:", err);
    }
}
