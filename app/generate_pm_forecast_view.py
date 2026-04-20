from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "forecast_montecarlo_summary.json"
DATASET_FILE = DATA_DIR / "forecast_dataset.csv"
OUTPUT_FILE = DATA_DIR / "pm_forecast_view.html"


def main():
    if not INPUT_FILE.exists():
        print("Arquivo forecast_montecarlo_summary.json não encontrado")
        return

    if not DATASET_FILE.exists():
        print("Arquivo forecast_dataset.csv não encontrado")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        summary = json.load(f)

    with open(DATASET_FILE, "r", encoding="utf-8-sig") as f:
        lines = f.read()

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Probabilistic Forecast - PM</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg: #f4f7fb;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #183a66;
      --border: #e5e7eb;
      --shadow: 0 6px 18px rgba(17, 24, 39, 0.08);
      --radius: 16px;
      --blue: #285ea8;
      --green: #15803d;
      --orange: #b45309;
      --note-bg: #fff7ed;
      --note-border: #fed7aa;
      --note-text: #9a3412;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      font-family: 'Segoe UI', Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}

    header {{
      background: linear-gradient(135deg, var(--primary), #0f2744);
      color: white;
      padding: 24px 28px;
      box-shadow: var(--shadow);
    }}

    .header-row {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 20px;
      flex-wrap: wrap;
    }}

    h1 {{
      margin: 0;
      font-size: 1.55rem;
      font-weight: 700;
    }}

    .subtitle {{
      margin-top: 8px;
      opacity: 0.9;
      font-size: 0.96rem;
      line-height: 1.5;
      max-width: 800px;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      text-decoration: none;
      border: 1px solid rgba(255,255,255,0.25);
      color: white;
      padding: 10px 14px;
      border-radius: 10px;
      font-size: 0.88rem;
      font-weight: 600;
      background: rgba(255,255,255,0.08);
      cursor: pointer;
    }}

    .btn:hover {{
      background: rgba(255,255,255,0.16);
    }}

    .container {{
      padding: 24px 28px 40px;
    }}

    .note {{
      background: var(--note-bg);
      border: 1px solid var(--note-border);
      color: var(--note-text);
      padding: 14px 16px;
      border-radius: 12px;
      margin-bottom: 24px;
      line-height: 1.6;
      font-size: 0.92rem;
    }}

    .filters, .simulator, .kpi, .panel, .table-panel {{
      background: var(--card);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      border: 1px solid var(--border);
    }}

    .filters, .simulator {{
      padding: 16px;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
      margin-bottom: 20px;
    }}

    .filters label, .simulator label {{
      font-size: 0.82rem;
      color: #4b5563;
      font-weight: 600;
    }}

    .filters select, .simulator select,
    .filters input, .simulator input,
    .filters button, .simulator button {{
      padding: 9px 12px;
      border: 1px solid #d1d5db;
      border-radius: 10px;
      background: white;
    }}

    .kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .kpi {{
      padding: 18px 20px;
    }}

    .kpi-label {{
      font-size: 0.79rem;
      color: var(--muted);
      margin-bottom: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .kpi-value {{
      font-size: 1.9rem;
      font-weight: 700;
      color: #111827;
    }}

    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }}

    .panel {{
      padding: 18px 20px;
    }}

    .panel h2, .table-panel h2 {{
      margin: 0 0 14px;
      font-size: 1rem;
      color: var(--primary);
    }}

    .panel canvas {{
      width: 100% !important;
      max-height: 340px;
    }}

    .table-panel {{
      padding: 18px 20px;
      overflow-x: auto;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}

    thead {{
      background: #eef2f7;
    }}

    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      text-align: left;
    }}

    .tip {{
      display: inline-block;
      width: 18px;
      height: 18px;
      line-height: 18px;
      text-align: center;
      border-radius: 50%;
      background: #dbeafe;
      color: #1d4ed8;
      font-size: 12px;
      font-weight: 700;
      cursor: help;
      margin-left: 6px;
      vertical-align: middle;
    }}

    .summary-box {{
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #1e3a8a;
      padding: 14px 16px;
      border-radius: 12px;
      line-height: 1.7;
      font-size: 0.95rem;
    }}

    .small-muted {{
      color: var(--muted);
      font-size: 0.85rem;
    }}

    @media (max-width: 960px) {{
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-row">
      <div>
        <h1>🎲 Probabilistic Forecast - PM</h1>
        <div class="subtitle">
          Visão probabilística do backlog usando Monte Carlo, com leitura por cards, story point e effort.
          Esta tela permite filtrar o escopo e simular expansão de demanda para avaliar impacto no prazo.
        </div>
      </div>
      <div>
        <a class="btn" href="pm_view.html">⬅ Voltar para visão do PM</a>
      </div>
    </div>
  </header>

  <div class="container">
    <div class="note">
      Esta abordagem depende do histórico real do board. No início, a previsibilidade tende a ser menor.
      Conforme o time usa consistentemente Story Point, Effort e o fluxo completo, o forecast fica mais robusto.
    </div>

    <section class="filters">
      <label>Cliente
        <span class="tip" title="Filtra o backlog aberto e o histórico concluído por cliente.">?</span>
      </label>
      <select id="filter-client">
        <option value="">Todos</option>
      </select>

      <label>Tipo
        <span class="tip" title="Permite analisar separadamente Feature, Bug, Débito Técnico ou Geral.">?</span>
      </label>
      <select id="filter-type">
        <option value="">Todos</option>
      </select>

      <button id="apply-filters">Aplicar filtros</button>
      <button id="clear-filters">Limpar</button>
    </section>

    <section class="simulator">
      <label>Adicionar X cards
        <span class="tip" title="Simula aumento de escopo no backlog atual.">?</span>
      </label>
      <input type="number" id="extra-cards" min="0" value="0">

      <label>Story Point médio</label>
      <input type="number" id="extra-sp" min="0" step="0.1" value="0">

      <label>Effort médio</label>
      <input type="number" id="extra-effort" min="0" step="0.1" value="0">

      <button id="simulate-btn">Simular cenário</button>
      <button id="reset-sim-btn">Resetar cenário</button>
    </section>

    <section class="kpis">
      <div class="kpi">
        <div class="kpi-label">Cards abertos</div>
        <div class="kpi-value" id="kpi-open-cards">0</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Story Points abertos</div>
        <div class="kpi-value" id="kpi-open-sp">0</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Effort aberto</div>
        <div class="kpi-value" id="kpi-open-effort">0</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Cards concluídos no histórico</div>
        <div class="kpi-value" id="kpi-completed">0</div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>
          Distribuição - Forecast por Cards
          <span class="tip" title="Usa o card como unidade de previsão. É simples, mas ignora tamanho.">?</span>
        </h2>
        <canvas id="chartCards"></canvas>
      </div>

      <div class="panel">
        <h2>
          Distribuição - Forecast por Effort
          <span class="tip" title="Considera esforço estimado acumulado e o ritmo histórico de entrega desse esforço.">?</span>
        </h2>
        <canvas id="chartEffort"></canvas>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>
          Distribuição - Forecast por Story Point
          <span class="tip" title="Considera o tamanho relativo das demandas e o ritmo histórico por Story Point.">?</span>
        </h2>
        <canvas id="chartStory"></canvas>
      </div>

      <div class="panel">
        <h2>
          Sumário executivo
          <span class="tip" title="Interpretação textual do cenário filtrado e/ou simulado.">?</span>
        </h2>
        <div class="summary-box" id="executive-summary"></div>
      </div>
    </section>

    <section class="table-panel">
      <h2>
        Resumo probabilístico
        <span class="tip" title="P50 é cenário provável. P70/P85 são cenários mais conservadores. P95 é alta segurança.">?</span>
      </h2>
      <table>
        <thead>
          <tr>
            <th>Modelo</th>
            <th>P50</th>
            <th>P70</th>
            <th>P85</th>
            <th>P95</th>
            <th>Média</th>
            <th>Mediana</th>
            <th>Amostras</th>
          </tr>
        </thead>
        <tbody id="summary-table-body"></tbody>
      </table>
      <div class="small-muted" style="margin-top:10px;">
        Os valores representam dias simulados necessários para concluir o escopo aberto selecionado.
      </div>
    </section>
  </div>

  <script>
    const INITIAL_SUMMARY = {json.dumps(summary, ensure_ascii=False)};
    const RAW_CSV = {json.dumps(lines)};
    const ITERATIONS = 5000;

    function parseCSV(text) {{
      const rows = text.trim().split('\\n');
      const headers = rows[0].split(',');
      return rows.slice(1).map(line => {{
        const values = [];
        let current = '';
        let inQuotes = false;

        for (let i = 0; i < line.length; i++) {{
          const char = line[i];
          if (char === '"' && line[i + 1] === '"') {{
            current += '"';
            i++;
          }} else if (char === '"') {{
            inQuotes = !inQuotes;
          }} else if (char === ',' && !inQuotes) {{
            values.push(current);
            current = '';
          }} else {{
            current += char;
          }}
        }}
        values.push(current);

        const obj = {{}};
        headers.forEach((h, idx) => obj[h] = values[idx] ?? '');
        return obj;
      }});
    }}

    function toNumber(value) {{
      if (value === undefined || value === null || value === '') return null;
      const n = Number(value);
      return Number.isNaN(n) ? null : n;
    }}

    function percentile(values, p) {{
      if (!values.length) return null;
      const sorted = [...values].sort((a, b) => a - b);
      const k = (sorted.length - 1) * p;
      const f = Math.floor(k);
      const c = Math.min(f + 1, sorted.length - 1);
      if (f === c) return sorted[k];
      return sorted[f] * (c - k) + sorted[c] * (k - f);
    }}

    function buildSummary(simResults) {{
      if (!simResults.length) {{
        return {{
          count: 0, min: null, max: null, avg: null, median: null,
          p50: null, p70: null, p85: null, p95: null
        }};
      }}

      const total = simResults.reduce((a, b) => a + b, 0);
      const sorted = [...simResults].sort((a, b) => a - b);
      const med = sorted.length % 2 === 0
        ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
        : sorted[Math.floor(sorted.length / 2)];

      return {{
        count: simResults.length,
        min: Number(Math.min(...simResults).toFixed(2)),
        max: Number(Math.max(...simResults).toFixed(2)),
        avg: Number((total / simResults.length).toFixed(2)),
        median: Number(med.toFixed(2)),
        p50: Number(percentile(simResults, 0.50).toFixed(2)),
        p70: Number(percentile(simResults, 0.70).toFixed(2)),
        p85: Number(percentile(simResults, 0.85).toFixed(2)),
        p95: Number(percentile(simResults, 0.95).toFixed(2))
      }};
    }}

    function histogram(values) {{
      const buckets = {{}};
      values.forEach(v => {{
        const rounded = Math.round(v);
        buckets[rounded] = (buckets[rounded] || 0) + 1;
      }});
      const labels = Object.keys(buckets).sort((a, b) => Number(a) - Number(b));
      const data = labels.map(l => buckets[l]);
      return {{ labels, data }};
    }}

    function randomChoice(arr) {{
      return arr[Math.floor(Math.random() * arr.length)];
    }}

    function simulateCards(openCardsCount, cycleTimes) {{
      const results = [];
      if (!openCardsCount || !cycleTimes.length) return results;

      for (let i = 0; i < ITERATIONS; i++) {{
        let total = 0;
        for (let c = 0; c < openCardsCount; c++) {{
          total += randomChoice(cycleTimes);
        }}
        results.push(Number(total.toFixed(2)));
      }}
      return results;
    }}

    function simulateByVolume(totalVolume, rates) {{
      const results = [];
      if (!totalVolume || totalVolume <= 0 || !rates.length) return results;

      for (let i = 0; i < ITERATIONS; i++) {{
        let remaining = totalVolume;
        let days = 0;

        while (remaining > 0) {{
          let sampled = randomChoice(rates);
          if (!sampled || sampled <= 0) sampled = 0.1;
          remaining -= sampled;
          days += 1;
        }}

        results.push(Number(days.toFixed(2)));
      }}

      return results;
    }}

    const DATASET = parseCSV(RAW_CSV).map(row => ({{
      ...row,
      story_point: toNumber(row.story_point),
      effort: toNumber(row.effort),
      total_horas_executado: toNumber(row.total_horas_executado),
      lead_time_days: toNumber(row.lead_time_days),
      cycle_time_days: toNumber(row.cycle_time_days),
    }}));

    const filterClient = document.getElementById("filter-client");
    const filterType = document.getElementById("filter-type");

    const clients = [...new Set(DATASET.map(r => r.cliente).filter(Boolean))].sort();
    const tipos = [...new Set(DATASET.map(r => r.tipo).filter(Boolean))].sort();

    clients.forEach(c => {{
      const option = document.createElement("option");
      option.value = c;
      option.textContent = c;
      filterClient.appendChild(option);
    }});

    tipos.forEach(t => {{
      const option = document.createElement("option");
      option.value = t;
      option.textContent = t;
      filterType.appendChild(option);
    }});

    const chartCards = new Chart(document.getElementById("chartCards"), {{
      type: "bar",
      data: {{ labels: [], datasets: [{{ label: "Simulações", data: [], backgroundColor: "#285ea8" }}] }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
    }});

    const chartEffort = new Chart(document.getElementById("chartEffort"), {{
      type: "bar",
      data: {{ labels: [], datasets: [{{ label: "Simulações", data: [], backgroundColor: "#15803d" }}] }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
    }});

    const chartStory = new Chart(document.getElementById("chartStory"), {{
      type: "bar",
      data: {{ labels: [], datasets: [{{ label: "Simulações", data: [], backgroundColor: "#b45309" }}] }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
    }});

    function getFilteredDataset() {{
      const client = filterClient.value;
      const tipo = filterType.value;

      return DATASET.filter(row => {{
        const matchClient = !client || row.cliente === client;
        const matchTipo = !tipo || row.tipo === tipo;
        return matchClient && matchTipo;
      }});
    }}

    function buildForecastFromDataset(rows, extraCards = 0, extraSP = 0, extraEffort = 0) {{
      const done = rows.filter(r => r.completion_type === "internal_done" || r.completion_type === "client_done");
      const open = rows.filter(r => r.completion_type === "open");

      const cycleTimes = done
        .map(r => r.cycle_time_days)
        .filter(v => v !== null && v > 0);

      const storyRates = done
        .map(r => (r.story_point && r.cycle_time_days && r.cycle_time_days > 0) ? (r.story_point / r.cycle_time_days) : null)
        .filter(v => v !== null && v > 0);

      const effortRates = done
        .map(r => (r.effort && r.cycle_time_days && r.cycle_time_days > 0) ? (r.effort / r.cycle_time_days) : null)
        .filter(v => v !== null && v > 0);

      const openCards = open.length + extraCards;
      const totalSP = open.reduce((acc, r) => acc + (r.story_point || 0), 0) + (extraCards * extraSP);
      const totalEffort = open.reduce((acc, r) => acc + (r.effort || 0), 0) + (extraCards * extraEffort);

      const simCards = simulateCards(openCards, cycleTimes);
      const simSP = simulateByVolume(totalSP, storyRates);
      const simEffort = simulateByVolume(totalEffort, effortRates);

      return {{
        backlog_snapshot: {{
          open_cards: openCards,
          total_story_points: Number(totalSP.toFixed(2)),
          total_effort: Number(totalEffort.toFixed(2)),
        }},
        historical_base: {{
          completed_cards: done.length,
          cycle_time_samples: cycleTimes.length,
          story_point_rate_samples: storyRates.length,
          effort_rate_samples: effortRates.length,
        }},
        forecast_by_cards: buildSummary(simCards),
        forecast_by_story_points: buildSummary(simSP),
        forecast_by_effort: buildSummary(simEffort),
        raw_samples: {{
          cards: simCards.slice(0, 300),
          story_points: simSP.slice(0, 300),
          effort: simEffort.slice(0, 300),
        }}
      }};
    }}

    function executiveSummary(data, filteredRows, extraCards, extraSP, extraEffort) {{
      const hist = data.historical_base.completed_cards;
      const p85Cards = data.forecast_by_cards.p85;
      const p85SP = data.forecast_by_story_points.p85;
      const p85Eff = data.forecast_by_effort.p85;

      let text = "";

      if (hist < 10) {{
        text += "Atenção: a base histórica ainda é pequena. Os percentis devem ser lidos como indicativos iniciais, não como compromisso firme.<br><br>";
      }} else if (hist < 30) {{
        text += "A base histórica já permite leitura inicial, mas ainda tende a ter volatilidade. A confiança aumenta conforme mais cards são concluídos.<br><br>";
      }} else {{
        text += "A base histórica já é razoável para um forecast mais útil. Ainda assim, variações de escopo e disciplina de uso do board influenciam a precisão.<br><br>";
      }}

      text += `Escopo atual filtrado: <b>${{data.backlog_snapshot.open_cards}}</b> cards abertos, <b>${{data.backlog_snapshot.total_story_points}}</b> story points e <b>${{data.backlog_snapshot.total_effort}}</b> de effort.<br><br>`;

      if (extraCards > 0) {{
        text += `Cenário simulado: adicionados <b>${{extraCards}}</b> cards com média de <b>${{extraSP}}</b> story points e <b>${{extraEffort}}</b> de effort por card.<br><br>`;
      }}

      if (p85Cards !== null) {{
        text += `Pela leitura por cards, há cerca de <b>85% de chance</b> de concluir o escopo em até <b>${{p85Cards}}</b> dias simulados.<br>`;
      }}

      if (p85SP !== null) {{
        text += `Pela leitura por story points, o cenário conservador aponta <b>${{p85SP}}</b> dias.<br>`;
      }} else {{
        text += `A leitura por story points ainda está insuficiente, possivelmente por falta de histórico concluído com story point preenchido.<br>`;
      }}

      if (p85Eff !== null) {{
        text += `Pela leitura por effort, o cenário conservador aponta <b>${{p85Eff}}</b> dias.<br><br>`;
      }}

      text += "Recomendação prática: use P50 para planejamento provável, P70/P85 para comunicação gerencial e P95 apenas quando precisar de alta segurança.";

      return text;
    }}

    function updateKPIs(data) {{
      document.getElementById("kpi-open-cards").textContent = data.backlog_snapshot.open_cards;
      document.getElementById("kpi-open-sp").textContent = data.backlog_snapshot.total_story_points;
      document.getElementById("kpi-open-effort").textContent = data.backlog_snapshot.total_effort;
      document.getElementById("kpi-completed").textContent = data.historical_base.completed_cards;
    }}

    function updateTable(data) {{
      const rows = [
        ["Por Cards", data.forecast_by_cards],
        ["Por Story Points", data.forecast_by_story_points],
        ["Por Effort", data.forecast_by_effort]
      ];

      const tbody = document.getElementById("summary-table-body");
      tbody.innerHTML = "";

      rows.forEach(([label, obj]) => {{
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${{label}}</td>
          <td>${{obj.p50 ?? ""}}</td>
          <td>${{obj.p70 ?? ""}}</td>
          <td>${{obj.p85 ?? ""}}</td>
          <td>${{obj.p95 ?? ""}}</td>
          <td>${{obj.avg ?? ""}}</td>
          <td>${{obj.median ?? ""}}</td>
          <td>${{obj.count ?? 0}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function updateCharts(data) {{
      const hCards = histogram(data.raw_samples.cards || []);
      const hEffort = histogram(data.raw_samples.effort || []);
      const hStory = histogram(data.raw_samples.story_points || []);

      chartCards.data.labels = hCards.labels;
      chartCards.data.datasets[0].data = hCards.data;
      chartCards.update();

      chartEffort.data.labels = hEffort.labels;
      chartEffort.data.datasets[0].data = hEffort.data;
      chartEffort.update();

      chartStory.data.labels = hStory.labels;
      chartStory.data.datasets[0].data = hStory.data;
      chartStory.update();
    }}

    function renderForecast(extraCards = 0, extraSP = 0, extraEffort = 0) {{
      const filteredRows = getFilteredDataset();
      const data = buildForecastFromDataset(filteredRows, extraCards, extraSP, extraEffort);

      updateKPIs(data);
      updateTable(data);
      updateCharts(data);

      document.getElementById("executive-summary").innerHTML =
        executiveSummary(data, filteredRows, extraCards, extraSP, extraEffort);
    }}

    document.getElementById("apply-filters").addEventListener("click", () => {{
      renderForecast();
    }});

    document.getElementById("clear-filters").addEventListener("click", () => {{
      filterClient.value = "";
      filterType.value = "";
      renderForecast();
    }});

    document.getElementById("simulate-btn").addEventListener("click", () => {{
      const extraCards = Number(document.getElementById("extra-cards").value || 0);
      const extraSP = Number(document.getElementById("extra-sp").value || 0);
      const extraEffort = Number(document.getElementById("extra-effort").value || 0);
      renderForecast(extraCards, extraSP, extraEffort);
    }});

    document.getElementById("reset-sim-btn").addEventListener("click", () => {{
      document.getElementById("extra-cards").value = 0;
      document.getElementById("extra-sp").value = 0;
      document.getElementById("extra-effort").value = 0;
      renderForecast();
    }});

    renderForecast();
  </script>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"View de forecast do PM gerada em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()


