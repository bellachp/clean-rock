(async function () {
    const [chartSpec, data] = await Promise.all([
        fetch("/chart.json").then((r) => r.json()),
        fetch("/data.json").then((r) => r.json()),
    ]);

    vegaEmbed("#chart", chartSpec, { actions: false });

    renderStats(data.summary);
    renderRaw(data.raw, data.bowlers);
})();

function renderStats(rows) {
    const cols = [
        { key: "bowler", label: "Bowler", type: "str" },
        { key: "games", label: "Games", type: "num" },
        { key: "average", label: "Avg", type: "num" },
        { key: "current_ma10", label: "Last 10 MA", type: "num" },
        { key: "high", label: "High", type: "num" },
        { key: "low", label: "Low", type: "num" },
        { key: "stddev", label: "StdDev", type: "num" },
    ];
    buildTable("stats-table", cols, rows);
}

function renderRaw(rows, bowlers) {
    const cols = [{ key: "game_date", label: "Date", type: "date" }];
    for (const b of bowlers) {
        cols.push({ key: `scores.${b}`, label: b, type: "num" });
    }
    const flat = rows.map((r) => {
        const o = { game_date: r.game_date };
        for (const b of bowlers) o[`scores.${b}`] = r.scores[b];
        return o;
    });
    buildTable("raw-table", cols, flat);
}

function buildTable(id, cols, rows) {
    const tbl = document.getElementById(id);
    const thead = tbl.querySelector("thead");
    const tbody = tbl.querySelector("tbody");
    thead.innerHTML = "";
    tbody.innerHTML = "";

    const trh = document.createElement("tr");
    cols.forEach((c, i) => {
        const th = document.createElement("th");
        th.textContent = c.label;
        th.dataset.idx = String(i);
        th.dataset.dir = "asc";
        th.style.cursor = "pointer";
        if (c.type === "num") th.classList.add("num");
        th.addEventListener("click", () => sortBy(tbl, cols, i));
        trh.appendChild(th);
    });
    thead.appendChild(trh);

    for (const r of rows) {
        const tr = document.createElement("tr");
        for (const c of cols) {
            const td = document.createElement("td");
            const v = r[c.key];
            td.textContent = v === null || v === undefined ? "" : v;
            if (c.type === "num") td.classList.add("num");
            tr.appendChild(td);
        }
        tbody.appendChild(tr);
    }
    tbl._cols = cols;
    tbl._rows = rows;
}

function sortBy(tbl, cols, i) {
    const col = cols[i];
    const ths = tbl.querySelectorAll("thead th");
    const dir = ths[i].dataset.dir === "asc" ? "desc" : "asc";
    ths.forEach((th) => (th.dataset.dir = ""));
    ths[i].dataset.dir = dir;
    const sign = dir === "asc" ? 1 : -1;
    const rows = [...tbl._rows].sort((a, b) => {
        const av = a[col.key], bv = b[col.key];
        // Nulls always sort to the bottom, regardless of direction.
        const aNull = av === null || av === undefined || av === "";
        const bNull = bv === null || bv === undefined || bv === "";
        if (aNull && bNull) return 0;
        if (aNull) return 1;
        if (bNull) return -1;
        return cmp(av, bv, col.type) * sign;
    });
    const tbody = tbl.querySelector("tbody");
    tbody.innerHTML = "";
    for (const r of rows) {
        const tr = document.createElement("tr");
        for (const c of cols) {
            const td = document.createElement("td");
            const v = r[c.key];
            td.textContent = v === null || v === undefined ? "" : v;
            if (c.type === "num") td.classList.add("num");
            tr.appendChild(td);
        }
        tbody.appendChild(tr);
    }
}

function cmp(a, b, type) {
    if (type === "num") return Number(a) - Number(b);
    if (type === "date") return String(a).localeCompare(String(b));
    return String(a).localeCompare(String(b));
}
