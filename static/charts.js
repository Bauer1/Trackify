// Fetches aggregated data from /api/summary and renders three Chart.js charts.
const PALETTE = [
  "#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4",
  "#a855f7", "#ec4899", "#84cc16", "#f97316", "#64748b",
];

const money = (v) => "$" + Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function emptyNote(canvas) {
  canvas.parentElement.innerHTML = '<p class="empty">No data yet</p>';
}

async function renderCharts() {
  const res = await fetch(window.SUMMARY_URL);
  const d = await res.json();

  Chart.defaults.font.family = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif";
  Chart.defaults.color = "#475569";

  const tooltipMoney = { callbacks: { label: (ctx) => ` ${money(ctx.parsed.y ?? ctx.parsed)}` } };

  // Doughnut: spending by category
  const catCanvas = document.getElementById("categoryChart");
  if (d.by_category.data.length) {
    new Chart(catCanvas, {
      type: "doughnut",
      data: {
        labels: d.by_category.labels,
        datasets: [{ data: d.by_category.data, backgroundColor: PALETTE, borderWidth: 2 }],
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { position: "right" }, tooltip: tooltipMoney },
      },
    });
  } else emptyNote(catCanvas);

  // Bar: daily spending
  const dayCanvas = document.getElementById("dailyChart");
  if (d.by_day.data.length) {
    new Chart(dayCanvas, {
      type: "bar",
      data: {
        labels: d.by_day.labels,
        datasets: [{ label: "Spent", data: d.by_day.data, backgroundColor: "#6366f1", borderRadius: 4 }],
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: tooltipMoney },
        scales: { y: { beginAtZero: true, ticks: { callback: money } } },
      },
    });
  } else emptyNote(dayCanvas);

  // Line: monthly trend
  const monCanvas = document.getElementById("monthlyChart");
  if (d.by_month.data.length) {
    new Chart(monCanvas, {
      type: "line",
      data: {
        labels: d.by_month.labels,
        datasets: [{
          label: "Monthly total", data: d.by_month.data,
          borderColor: "#22c55e", backgroundColor: "rgba(34,197,94,.15)",
          fill: true, tension: 0.3, pointRadius: 4,
        }],
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: tooltipMoney },
        scales: { y: { beginAtZero: true, ticks: { callback: money } } },
      },
    });
  } else emptyNote(monCanvas);
}

renderCharts();
